"""Independent field-based current, energy and weak-residual checks for G1."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from .fem_g1 import MATERIALS, reference, tetra_geometry


def section_current(points, cells, bodies, current_density, body, axis, coordinate):
    """Direct flux through an interior planar cut, independent of FE reactions.

    Use cuts away from material junction/terminal singularities. Linear-element
    current is constant for constant properties; the cell mean is used for the
    synthetic variable-property diagnostic.
    """
    edges = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    total, total_area = 0., 0.
    other = [d for d in range(3) if d != axis]
    for ci in np.flatnonzero(bodies == body):
        vertices = points[cells[ci]]
        signed = vertices[:, axis]-coordinate
        if signed.min() >= 0 or signed.max() <= 0:
            continue
        polygon = []
        for a, b in edges:
            if signed[a]*signed[b] < 0:
                t = signed[a]/(signed[a]-signed[b])
                polygon.append(vertices[a]+t*(vertices[b]-vertices[a]))
        if len(polygon) < 3:
            continue
        polygon = np.asarray(polygon)
        center = polygon.mean(axis=0)
        rel = polygon[:, other]-center[other]
        order = np.argsort(np.arctan2(rel[:, 1], rel[:, 0]))
        xy = polygon[order][:, other]
        area = abs(np.dot(xy[:, 0], np.roll(xy[:, 1], 1))
                   - np.dot(xy[:, 1], np.roll(xy[:, 0], 1)))/2
        total += area*current_density[ci, axis]
        total_area += area
    return float(total), float(total_area)


def postprocess(mesh_dir: Path, case_dir: Path, export_fields=True) -> dict:
    import meshio
    meta = json.loads((case_dir/"case.json").read_text())
    data = np.load(mesh_dir/"mesh.npz")
    points, cells, bodies = (data[k] for k in ("points", "cells", "bodies"))
    faces, boundaries = data["faces"], data["boundaries"]
    files = sorted(case_dir.glob("fields*.vtu"))
    if not files:
        raise RuntimeError(f"No actual Elmer VTU in {case_dir}")
    field = meshio.read(files[-1])
    distance, mapping = cKDTree(field.points).query(points)
    if distance.max() > 1e-12 or len(np.unique(mapping)) != len(points):
        raise ValueError("VTU/mesh coordinates do not match bijectively")
    pd = {k.lower(): np.asarray(v).reshape(len(field.points), -1)[:, 0][mapping]
          for k, v in field.point_data.items()}
    temperature, potential = pd["temperature"], pd["potential"]
    if not np.isfinite(temperature).all() or not np.isfinite(potential).all():
        raise ValueError("Nonfinite FEM fields")
    volumes, grad = tetra_geometry(points, cells)
    grad_t = np.einsum("ei,eij->ej", temperature[cells], grad)
    grad_p = np.einsum("ei,eij->ej", potential[cells], grad)
    efield = -grad_p
    props = np.array([MATERIALS[int(b)] for b in bodies])
    props[bodies >= 6, 1] = meta["alumina_sigma_s_m"]
    # Four-point symmetric degree-2 tetrahedron quadrature, as in Elmer p:1.
    a, b = .5854101966249685, .1381966011250105
    bary = np.full((4, 4), b)
    np.fill_diagonal(bary, a)
    tq = temperature[cells] @ bary.T
    kq, sigq, sq = [np.repeat(props[:, i:i+1], 4, axis=1) for i in range(3)]
    if meta["temperature_slopes"]:
        for values, slope in ((kq, .0005), (sigq, -.001), (sq, .0002)):
            values[bodies <= 2] *= 1+slope*(tq[bodies <= 2]-300.)
    jq = sigq[:, :, None]*(efield[:, None, :]-sq[:, :, None]*grad_t[:, None, :])
    qq = -kq[:, :, None]*grad_t[:, None, :] + (tq*sq)[:, :, None]*jq
    powerq = np.einsum("eqj,ej->eq", jq, efield)
    jmean, qmean = jq.mean(axis=1), qq.mean(axis=1)
    work = float(np.dot(volumes, powerq.mean(axis=1)))
    joule = float(np.dot(volumes, (np.sum(jq**2, axis=2)/sigq).mean(axis=1)))
    # Reassemble the ORIGINAL nonlinear weak form, without Dirichlet elimination.
    # rT = -int grad(N).q - int N J.E ; rPhi = -int grad(N).J.
    thermal = -volumes[:, None]*(np.einsum("eij,ej->ei", grad, qmean)
                                 + powerq @ bary / 4)
    electrical = -volumes[:, None]*np.einsum("eij,ej->ei", grad, jmean)
    rt, rp = np.zeros(len(points)), np.zeros(len(points))
    np.add.at(rt, cells.ravel(), thermal.ravel())
    np.add.at(rp, cells.ravel(), electrical.ravel())
    area_vec = np.cross(points[faces[:, 1]]-points[faces[:, 0]],
                        points[faces[:, 2]]-points[faces[:, 0]])/2
    areas = np.linalg.norm(area_vec, axis=1)
    normals = area_vec/areas[:, None]
    centers = points[faces].mean(axis=1)
    adjacency = {}
    for ci, c in enumerate(cells):
        for ff in ((c[1], c[2], c[3]), (c[0], c[2], c[3]),
                   (c[0], c[1], c[3]), (c[0], c[1], c[2])):
            adjacency.setdefault(tuple(sorted(ff)), []).append(ci)
    face_cell = np.array([adjacency[tuple(sorted(f))][0] for f in faces])
    outward = np.einsum("ij,ij->i", normals, centers-points[cells[face_cell]].mean(axis=1))
    normals[outward < 0] *= -1
    def integrate_nodal(values, tag):
        m = boundaries == tag
        return float(np.dot(areas[m], values[faces[m]].mean(axis=1)))
    def average(values, tag):
        return integrate_nodal(values, tag)/areas[boundaries == tag].sum()
    def node_set(tag):
        return np.unique(faces[boundaries == tag])
    def outward_flux(values, tag):
        m = boundaries == tag
        return float(np.sum(areas[m]*np.einsum("ij,ij->i", values[face_cell[m]], normals[m])))
    hot_nodes, cold_nodes, ground_nodes = node_set(101), node_set(102), node_set(104)
    hot_reaction = -float(rt[hot_nodes].sum())
    cold_reaction = -float(rt[cold_nodes].sum())
    return_current = -float(rp[ground_nodes].sum())
    voltage = average(potential, 103)-average(potential, 104)
    pin = meta["current_a"]*voltage
    if meta["fixed_cold_k"] is None:
        load = meta["load_w"]
        cold_reaction = -load
        m = boundaries == 102
        np.add.at(rt, faces[m].ravel(), -np.repeat(areas[m]*load/areas[m].sum()/3, 3))
    m = boundaries == 103
    np.add.at(rp, faces[m].ravel(), -np.repeat(areas[m]*meta["current_a"]/areas[m].sum()/3, 3))
    free_t, free_p = np.ones(len(points), bool), np.ones(len(points), bool)
    free_t[hot_nodes] = False
    if meta["fixed_cold_k"] is not None:
        free_t[cold_nodes] = False
    free_p[ground_nodes] = False
    current_scale = max(abs(meta["current_a"]), 1e-6)
    energy_scale = max(abs(pin), abs(cold_reaction), 1e-4)
    energy_error = (hot_reaction+cold_reaction-pin)/energy_scale
    # Bath lies wholly in passive alumina: its direct constitutive flux provides
    # an additional check independent of reaction summation.
    bath_gradient = outward_flux(qmean, 101)
    bath_error = (bath_gradient+cold_reaction-pin)/energy_scale
    leakage = float(np.max(np.linalg.norm(jmean[bodies >= 6], axis=1)))
    result = {
        **meta, "nodes": len(points), "tetrahedra": len(cells),
        "cold_mean_k": average(temperature, 102),
        "cold_min_k": float(temperature[cold_nodes].min()),
        "cold_max_k": float(temperature[cold_nodes].max()),
        "temperature_min_k": float(temperature.min()), "temperature_max_k": float(temperature.max()),
        "delta_t_k": 300.-average(temperature, 102), "voltage_v": voltage,
        "electrical_input_w": pin, "volume_j_dot_e_w": work, "irreversible_joule_w": joule,
        "hot_out_reaction_w": hot_reaction, "cold_out_reaction_w": cold_reaction,
        "hot_out_gradient_w": bath_gradient, "energy_relative_residual": energy_error,
        "bath_gradient_energy_relative_residual": bath_error,
        "power_work_relative_residual": (work-pin)/energy_scale,
        "return_current_a": return_current,
        "current_relative_residual": (return_current-meta["current_a"])/current_scale,
        "terminal_in_gradient_a": -outward_flux(jmean, 103),
        "terminal_out_gradient_a": outward_flux(jmean, 104),
        "free_thermal_residual_l1_w": float(np.abs(rt[free_t]).sum()),
        "free_current_residual_l1_a": float(np.abs(rp[free_p]).sum()),
        "alumina_max_current_density_a_m2": leakage,
        "alumina_leakage_upper_bound_a": leakage*2*8.4e-7,
        "field_source": files[-1].name,
    }
    section_values = {}
    for name, body, axis, coordinate, sign in (
            ("p_leg", 1, 2, .600013e-3, -1),
            ("n_leg", 2, 2, .600013e-3, 1),
            ("bridge", 3, 0, .600017e-3, -1)):
        flux, area = section_current(points, cells, bodies, jmean, body, axis, coordinate)
        section_values[f"{name}_section_current_a"] = sign*flux
        section_values[f"{name}_section_area_m2"] = area
    result.update(section_values)
    section_error = max(abs(result[f"{name}_section_current_a"]-meta["current_a"])
                        for name in ("p_leg", "n_leg", "bridge"))
    result["section_current_absolute_error_a"] = section_error
    result["section_current_relative_residual"] = (section_error/abs(meta["current_a"])
                                                   if meta["current_a"] else None)
    # Actual average junction temperatures, excluding ceramic/contact spreading.
    contact_tags = {}
    for tag in np.unique(boundaries[boundaries >= 201]):
        i = np.flatnonzero(boundaries == tag)[0]
        adj = adjacency[tuple(sorted(faces[i]))]
        pair = tuple(sorted(int(bodies[ci]) for ci in adj))
        contact_tags[pair] = int(tag)
    junction = {name: average(temperature, contact_tags[pair])
                for name, pair in {"p_cold_k": (1, 3), "n_cold_k": (2, 3),
                                   "p_hot_k": (1, 4), "n_hot_k": (2, 5)}.items()}
    result.update(junction)
    seebeck = (MATERIALS[1][2]*(junction["p_hot_k"]-junction["p_cold_k"])
               - MATERIALS[2][2]*(junction["n_hot_k"]-junction["n_cold_k"]))
    result["junction_seebeck_reference_v"] = seebeck
    if not meta["temperature_slopes"]:
        if meta["fixed_cold_k"] is None:
            ideal = reference(meta["current_a"], meta["load_w"])
            result["ideal_reference"] = ideal
            result["cold_reference_relative_error"] = (result["cold_mean_k"]-ideal["cold_k"])/ideal["cold_k"]
            result["delta_t_reference_absolute_error_k"] = result["delta_t_k"]-ideal["delta_t_k"]
            result["voltage_reference_relative_error"] = (voltage-ideal["voltage_v"])/max(abs(ideal["voltage_v"]), 1e-9)
        else:
            result["open_circuit_seebeck_relative_error"] = (voltage-seebeck)/max(abs(seebeck), 1e-9)
    if export_fields:
        meshio.write(case_dir/"derived.vtu", meshio.Mesh(points, [("tetra", cells)],
            point_data={"Temperature_K": temperature, "Potential_V": potential},
            cell_data={"body_id": [bodies], "J_A_m2": [jmean], "q_W_m2": [qmean],
                       "J_dot_E_W_m3": [powerq.mean(axis=1)],
                       "Joule_W_m3": [(np.sum(jq**2, axis=2)/sigq).mean(axis=1)]}))
        export_isosurfaces(case_dir, points, cells, temperature)
        field_plot(case_dir, points, faces, boundaries, temperature, potential)
    (case_dir/"metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    return result


def export_isosurfaces(out, points, cells, temperature):
    """March linear tetrahedra; preserve actual computed isosurface coordinates."""
    import meshio
    vertices, triangles, levels = [], [], []
    edges = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    for level in np.linspace(temperature.min(), temperature.max(), 5)[1:-1]:
        for c in cells:
            tv = temperature[c]-level
            if tv.min() >= 0 or tv.max() <= 0:
                continue
            poly = []
            for a, b in edges:
                if tv[a]*tv[b] < 0:
                    fraction = tv[a]/(tv[a]-tv[b])
                    poly.append(points[c[a]]+fraction*(points[c[b]]-points[c[a]]))
            if len(poly) < 3:
                continue
            poly = np.asarray(poly)
            center = poly.mean(axis=0)
            u = poly[0]-center
            normal = np.cross(poly[1]-poly[0], poly[2]-poly[0])
            if np.linalg.norm(normal) < 1e-25:
                continue
            v = np.cross(normal/np.linalg.norm(normal), u)
            order = np.argsort(np.arctan2((poly-center)@v, (poly-center)@u))
            offset = len(vertices)
            vertices.extend(poly[order])
            levels.extend([level]*len(poly))
            triangles.extend((offset, offset+i, offset+i+1) for i in range(1, len(poly)-1))
    if triangles:
        meshio.write(out/"temperature_isosurfaces.vtu", meshio.Mesh(np.asarray(vertices),
            [("triangle", np.asarray(triangles))], point_data={"Temperature_K": np.asarray(levels)}))


def field_plot(out, points, faces, boundaries, temperature, potential):
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    fig = plt.figure(figsize=(11, 4))
    ax = fig.add_subplot(121, projection="3d")
    external = faces[boundaries < 200]
    collection = ax.plot_trisurf(points[:, 0]*1e3, points[:, 1]*1e3, points[:, 2]*1e3,
                                 triangles=external, cmap="coolwarm", linewidth=0, shade=False)
    collection.set_array(temperature[external].mean(axis=1))
    collection.set_clim(temperature.min(), temperature.max())
    fig.colorbar(collection, ax=ax, shrink=.65, label="Temperature (K)")
    ax.set(xlabel="x (mm)", ylabel="y (mm)", zlabel="z (mm)", title="Coupled 3D FEM temperature")
    ax.set_box_aspect((1.4, .6, 1.6))
    ax.view_init(20, -65)
    ax2 = fig.add_subplot(122)
    cold = faces[boundaries == 102]
    triang = mtri.Triangulation(points[:, 0]*1e3, points[:, 1]*1e3, triangles=cold)
    image = ax2.tripcolor(triang, temperature, shading="gouraud", cmap="coolwarm")
    cold_temperature = temperature[np.unique(cold)]
    image.set_clim(cold_temperature.min(), cold_temperature.max())
    fig.colorbar(image, ax=ax2, label="Temperature (K)")
    ax2.set(xlabel="x (mm)", ylabel="y (mm)", title="Actual loaded cold alumina face", aspect="equal")
    fig.tight_layout()
    fig.savefig(out/"temperature.png", dpi=170)
    plt.close(fig)
