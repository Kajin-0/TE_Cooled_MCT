"""Independent field checks for the real two-terminal 88-leg coupled stack."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from .fem_g1 import tetra_geometry
from .fem_g1_post import export_isosurfaces
from .fem_g2a import PROPERTIES, mesh_adjacency
from .fem_g2a_post import field_plot, plane_sections
from .fem_g2b_physics import cascade_reference


def cut_flux(points, cells, bodies, ids, axis, coordinate, current, gt, temperature, k, seebeck):
    selected = np.flatnonzero(np.isin(bodies, ids))
    subcells = cells[selected]
    current_flux, heat_flux, area = 0., 0., 0.
    for local, da, center in plane_sections(points, subcells, np.ones(len(subcells), bool), axis, coordinate):
        ci = selected[local]
        t = temperature[cells[ci, 0]]+np.dot(gt[ci], center-points[cells[ci, 0]])
        q = -k[ci]*gt[ci]+t*seebeck[ci]*current[ci]
        current_flux += da*current[ci, axis]
        heat_flux += da*q[axis]
        area += da
    return {"current_positive_axis_a": float(current_flux), "heat_positive_axis_w": float(heat_flux),
            "area_m2": float(area)}


def postprocess(mesh_dir, case_dir, export_fields=False):
    import meshio
    meta = json.loads((case_dir/"case.json").read_text())
    m = json.loads((mesh_dir/"manifest.json").read_text())
    mesh = np.load(mesh_dir/"mesh.npz")
    points, cells, bodies, faces, boundaries = (mesh[k] for k in ("points", "cells", "bodies", "faces", "boundaries"))
    source = sorted(case_dir.glob("fields*.vtu"))[-1]
    field = meshio.read(source)
    distances, mapping = cKDTree(field.points).query(points)
    if distances.max() > 1e-12 or len(np.unique(mapping)) != len(points):
        raise ValueError("VTU mesh mismatch")
    pd = {name.lower(): np.asarray(value) for name, value in field.point_data.items()}
    temperature, potential = pd["temperature"].reshape(-1)[mapping], pd["potential"].reshape(-1)[mapping]
    if not np.isfinite([temperature, potential]).all() or temperature.min() <= 0:
        raise ValueError("Nonfinite/unphysical absolute temperature")
    volumes, gradients = tetra_geometry(points, cells)
    gt = np.einsum("ei,eij->ej", temperature[cells], gradients)
    electric = -np.einsum("ei,eij->ej", potential[cells], gradients)
    by_id = {b["id"]: b for b in m["bodies"]}
    props = np.array([PROPERTIES[by_id[int(b)]["material"]] for b in bodies])
    ceramic = np.array([by_id[int(b)]["material"] == "Alumina" for b in bodies])
    props[ceramic, 1] = meta["alumina_sigma_s_m"]
    k, sigma, seebeck = props[:, 0], props[:, 1], props[:, 2]
    current = sigma[:, None]*(electric-seebeck[:, None]*gt)
    tmean = temperature[cells].mean(axis=1)
    heat = -k[:, None]*gt+(tmean*seebeck)[:, None]*current
    work_density = np.sum(current*electric, axis=1)
    joule_density = np.sum(current**2, axis=1)/sigma
    local_t = -volumes[:, None]*(np.einsum("eij,ej->ei", gradients, heat)+work_density[:, None]/4)
    local_p = -volumes[:, None]*np.einsum("eij,ej->ei", gradients, current)
    rt, rp = np.zeros(len(points)), np.zeros(len(points))
    np.add.at(rt, cells.ravel(), local_t.ravel())
    np.add.at(rp, cells.ravel(), local_p.ravel())
    adjacency = mesh_adjacency(cells)
    face_cell = np.array([adjacency[tuple(sorted(f))][0] for f in faces])
    pf = points[faces]
    av = np.cross(pf[:, 1]-pf[:, 0], pf[:, 2]-pf[:, 0])/2
    areas = np.linalg.norm(av, axis=1)
    normal = av/areas[:, None]
    center = pf.mean(axis=1)
    sign = np.einsum("ij,ij->i", normal, center-points[cells[face_cell]].mean(axis=1))
    normal[sign < 0] *= -1
    def nodes(tag):
        return np.unique(faces[boundaries == tag])
    def average(values, tag):
        selected = boundaries == tag
        return float(np.dot(areas[selected], values[faces[selected]].mean(axis=1))/areas[selected].sum())
    def flux(vector, tag):
        selected = boundaries == tag
        return float(np.sum(areas[selected]*np.einsum("ij,ij->i", vector[face_cell[selected]], normal[selected])))
    hot_nodes, ground_nodes, cold_nodes = nodes(101), nodes(104), nodes(102)
    hot_out = -float(rt[hot_nodes].sum())
    return_current = -float(rp[ground_nodes].sum())
    voltage = average(potential, 103)-average(potential, 104)
    pin = meta["current_a"]*voltage
    work = float(np.dot(volumes, work_density))
    bath_flux = flux(heat, 101)
    cold_mean = average(temperature, 102)
    energy_scale = max(abs(pin), abs(meta["load_w"]), 1e-4)
    for tag, values, inward in ((102, rt, meta["load_w"]), (103, rp, meta["current_a"])):
        selected = boundaries == tag
        np.add.at(values, faces[selected].ravel(), -np.repeat(areas[selected]*inward/areas[selected].sum()/3, 3))
    free_t, free_p = np.ones(len(points), bool), np.ones(len(points), bool)
    free_t[hot_nodes], free_p[ground_nodes] = False, False
    result = {**meta, "nodes": len(points), "tetrahedra": len(cells), "dofs": 2*len(points),
              "cold_mean_k": cold_mean, "cold_min_k": float(temperature[cold_nodes].min()),
              "cold_max_k": float(temperature[cold_nodes].max()), "delta_t_k": 300-cold_mean,
              "temperature_min_k": float(temperature.min()), "temperature_max_k": float(temperature.max()),
              "voltage_v": voltage, "electrical_input_w": pin, "volume_j_dot_e_w": work,
              "irreversible_joule_w": float(np.dot(volumes, joule_density)),
              "hot_out_reaction_w": hot_out, "cold_out_w": -meta["load_w"],
              "hot_out_gradient_w": bath_flux, "energy_scale_w": energy_scale,
              "energy_relative_residual": (hot_out-meta["load_w"]-pin)/energy_scale,
              "bath_gradient_energy_relative_residual": (bath_flux-meta["load_w"]-pin)/energy_scale,
              "power_work_relative_residual": (work-pin)/energy_scale,
              "return_current_a": return_current, "current_absolute_error_a": abs(return_current-meta["current_a"]),
              "current_relative_error": abs(return_current-meta["current_a"])/abs(meta["current_a"]) if meta["current_a"] else None,
              "terminal_in_gradient_a": -flux(current, 103), "terminal_out_gradient_a": flux(current, 104),
              "free_thermal_residual_l1_w": float(np.abs(rt[free_t]).sum()),
              "free_current_residual_l1_a": float(np.abs(rp[free_p]).sum()),
              "field_source": source.name,
              "alumina_leakage_upper_bound_a": float(np.linalg.norm(current[ceramic], axis=1).max())*2*(.0064**2)}
    body_joule, body_work, plates, cuts = {}, {}, {}, {}
    for b in m["bodies"]:
        bid = b["id"]
        selected = bodies == bid
        body_joule[b["name"]] = float(np.dot(volumes[selected], joule_density[selected]))
        body_work[b["name"]] = float(np.dot(volumes[selected], work_density[selected]))
        if b["kind"] == "ceramic":
            vn = np.unique(cells[selected])
            plates[b["name"]] = {"mean_k": float(np.dot(volumes[selected], tmean[selected])/volumes[selected].sum()),
                                  "min_k": float(temperature[vn].min()), "max_k": float(temperature[vn].max())}
        if b["kind"] in ("leg", "bridge", "interstage_link"):
            c = cut_flux(points, cells, bodies, [bid], b["cut_axis"], b["cut_coordinate_m"], current, gt, temperature, k, seebeck)
            measured_current = b["current_sign"]*c["current_positive_axis_a"]
            c.update(body_id=bid, kind=b["kind"], current_a=measured_current,
                     current_absolute_error_a=abs(measured_current-meta["current_a"]),
                     current_relative_error=abs(measured_current-meta["current_a"])/abs(meta["current_a"]) if meta["current_a"] else None,
                     expected_area_m2=b["cut_area_m2"], joule_w=body_joule[b["name"]])
            if b["kind"] == "leg":
                expected = meta["current_a"]**2*b["box_m"][5]/(PROPERTIES[b["material"]][1]*b["box_m"][3]**2)
                c["ideal_joule_w"] = expected
                c["joule_relative_error"] = (c["joule_w"]-expected)/expected if expected else None
            cuts[b["name"]] = c
    result.update(plate_temperatures=plates, cuts=cuts, joule_by_body_w=body_joule, electrical_work_by_body_w=body_work)
    for kind in ("leg", "bridge", "interstage_link"):
        selected = [c for c in cuts.values() if c["kind"] == kind]
        result[f"max_{kind}_current_relative_error"] = max(c["current_relative_error"] for c in selected) if meta["current_a"] else None
        result[f"max_{kind}_current_absolute_error_a"] = max(c["current_absolute_error_a"] for c in selected)
    # Stage control volumes are divided through the lower part of shared plates.
    # The nodal indicator is a P1 partition of unity. It yields independently
    # reconstructed conservative weak heat transfers, plus direct geometric cuts.
    all_ids = list(by_id)
    interfaces = []
    for bid in (2, 3):
        box = by_id[bid]["box_m"]
        z = box[2]+.2*box[5]
        weight = (points[:, 2] <= z).astype(float)
        grad_w = np.einsum("ei,eij->ej", weight[cells], gradients)
        upward_weak = -float(np.dot(volumes, np.sum(grad_w*heat, axis=1)))
        below_work = float(np.dot(volumes, weight[cells].mean(axis=1)*work_density))
        direct = cut_flux(points, cells, bodies, all_ids, 2, z, current, gt, temperature, k, seebeck)
        interfaces.append({"z_m": z, "upward_heat_weak_w": upward_weak,
                           "upward_heat_direct_w": direct["heat_positive_axis_w"],
                           "below_electrical_work_w": below_work,
                           "below_energy_residual_w": hot_out+upward_weak-below_work})
    flows = [-hot_out, *(c["upward_heat_weak_w"] for c in interfaces), -meta["load_w"]]
    cumulative_work = [0., *(c["below_electrical_work_w"] for c in interfaces), work]
    stage_budgets = []
    for stage in range(3):
        power = cumulative_work[stage+1]-cumulative_work[stage]
        qhot, qcold = -flows[stage], -flows[stage+1]
        local_stage_work = sum(v for name, v in body_work.items() if name.startswith(f"stage_{stage}_"))
        stage_budgets.append({"stage": stage, "hot_out_w": qhot, "cold_absorbed_w": qcold,
                              "electrical_work_control_volume_w": power, "leg_and_local_metal_work_w": local_stage_work,
                              "balance_residual_w": qhot-qcold-power,
                              "scope": "nodal plane control volume including dielectric/routing portions, no fixed intermediate T"})
    result["stage_control_volume_budgets"] = stage_budgets
    result["intermediate_plane_heat_transfers"] = interfaces
    result["ideal_cascade_reference"] = cascade_reference(m, meta["current_a"], meta["load_w"])
    if export_fields:
        meshio.write(case_dir/"derived.vtu", meshio.Mesh(points, [("tetra", cells)],
            point_data={"Temperature_K": temperature, "Potential_V": potential},
            cell_data={"body_id": [bodies], "E_V_m": [electric], "J_A_m2": [current], "q_W_m2": [heat],
                       "Joule_W_m3": [joule_density], "J_dot_E_W_m3": [work_density]}))
        export_isosurfaces(case_dir, points, cells, temperature)
        field_plot(case_dir, points, cells, bodies, faces, boundaries, temperature, potential)
    (case_dir/"metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    return result
