"""Independent verification from actual multi-couple Elmer temperature/potential."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from .fem_g1 import tetra_geometry
from .fem_g1_post import export_isosurfaces
from .fem_g2a import PROPERTIES, ideal_reference, mesh_adjacency


def plane_sections(points, cells, selected, axis, coordinate):
    """Exact polygon/triangle integration geometry for a planar tetrahedron cut."""
    edges = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    other = [d for d in range(3) if d != axis]
    signed = points[cells, axis]-coordinate
    candidates = np.flatnonzero(selected & (signed.min(axis=1) < 0) & (signed.max(axis=1) > 0))
    for ci in candidates:
        vertices, distances = points[cells[ci]], signed[ci]
        polygon = []
        for a, b in edges:
            if distances[a]*distances[b] < 0:
                t = distances[a]/(distances[a]-distances[b])
                polygon.append(vertices[a]+t*(vertices[b]-vertices[a]))
        if len(polygon) < 3:
            continue
        polygon = np.asarray(polygon)
        rel = polygon[:, other]-polygon[:, other].mean(axis=0)
        order = np.argsort(np.arctan2(rel[:, 1], rel[:, 0]))
        polygon = polygon[order]
        for i in range(1, len(polygon)-1):
            triangle = polygon[[0, i, i+1]]
            area = np.linalg.norm(np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0]))/2
            yield int(ci), float(area), triangle.mean(axis=0)


def postprocess(mesh_dir, case_dir, export_fields=False):
    import meshio
    meta = json.loads((case_dir/"case.json").read_text())
    manifest = json.loads((mesh_dir/"manifest.json").read_text())
    mesh = np.load(mesh_dir/"mesh.npz")
    points, cells, bodies, faces, boundaries = (mesh[k] for k in ("points", "cells", "bodies", "faces", "boundaries"))
    field_path = sorted(case_dir.glob("fields*.vtu"))[-1]
    field = meshio.read(field_path)
    distance, mapping = cKDTree(field.points).query(points)
    if distance.max() > 1e-12 or len(np.unique(mapping)) != len(points):
        raise ValueError("Actual VTU does not match the mesh")
    fields = {name.lower(): np.asarray(values) for name, values in field.point_data.items()}
    temperature = fields["temperature"].reshape(-1)[mapping]
    potential = fields["potential"].reshape(-1)[mapping]
    if not np.isfinite([temperature, potential]).all():
        raise ValueError("Nonfinite coupled fields")
    volumes, gradients = tetra_geometry(points, cells)
    gt = np.einsum("ei,eij->ej", temperature[cells], gradients)
    ep = -np.einsum("ei,eij->ej", potential[cells], gradients)
    material = {b["id"]: b["material"] for b in manifest["bodies"]}
    props = np.asarray([PROPERTIES[material[int(b)]] for b in bodies])
    k, sigma, seebeck = props[:, 0], props[:, 1], props[:, 2]
    current = sigma[:, None]*(ep-seebeck[:, None]*gt)
    tmean = temperature[cells].mean(axis=1)
    heat = -k[:, None]*gt+(tmean*seebeck)[:, None]*current
    work_density = np.sum(current*ep, axis=1)
    joule_density = np.sum(current**2, axis=1)/sigma
    work = float(np.dot(volumes, work_density))
    # With constant properties J and J.E are cellwise constant, q is affine.
    # Mean q and int N=V/4 therefore integrate the nonlinear weak form exactly.
    thermal_local = -volumes[:, None]*(np.einsum("eij,ej->ei", gradients, heat)+work_density[:, None]/4)
    electrical_local = -volumes[:, None]*np.einsum("eij,ej->ei", gradients, current)
    rt, rp = np.zeros(len(points)), np.zeros(len(points))
    np.add.at(rt, cells.ravel(), thermal_local.ravel())
    np.add.at(rp, cells.ravel(), electrical_local.ravel())
    adjacency = mesh_adjacency(cells)
    face_cell = np.array([adjacency[tuple(sorted(f))][0] for f in faces])
    pfaces = points[faces]
    avec = np.cross(pfaces[:, 1]-pfaces[:, 0], pfaces[:, 2]-pfaces[:, 0])/2
    areas = np.linalg.norm(avec, axis=1)
    normals = avec/areas[:, None]
    centroid = pfaces.mean(axis=1)
    sign = np.einsum("ij,ij->i", normals, centroid-points[cells[face_cell]].mean(axis=1))
    normals[sign < 0] *= -1
    def nodes(tag):
        return np.unique(faces[boundaries == tag])
    def average(values, tag):
        m = boundaries == tag
        return float(np.dot(areas[m], values[faces[m]].mean(axis=1))/areas[m].sum())
    def flux(values, tag):
        m = boundaries == tag
        return float(np.sum(areas[m]*np.einsum("ij,ij->i", values[face_cell[m]], normals[m])))
    hot_nodes, cold_nodes, ground_nodes = nodes(101), nodes(102), nodes(104)
    hot_out = -float(rt[hot_nodes].sum())
    cold_out = -float(rt[cold_nodes].sum()) if meta["fixed_cold_k"] is not None else -meta["load_w"]
    return_current = -float(rp[ground_nodes].sum())
    voltage = average(potential, 103)
    pin = meta["current_a"]*voltage
    if meta["fixed_cold_k"] is None:
        m = boundaries == 102
        np.add.at(rt, faces[m].ravel(), -np.repeat(areas[m]*meta["load_w"]/areas[m].sum()/3, 3))
    m = boundaries == 103
    np.add.at(rp, faces[m].ravel(), -np.repeat(areas[m]*meta["current_a"]/areas[m].sum()/3, 3))
    free_t, free_p = np.ones(len(points), bool), np.ones(len(points), bool)
    free_t[hot_nodes], free_p[ground_nodes] = False, False
    if meta["fixed_cold_k"] is not None:
        free_t[cold_nodes] = False
    energy_scale = max(abs(pin), abs(cold_out), 1e-4)
    bath_flux = flux(heat, 101)
    cold_mean = average(temperature, 102)
    result = {**meta, "nodes": len(points), "tetrahedra": len(cells),
              "cold_mean_k": cold_mean, "cold_min_k": float(temperature[cold_nodes].min()),
              "cold_max_k": float(temperature[cold_nodes].max()), "delta_t_k": 300-cold_mean,
              "temperature_min_k": float(temperature.min()), "temperature_max_k": float(temperature.max()),
              "voltage_v": voltage, "electrical_input_w": pin, "volume_j_dot_e_w": work,
              "irreversible_joule_w": float(np.dot(volumes, joule_density)),
              "hot_out_reaction_w": hot_out, "cold_out_reaction_w": cold_out,
              "cold_heat_absorbed_w": -cold_out, "hot_out_gradient_w": bath_flux,
              "energy_relative_residual": (hot_out+cold_out-pin)/energy_scale,
              "bath_gradient_energy_relative_residual": (bath_flux+cold_out-pin)/energy_scale,
              "power_work_relative_residual": (work-pin)/energy_scale,
              "return_current_a": return_current,
              "current_absolute_error_a": abs(return_current-meta["current_a"]),
              "current_relative_error": abs(return_current-meta["current_a"])/abs(meta["current_a"]) if meta["current_a"] else None,
              "terminal_in_gradient_a": -flux(current, 103), "terminal_out_gradient_a": flux(current, 104),
              "free_thermal_residual_l1_w": float(np.abs(rt[free_t]).sum()),
              "free_current_residual_l1_a": float(np.abs(rp[free_p]).sum()),
              "field_source": field_path.name}
    # Exact affine q integration on each polygon triangle, independent of reactions.
    cuts, joule_by_body = {}, {}
    for body in manifest["bodies"]:
        bid = body["id"]
        selected = bodies == bid
        integrated_joule = float(np.dot(volumes[selected], joule_density[selected]))
        joule_by_body[body["name"]] = integrated_joule
        if body["kind"] not in ("leg", "bridge"):
            continue
        axis, coordinate = body["cut_axis"], body["cut_coordinate_m"]
        if body["kind"] == "bridge":
            # Place the cut in the narrow gap, away from both leg footprints.
            coordinate = body["box_m"][axis]+body["box_m"][axis+3]*.500017
        i_cut, q_cut, area = 0., 0., 0.
        for ci, da, center in plane_sections(points, cells, selected, axis, coordinate):
            tc = temperature[cells[ci, 0]]+np.dot(gt[ci], center-points[cells[ci, 0]])
            q = -k[ci]*gt[ci]+tc*seebeck[ci]*current[ci]
            i_cut += da*current[ci, axis]
            q_cut += da*q[axis]
            area += da
        signed_current = body["current_sign"]*i_cut
        entry = {"body_id": bid, "kind": body["kind"], "axis": axis,
                 "coordinate_m": coordinate, "area_m2": area,
                 "expected_area_m2": body["cut_area_m2"], "current_a": signed_current,
                 "current_absolute_error_a": abs(signed_current-meta["current_a"]),
                 "current_relative_error": abs(signed_current-meta["current_a"])/abs(meta["current_a"]) if meta["current_a"] else None,
                 "heat_in_positive_axis_w": q_cut, "joule_w": integrated_joule}
        if body["kind"] == "leg":
            expected_joule = meta["current_a"]**2*manifest["config"]["leg_height_m"]/(PROPERTIES[body["material"]][1]*manifest["config"]["leg_width_m"]**2)
            entry["ideal_joule_w"] = expected_joule
            entry["joule_relative_error"] = (integrated_joule-expected_joule)/expected_joule if expected_joule else None
        cuts[body["name"]] = entry
    result["cuts"], result["joule_by_body_w"] = cuts, joule_by_body
    for kind in ("leg", "bridge"):
        selected = [c for c in cuts.values() if c["kind"] == kind]
        result[f"max_{kind}_current_absolute_error_a"] = max(c["current_absolute_error_a"] for c in selected)
        result[f"max_{kind}_current_relative_error"] = max(c["current_relative_error"] for c in selected) if meta["current_a"] else None
    legs = [c for c in cuts.values() if c["kind"] == "leg"]
    result["max_leg_joule_relative_error"] = max(abs(c["joule_relative_error"]) for c in legs) if meta["current_a"] else None
    ceramic_ids = [b["id"] for b in manifest["bodies"] if b["material"] == "Alumina"]
    leak = float(np.max(np.linalg.norm(current[np.isin(bodies, ceramic_ids)], axis=1)))
    result["alumina_leakage_upper_bound_a"] = leak*2*manifest["cold_area_m2"]
    junctions = {}
    seebeck_voltage = 0.
    leg_info = {b["id"]: b for b in manifest["bodies"] if b["kind"] == "leg"}
    for contact in manifest["contacts"]:
        if not contact["electrical"]:
            continue
        for bid in contact["bodies"]:
            if bid not in leg_info:
                continue
            other = next(b for b in contact["bodies"] if b != bid)
            metal = manifest["bodies"][other-1]
            leg = leg_info[bid]
            side = metal["side"]
            junctions.setdefault(leg["name"], {})[side+"_k"] = average(temperature, contact["boundary_id"])
    for leg in leg_info.values():
        t = junctions[leg["name"]]
        # V(in)-V(out) = integral S dT along current path at open circuit.
        seebeck_voltage += leg["current_sign"]*PROPERTIES[leg["material"]][2]*(t["cold_k"]-t["hot_k"])
    result["junction_temperatures"] = junctions
    result["junction_seebeck_reference_v"] = seebeck_voltage
    if meta["fixed_cold_k"] is None:
        ideal = ideal_reference(manifest, meta["current_a"], meta["load_w"])
        result["ideal_reference"] = ideal
        result["delta_t_reference_absolute_error_k"] = result["delta_t_k"]-ideal["delta_t_k"]
        result["cold_reference_relative_error"] = (cold_mean-ideal["cold_k"])/ideal["cold_k"]
        result["voltage_reference_relative_error"] = (voltage-ideal["voltage_v"])/max(abs(ideal["voltage_v"]), 1e-9)
    elif not meta["current_a"]:
        result["open_circuit_seebeck_relative_error"] = (voltage-seebeck_voltage)/max(abs(seebeck_voltage), 1e-9)
    if export_fields:
        meshio.write(case_dir/"derived.vtu", meshio.Mesh(points, [("tetra", cells)],
            point_data={"Temperature_K": temperature, "Potential_V": potential},
            cell_data={"body_id": [bodies], "E_V_m": [ep], "J_A_m2": [current],
                       "q_W_m2": [heat], "Joule_W_m3": [joule_density],
                       "J_dot_E_W_m3": [work_density]}))
        export_isosurfaces(case_dir, points, cells, temperature)
        field_plot(case_dir, points, cells, bodies, faces, boundaries, temperature, potential)
    (case_dir/"metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    return result


def field_plot(out, points, cells, bodies, faces, boundaries, temperature, potential):
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    fig = plt.figure(figsize=(12, 4.5))
    external = faces[boundaries < 1000]
    for pos, values, name, cmap in ((131, temperature, "Temperature (K)", "coolwarm"),
                                    (132, potential*1e3, "Potential (mV)", "viridis")):
        ax = fig.add_subplot(pos, projection="3d")
        surface = ax.plot_trisurf(points[:, 0]*1e3, points[:, 1]*1e3, points[:, 2]*1e3,
                                 triangles=external, cmap=cmap, linewidth=0, shade=False)
        surface.set_array(values[external].mean(axis=1))
        surface.set_clim(values.min(), values.max())
        fig.colorbar(surface, ax=ax, shrink=.6, label=name)
        ax.set(xlabel="x (mm)", ylabel="y (mm)", zlabel="z (mm)")
        ax.set_box_aspect(np.ptp(points, axis=0))
        ax.view_init(25, -65)
    ax = fig.add_subplot(133)
    cold = faces[boundaries == 102]
    tri = mtri.Triangulation(points[:, 0]*1e3, points[:, 1]*1e3, triangles=cold)
    image = ax.tripcolor(tri, temperature, shading="gouraud", cmap="coolwarm")
    ct = temperature[np.unique(cold)]
    image.set_clim(ct.min(), ct.max())
    fig.colorbar(image, ax=ax, label="Cold face (K)")
    ax.set(xlabel="x (mm)", ylabel="y (mm)", title="Loaded cold ceramic", aspect="equal")
    fig.suptitle("Actual coupled multi-couple FEM fields")
    fig.tight_layout()
    fig.savefig(out/"fields.png", dpi=170)
    plt.close(fig)
