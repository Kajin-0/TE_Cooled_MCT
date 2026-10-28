"""G2b FEASIBILITY ONLY: 88 legs, three separately wired stages, shared ceramics.

No coupled solve and no inferred two-terminal OEM interstage wiring. Six stage
ports deliberately remain explicit. The 28/12/4 split and internal dimensions
are assumptions. G1/G2a solver sources and published evidence remain unchanged.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

from .fem_g1 import tetra_geometry
from .fem_g1_run import execute
from .fem_g2a import Stage, audit_boxes, mesh_adjacency, stage_manifest, validate_path
from .fem_g2a_run import g1_integrity


def assembly_manifest():
    # Envelope matches the nominal reference; internals/netlists are not OEM data.
    counts, columns = (28, 12, 4), (8, 6, 4)
    lengths = (1.07e-3, .82e-3, .64e-3)
    sides = (6.4e-3, 4.55e-3, 3.25e-3, 2.4e-3)
    ceramic, copper = .22e-3, .065e-3
    hot_z = [0.]
    for h in lengths:
        hot_z.append(hot_z[-1]+h+2*copper+ceramic)
    bodies, contacts, nets, terminal_planes = [], [], [], {}
    for i, side in enumerate(sides):
        bottom = -ceramic if i == 0 else hot_z[i]-ceramic
        bodies.append({"id": i+1, "name": f"ceramic_{i}", "kind": "ceramic", "material": "Alumina",
                       "box_m": [-side/2, -side/2, bottom, side, side, ceramic]})
    for stage, (n, cols, length) in enumerate(zip(counts, columns, lengths)):
        cfg = Stage(couples=n, columns=cols, leg_height_m=length, gap_m=.15e-3,
                    copper_m=copper, ceramic_m=ceramic, margin_m=.05e-3)
        local = stage_manifest(cfg)
        span = np.array([max(b["box_m"][a]+b["box_m"][a+3] for b in local["bodies"] if b["kind"] == "leg") for a in (0, 1)])
        offset = np.array([-span[0]/2, -span[1]/2, hot_z[stage]])
        mapping = {local["hot_body"]: stage+1, local["cold_body"]: stage+2}
        for original in local["bodies"]:
            if original["kind"] == "ceramic":
                continue
            body = {**original, "id": len(bodies)+1, "stage": stage,
                    "name": f"stage_{stage}_{original['name']}"}
            box = np.array(original["box_m"])
            box[:3] += offset
            body["box_m"] = box.tolist()
            if "cut_axis" in body:
                body["cut_coordinate_m"] += offset[body["cut_axis"]]
            if body["kind"] == "terminal":
                body["boundary"] = 210+2*stage+(0 if original["boundary"] == 103 else 1)
            bodies.append(body)
            mapping[original["id"]] = body["id"]
        for contact in local["contacts"]:
            contacts.append({"bodies": sorted(mapping[b] for b in contact["bodies"]),
                             "area_m2": contact["area_m2"], "electrical": contact["electrical"],
                             "stage": stage})
        ports = []
        for bc, plane in local["terminal_planes"].items():
            tag = 210+2*stage+(0 if int(bc) == 103 else 1)
            terminal_planes[str(tag)] = {**plane, "body": mapping[plane["body"]],
                                         "coordinate_m": plane["coordinate_m"]+offset[plane["axis"]]}
            ports.append(tag)
        path = [mapping[b] for b in local["conductor_path"]]
        terminals = [mapping[b] for b in local["terminals"]]
        graph = validate_path(path, [c["bodies"] for c in contacts if c["stage"] == stage and c["electrical"]], terminals)
        nets.append({"stage": stage, "couples": n, "leg_height_m": length,
                     "conductor_path": path, "terminals": terminals, "port_boundaries": ports,
                     "graph_audit": graph})
    for i, contact in enumerate(sorted(contacts, key=lambda c: c["bodies"]), 1001):
        contact["boundary_id"] = i
    manifest = {"status": "geometry/netlist/mesh feasibility only; no thermoelectric solve",
                "bodies": bodies, "contacts": contacts, "stage_nets": nets,
                "terminal_planes": terminal_planes, "hot_z_m": -ceramic,
                "cold_z_m": hot_z[-1], "overall_height_m": hot_z[-1]+ceramic,
                "envelope_sides_m": sides, "stage_couples_assumed": counts,
                "legs": 88, "copper_bridges": 85, "stage_ports": 6,
                "module_two_terminal_wiring": "not implemented; OEM interstage wiring undocumented",
                "contacts_assumed": "zero resistance; solder omitted", "units": "SI"}
    audit_boxes(manifest)
    return manifest


def audit_assembly_mesh(manifest, points, cells, bodies, faces, boundaries):
    volumes, _ = tetra_geometry(points, cells)
    if np.any(volumes <= 0):
        raise ValueError("Degenerate tetrahedra")
    measured_volumes = {}
    for b in manifest["bodies"]:
        volume = float(volumes[bodies == b["id"]].sum())
        if not math.isclose(volume, np.prod(b["box_m"][3:]), rel_tol=1e-8):
            raise ValueError(f"Invalid mesh volume {b['name']}")
        measured_volumes[b["name"]] = volume
    adjacency = mesh_adjacency(cells)
    if any(len(adj) > 2 for adj in adjacency.values()):
        raise ValueError("Nonmanifold mesh")
    measured = {}
    for face, adj in adjacency.items():
        if len(adj) == 2 and bodies[adj[0]] != bodies[adj[1]]:
            pair = tuple(sorted(int(bodies[ci]) for ci in adj))
            p = points[list(face)]
            measured[pair] = measured.get(pair, 0.)+np.linalg.norm(np.cross(p[1]-p[0], p[2]-p[0]))/2
    expected = {tuple(c["bodies"]): c for c in manifest["contacts"]}
    if set(measured) != set(expected):
        raise ValueError("Actual assembly contact graph differs from intended graph")
    for pair, area in measured.items():
        if not math.isclose(area, expected[pair]["area_m2"], rel_tol=1e-8):
            raise ValueError(f"Contact gap/wrong area {pair}")
    for face, tag in zip(faces, boundaries):
        if len(adjacency.get(tuple(sorted(face)), [])) != (2 if tag >= 1001 else 1):
            raise ValueError("Nonconformal physical face")
    conductor_ids = {b["id"] for b in manifest["bodies"] if b["kind"] != "ceramic"}
    electrical_edges = [p for p in measured if p[0] in conductor_ids and p[1] in conductor_ids]
    node_bodies = [set() for _ in points]
    for bid in conductor_ids:
        for node in np.unique(cells[bodies == bid]):
            node_bodies[node].add(bid)
    for joined in node_bodies:
        joined = sorted(joined)
        for i, a in enumerate(joined):
            if any((a, b) not in expected for b in joined[i+1:]):
                raise ValueError("Illegal conductor connection at a point/edge")
    graphs, assigned_edges = [], set()
    for net in manifest["stage_nets"]:
        vertices = set(net["conductor_path"])
        edges = [e for e in electrical_edges if e[0] in vertices and e[1] in vertices]
        graphs.append(validate_path(vertices, edges, net["terminals"]))
        assigned_edges.update(edges)
    if assigned_edges != set(electrical_edges):
        raise ValueError("Unintended interstage electrical contact")
    return {"passed": True, "scope": "geometry/netlist/mesh only", "coupled_solution": False,
            "nodes": len(points), "tetrahedra": len(cells), "domains": len(manifest["bodies"]),
            "legs": sum(b["kind"] == "leg" for b in manifest["bodies"]),
            "copper_bridges": sum(b["kind"] == "bridge" for b in manifest["bodies"]),
            "ceramic_plates": sum(b["kind"] == "ceramic" for b in manifest["bodies"]),
            "stage_ports": len(manifest["terminal_planes"]), "separate_stage_paths": graphs,
            "electrical_components": 3, "thermal_contact_count": len(measured),
            "unintended_conductor_connections": 0, "volumes_m3": measured_volumes,
            "contact_areas_m2": {f"{a}:{b}": float(v) for (a, b), v in measured.items()}}


def generate(out, size_m=.2e-3):
    import gmsh
    import meshio
    manifest = assembly_manifest()
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    gmsh.initialize()
    gmsh.logger.start()
    try:
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("Mesh.RandomSeed", 20261028)
        gmsh.model.add("G2b_geometry_only")
        original = [(3, gmsh.model.occ.addBox(*b["box_m"])) for b in manifest["bodies"]]
        _, mapping = gmsh.model.occ.fragment(original[:1], original[1:])
        gmsh.model.occ.synchronize()
        volumes_to_body = {}
        for body, fragments in zip(manifest["bodies"], mapping):
            tags = [v for dim, v in fragments if dim == 3]
            gmsh.model.addPhysicalGroup(3, tags, body["id"], body["name"])
            volumes_to_body.update({v: body["id"] for v in tags})
        expected = {tuple(c["bodies"]): c for c in manifest["contacts"]}
        names = {101: "bottom_bath_face_geometry_only", 102: "top_face_geometry_only", 105: "other_exposed_faces"}
        for stage in range(3):
            names[210+2*stage] = f"stage_{stage}_port_in_unconnected"
            names[211+2*stage] = f"stage_{stage}_port_out_unconnected"
        groups = {tag: [] for tag in names}
        groups.update({c["boundary_id"]: [] for c in manifest["contacts"]})
        for _, surface in gmsh.model.getEntities(2):
            up, _ = gmsh.model.getAdjacencies(2, surface)
            pair = tuple(sorted({volumes_to_body[int(v)] for v in up}))
            center = gmsh.model.occ.getCenterOfMass(2, surface)
            if len(pair) == 2:
                tag = expected[pair]["boundary_id"]
            elif len(pair) == 1:
                tag = 105
                if abs(center[2]-manifest["hot_z_m"]) < 1e-11:
                    tag = 101
                elif abs(center[2]-manifest["cold_z_m"]) < 1e-11:
                    tag = 102
                else:
                    for port, plane in manifest["terminal_planes"].items():
                        if pair[0] == plane["body"] and abs(center[plane["axis"]]-plane["coordinate_m"]) < 1e-11:
                            tag = int(port)
            else:
                raise ValueError("Invalid geometric surface adjacency")
            groups[tag].append(surface)
        for tag, surfaces in groups.items():
            if not surfaces:
                raise ValueError(f"Missing geometry face tag {tag}")
            gmsh.model.addPhysicalGroup(2, surfaces, tag, names.get(tag, f"contact_{tag}"))
        gmsh.option.setNumber("Mesh.MeshSizeMin", size_m)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size_m)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.model.mesh.generate(3)
        gmsh.write(str(out/"assembly.msh"))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        points = np.asarray(xyz).reshape(-1, 3)
        lookup = {int(tag): i for i, tag in enumerate(tags)}
        def conn(nodes, width):
            return np.fromiter((lookup[int(n)] for n in nodes), dtype=int).reshape(-1, width)
        cells, bodies, faces, boundaries = [], [], [], []
        for volume, bid in volumes_to_body.items():
            types, _, arrays = gmsh.model.mesh.getElements(3, volume)
            for typ, nodes in zip(types, arrays):
                if typ != 4:
                    raise ValueError("Expected linear tetrahedra")
                c = conn(nodes, 4)
                cells.append(c)
                bodies.extend([bid]*len(c))
        for tag, surfaces in groups.items():
            for surface in surfaces:
                types, _, arrays = gmsh.model.mesh.getElements(2, surface)
                for typ, nodes in zip(types, arrays):
                    if typ != 2:
                        raise ValueError("Expected triangles")
                    f = conn(nodes, 3)
                    faces.append(f)
                    boundaries.extend([tag]*len(f))
        cells, faces = np.concatenate(cells), np.concatenate(faces)
        bodies, boundaries = np.array(bodies), np.array(boundaries)
        np.savez_compressed(out/"mesh.npz", points=points, cells=cells, bodies=bodies,
                            faces=faces, boundaries=boundaries)
        result = audit_assembly_mesh(manifest, points, cells, bodies, faces, boundaries)
        result.update(mesh_size_m=size_m, gmsh_version=gmsh.__version__, elapsed_s=time.monotonic()-started)
        meshio.write(out/"geometry_only.vtu", meshio.Mesh(points, [("tetra", cells)], cell_data={"body_id": [bodies]}))
        manifest["physical_boundary_names"] = {str(k): names.get(k, f"contact_{k}") for k in groups}
        (out/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
        (out/"audit.json").write_text(json.dumps(result, indent=2)+"\n")
        draw_geometry(out, manifest)
        return result
    finally:
        (out/"gmsh.log").write_text("\n".join(gmsh.logger.get())+"\n")
        gmsh.logger.stop()
        gmsh.finalize()


def draw_geometry(out, manifest):
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    for body in manifest["bodies"]:
        x, y, z, dx, dy, dz = np.array(body["box_m"])*1e3
        p = np.array([[x, y, z], [x+dx, y, z], [x+dx, y+dy, z], [x, y+dy, z],
                      [x, y, z+dz], [x+dx, y, z+dz], [x+dx, y+dy, z+dz], [x, y+dy, z+dz]])
        indices = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        ceramic = body["kind"] == "ceramic"
        color = {"P": "#b33b42", "N": "#3469b0", "Cu": "#bf853c", "Alumina": "#eeeeee"}[body["material"]]
        poly = Poly3DCollection([p[i] for i in indices], facecolor=color, edgecolor="gray" if ceramic else "none",
                               linewidth=.4, alpha=.1 if ceramic else .95)
        ax.add_collection3d(poly)
    ax.set(xlim=(-3.3, 3.3), ylim=(-3.3, 3.3), zlim=(-.3, 3.7),
           xlabel="x (mm)", ylabel="y (mm)", zlabel="z (mm)")
    ax.set_box_aspect((6.4, 6.4, 3.8))
    ax.view_init(24, -62)
    ax.set_title("G2b GEOMETRY ONLY: 88 legs, assumed 28/12/4 stages\n"
                 "P red / N blue / Cu brown; six independent stage ports; no coupled solution")
    fig.tight_layout()
    fig.savefig(out/"geometry_only.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/fem-g2b-geometry"))
    parser.add_argument("--size-mm", type=float, default=.2)
    args = parser.parse_args()
    if not math.isfinite(args.size_mm) or args.size_mm <= 0:
        raise SystemExit("Positive finite mesh size required")
    root = Path(__file__).resolve().parents[1]
    g2a = json.loads((root/"fem/results/g2a_20261028/summary.json").read_text())
    if not g2a["verification"]["passed"] or not g1_integrity()["passed"]:
        raise SystemExit("Verified G1/G2a prerequisites missing")
    for filename, digest in g2a["source_sha256"].items():
        if hashlib.sha256((root/filename).read_bytes()).hexdigest() != digest:
            raise SystemExit(f"G2a source changed: {filename}")
    out = args.out.resolve()
    audit = generate(out, args.size_mm*1e-3)
    execute(["ElmerGrid", "14", "2", "assembly.msh", "-out", "elmer"], out, "grid")
    print(json.dumps({k: v for k, v in audit.items() if k not in ("volumes_m3", "contact_areas_m2")}, indent=2))


if __name__ == "__main__":
    main()
