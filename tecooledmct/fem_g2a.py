"""Parametric, connected multi-couple solid geometry and genuine Elmer input.

G1 is imported read-only for its pinned material constants and tetra utilities.
All dimensions are SI. Geometry is a verification specimen, not an OEM netlist.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path

import numpy as np

from .fem_g1 import ELMER_COMMIT, MATERIALS, tetra_geometry

PROPERTIES = {"P": MATERIALS[1], "N": MATERIALS[2], "Cu": MATERIALS[3],
              "Alumina": MATERIALS[6]}
BC_NAMES = {101: "hot_bath", 102: "cold_face", 103: "current_in",
            104: "ground", 105: "insulated_sides"}


@dataclass(frozen=True)
class Stage:
    couples: int = 4
    columns: int = 4
    leg_width_m: float = .4e-3
    leg_height_m: float = 1e-3
    gap_m: float = .4e-3
    copper_m: float = .1e-3
    ceramic_m: float = .2e-3
    margin_m: float = .1e-3

    def validate(self):
        if not isinstance(self.couples, int) or self.couples < 1:
            raise ValueError("Positive integer couple count required")
        if not isinstance(self.columns, int) or self.columns < 2 or 2*self.couples % self.columns:
            raise ValueError("Columns must divide the even leg count and be at least two")
        sizes = [v for k, v in asdict(self).items() if k not in ("couples", "columns")]
        if not all(math.isfinite(v) and v > 0 for v in sizes):
            raise ValueError("Positive finite geometry dimensions required")


def validate_path(nodes, edges, terminals):
    """A connected simple path has exactly two degree-one vertices and |E|=|V|-1."""
    nodes, edges = set(nodes), [tuple(sorted(p)) for p in edges]
    if len(set(edges)) != len(edges) or any(a == b for a, b in edges):
        raise ValueError("Duplicate/self conductor edge")
    adjacency = {n: set() for n in nodes}
    for a, b in edges:
        if a not in nodes or b not in nodes:
            raise ValueError("Unknown conductor in netlist")
        adjacency[a].add(b)
        adjacency[b].add(a)
    if len(edges) != len(nodes)-1 or len(terminals) != 2:
        raise ValueError("Conductor netlist is not one open path")
    for n, adjacent in adjacency.items():
        if len(adjacent) != (1 if n in terminals else 2):
            raise ValueError(f"Illegal conductor degree at {n}: {len(adjacent)}")
    seen, stack = set(), [terminals[0]]
    while stack:
        n = stack.pop()
        if n not in seen:
            seen.add(n)
            stack.extend(adjacency[n]-seen)
    if seen != nodes:
        raise ValueError("Disconnected conductor netlist")
    return {"nodes": len(nodes), "edges": len(edges), "unique_path": True,
            "degrees": {str(n): len(a) for n, a in adjacency.items()}}


def stage_manifest(config=Stage()):
    config.validate()
    w, h, pitch = config.leg_width_m, config.leg_height_m, config.leg_width_m+config.gap_m
    cu, cer, margin = config.copper_m, config.ceramic_m, config.margin_m
    rows = 2*config.couples//config.columns
    coordinates = [(c*pitch, r*pitch) for r in range(rows)
                   for c in (range(config.columns) if r % 2 == 0 else reversed(range(config.columns)))]
    bodies = []
    def add(name, kind, box, material, **kw):
        b = {"id": len(bodies)+1, "name": name, "kind": kind,
             "box_m": list(box), "material": material, **kw}
        bodies.append(b)
        return b["id"]
    legs = []
    for i, (x, y) in enumerate(coordinates):
        legs.append(add(f"leg_{i:02d}_{'N' if i % 2 == 0 else 'P'}", "leg",
                        (x, y, cu, w, w, h), "N" if i % 2 == 0 else "P",
                        order=i, cut_axis=2, cut_coordinate_m=cu+h*.500013,
                        current_sign=1 if i % 2 == 0 else -1, cut_area_m2=w*w))
    bridges = []
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(coordinates, coordinates[1:])):
        cold = i % 2 == 0
        axis = 0 if abs(x1-x0) > 1e-15 else 1
        box = (min(x0, x1), min(y0, y1), cu+h if cold else 0.,
               abs(x1-x0)+w, abs(y1-y0)+w, cu)
        bridges.append(add(f"bridge_{i:02d}_{'cold' if cold else 'hot'}", "bridge", box, "Cu",
                           order=i, side="cold" if cold else "hot", cut_axis=axis,
                           cut_coordinate_m=box[axis]+box[axis+3]*.500017,
                           current_sign=1 if (x1-x0 if axis == 0 else y1-y0) > 0 else -1,
                           cut_area_m2=w*cu))
    terminals = [add(name, "terminal", (*coordinates[i], 0., w, w, cu), "Cu",
                     side="hot", boundary=bc)
                 for name, i, bc in (("terminal_in", 0, 103), ("terminal_out", -1, 104))]
    sx, sy = (config.columns-1)*pitch+w+2*margin, (rows-1)*pitch+w+2*margin
    hot = add("hot_alumina", "ceramic", (-margin, -margin, -cer, sx, sy, cer), "Alumina")
    cold = add("cold_alumina", "ceramic", (-margin, -margin, h+2*cu, sx, sy, cer), "Alumina")
    path = [terminals[0]]
    for i, leg in enumerate(legs):
        path.append(leg)
        if i < len(bridges):
            path.append(bridges[i])
    path.append(terminals[1])
    contacts = [{"bodies": sorted((a, b)), "area_m2": w*w, "electrical": True}
                for a, b in zip(path, path[1:])]
    for body in bodies:
        if body["kind"] in ("bridge", "terminal"):
            contacts.append({"bodies": sorted((body["id"], hot if body["side"] == "hot" else cold)),
                             "area_m2": body["box_m"][3]*body["box_m"][4], "electrical": False})
    for i, contact in enumerate(sorted(contacts, key=lambda c: c["bodies"]), 1001):
        contact["boundary_id"] = i
    terminal_planes = {}
    for tid in terminals:
        body = bodies[tid-1]
        x = body["box_m"][0]
        # Both snake endpoints lie on an outer x edge.
        terminal_planes[str(body["boundary"])] = {"body": tid, "axis": 0,
            "coordinate_m": x if abs(x) < 1e-14 else x+w, "area_m2": w*cu}
    manifest = {"config": asdict(config), "bodies": bodies, "contacts": contacts,
                "conductor_path": path, "terminals": terminals, "terminal_planes": terminal_planes,
                "hot_body": hot, "cold_body": cold, "cold_area_m2": sx*sy,
                "hot_z_m": -cer, "cold_z_m": h+2*cu+cer,
                "material_properties_si": {k: list(v) for k, v in PROPERTIES.items()},
                "units": "SI", "contacts_assumed": "zero electrical and thermal resistance",
                "status": "verification geometry, not a measured OEM netlist"}
    manifest["graph_audit"] = validate_path(path, [c["bodies"] for c in contacts if c["electrical"]], terminals)
    audit_boxes(manifest)
    return manifest


def audit_boxes(manifest):
    """Independent AABB check catches volume overlaps and illegal edge/point shorts."""
    expected = {tuple(c["bodies"]): c["area_m2"] for c in manifest["contacts"]}
    measured = {}
    bodies = manifest["bodies"]
    tol = 1e-13
    for i, a in enumerate(bodies):
        aa = np.array(a["box_m"])
        for b in bodies[i+1:]:
            bb = np.array(b["box_m"])
            overlap = np.minimum(aa[:3]+aa[3:], bb[:3]+bb[3:])-np.maximum(aa[:3], bb[:3])
            if np.all(overlap > tol):
                raise ValueError(f"Overlapping bodies {a['name']} / {b['name']}")
            if np.all(overlap >= -tol):
                pair = (a["id"], b["id"])
                positive = overlap[overlap > tol]
                if len(positive) == 2:
                    measured[pair] = float(np.prod(positive))
                elif a["material"] != "Alumina" and b["material"] != "Alumina" and pair not in expected:
                    raise ValueError(f"Unintended edge/point conductor short {pair}")
    if set(measured) != set(expected):
        raise ValueError("Box contact graph differs from intended netlist")
    for pair, area in measured.items():
        if not math.isclose(area, expected[pair], rel_tol=1e-8):
            raise ValueError(f"Wrong geometric contact area {pair}")


def mesh_adjacency(cells):
    adjacency = {}
    for ci, c in enumerate(cells):
        for f in ((c[1], c[2], c[3]), (c[0], c[2], c[3]),
                  (c[0], c[1], c[3]), (c[0], c[1], c[2])):
            adjacency.setdefault(tuple(sorted(f)), []).append(ci)
    return adjacency


def audit_mesh(manifest, points, cells, body_ids, faces, boundaries):
    volumes, _ = tetra_geometry(points, cells)
    if not np.all(volumes > 0):
        raise ValueError("Degenerate tetrahedron")
    measured_volumes = {}
    for b in manifest["bodies"]:
        v = float(volumes[body_ids == b["id"]].sum())
        if not math.isclose(v, np.prod(b["box_m"][3:]), rel_tol=1e-8):
            raise ValueError(f"Gap/overlap in {b['name']} volume")
        measured_volumes[b["name"]] = v
    adjacency = mesh_adjacency(cells)
    if any(len(adj) > 2 for adj in adjacency.values()):
        raise ValueError("Nonmanifold mesh")
    contact_area = {}
    for f, adj in adjacency.items():
        if len(adj) == 2 and body_ids[adj[0]] != body_ids[adj[1]]:
            pair = tuple(sorted(int(body_ids[ci]) for ci in adj))
            p = points[list(f)]
            contact_area[pair] = contact_area.get(pair, 0.)+np.linalg.norm(np.cross(p[1]-p[0], p[2]-p[0]))/2
    expected = {tuple(c["bodies"]): c for c in manifest["contacts"]}
    if set(contact_area) != set(expected):
        raise ValueError("Actual mesh contact graph differs from netlist")
    for pair, area in contact_area.items():
        if not math.isclose(area, expected[pair]["area_m2"], rel_tol=1e-8):
            raise ValueError(f"Mesh interface gap {pair}")
    conductor = {b["id"] for b in manifest["bodies"] if b["material"] != "Alumina"}
    # Also catch a short connected at only an edge or a point (no shared face).
    node_bodies = [set() for _ in points]
    for b in conductor:
        for node in np.unique(cells[body_ids == b]):
            node_bodies[node].add(b)
    for touching in node_bodies:
        touching = sorted(touching)
        for i, a in enumerate(touching):
            if any((a, b) not in expected for b in touching[i+1:]):
                raise ValueError("Unintended conductor edge/point mesh connection")
    for f, bc in zip(faces, boundaries):
        if len(adjacency.get(tuple(sorted(f)), [])) != (2 if bc >= 1001 else 1):
            raise ValueError("Nonconformal tagged face")
    electrical_edges = [p for p in contact_area if p[0] in conductor and p[1] in conductor]
    graph = validate_path(conductor, electrical_edges, manifest["terminals"])
    return {"passed": True, "nodes": len(points), "tetrahedra": len(cells),
            "volumes_m3": measured_volumes, "mesh_graph": graph,
            "contact_areas_m2": {f"{a}:{b}": float(area) for (a, b), area in contact_area.items()},
            "unintended_point_edge_connections": 0}


def generate_mesh(out: Path, size_m: float, config=Stage(), manifest=None):
    import gmsh
    if not math.isfinite(size_m) or size_m <= 0:
        raise ValueError("Positive mesh size required")
    manifest = stage_manifest(config) if manifest is None else manifest
    out.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    gmsh.logger.start()
    try:
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("Mesh.RandomSeed", 20261028)
        gmsh.model.add("multi_couple_series_stage")
        originals = [(3, gmsh.model.occ.addBox(*b["box_m"])) for b in manifest["bodies"]]
        _, mapping = gmsh.model.occ.fragment(originals[:1], originals[1:])
        gmsh.model.occ.synchronize()
        volume_body = {}
        for body, fragments in zip(manifest["bodies"], mapping):
            tags = [tag for dim, tag in fragments if dim == 3]
            gmsh.model.addPhysicalGroup(3, tags, body["id"], body["name"])
            volume_body.update({v: body["id"] for v in tags})
        contact_by_pair = {tuple(c["bodies"]): c for c in manifest["contacts"]}
        surfaces = {b: [] for b in BC_NAMES}
        surfaces.update({c["boundary_id"]: [] for c in manifest["contacts"]})
        for _, surface in gmsh.model.getEntities(2):
            up, _ = gmsh.model.getAdjacencies(2, surface)
            pair = tuple(sorted({volume_body[int(v)] for v in up}))
            center = gmsh.model.occ.getCenterOfMass(2, surface)
            if len(pair) == 2:
                surfaces[contact_by_pair[pair]["boundary_id"]].append(surface)
            elif len(pair) == 1:
                tag = 105
                if abs(center[2]-manifest["hot_z_m"]) < 1e-11:
                    tag = 101
                elif abs(center[2]-manifest["cold_z_m"]) < 1e-11:
                    tag = 102
                else:
                    for bc, plane in manifest["terminal_planes"].items():
                        if pair[0] == plane["body"] and abs(center[plane["axis"]]-plane["coordinate_m"]) < 1e-11:
                            tag = int(bc)
                surfaces[tag].append(surface)
            else:
                raise ValueError("Invalid geometric interface")
        for tag, ss in surfaces.items():
            if not ss:
                raise ValueError(f"Missing physical boundary {tag}")
            gmsh.model.addPhysicalGroup(2, ss, tag, BC_NAMES.get(tag, f"contact_{tag}"))
        gmsh.option.setNumber("Mesh.MeshSizeMin", size_m)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size_m)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.model.mesh.generate(3)
        gmsh.write(str(out/"stage.msh"))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        points = np.asarray(xyz).reshape(-1, 3)
        lookup = {int(t): i for i, t in enumerate(tags)}
        def connectivity(nodes, width):
            return np.fromiter((lookup[int(n)] for n in nodes), dtype=int).reshape(-1, width)
        cells, bodies, faces, boundaries = [], [], [], []
        for volume, body in volume_body.items():
            types, _, arrays = gmsh.model.mesh.getElements(3, volume)
            for typ, nodes in zip(types, arrays):
                if typ != 4:
                    raise ValueError("Linear tetrahedra required")
                conn = connectivity(nodes, 4)
                cells.append(conn)
                bodies.extend([body]*len(conn))
        for tag, ss in surfaces.items():
            for surface in ss:
                types, _, arrays = gmsh.model.mesh.getElements(2, surface)
                for typ, nodes in zip(types, arrays):
                    if typ != 2:
                        raise ValueError("Triangular faces required")
                    conn = connectivity(nodes, 3)
                    faces.append(conn)
                    boundaries.extend([tag]*len(conn))
        cells, faces = np.concatenate(cells), np.concatenate(faces)
        bodies, boundaries = np.array(bodies), np.array(boundaries)
        np.savez_compressed(out/"mesh.npz", points=points, cells=cells, bodies=bodies,
                            faces=faces, boundaries=boundaries)
        audit = audit_mesh(manifest, points, cells, bodies, faces, boundaries)
        audit.update(mesh_size_m=size_m, gmsh_version=gmsh.__version__)
        manifest["boundary_groups"] = {str(b): BC_NAMES.get(b, f"contact_{b}") for b in surfaces}
        (out/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
        (out/"audit.json").write_text(json.dumps(audit, indent=2)+"\n")
        return audit
    finally:
        (out/"gmsh.log").write_text("\n".join(gmsh.logger.get())+"\n")
        gmsh.logger.stop()
        gmsh.finalize()


def ideal_reference(manifest, current_a, load_w, hot_k=300.):
    cfg = manifest["config"]
    n, w, h = cfg["couples"], cfg["leg_width_m"], cfg["leg_height_m"]
    alpha = n*(PROPERTIES["P"][2]-PROPERTIES["N"][2])
    rlegs = n*h/w**2*(1/PROPERTIES["P"][1]+1/PROPERTIES["N"][1])
    rmetal = 0.
    for b in manifest["bodies"]:
        box = b["box_m"]
        if b["kind"] == "bridge":
            # Centre-to-centre 1-D estimate; 3D turn/spreading resistance is not fitted.
            axis = b["cut_axis"]
            rmetal += (box[axis+3]-w)/(PROPERTIES["Cu"][1]*w*cfg["copper_m"])
        elif b["kind"] == "terminal":
            rmetal += .5*w/(PROPERTIES["Cu"][1]*w*cfg["copper_m"])
    resistance = rlegs+rmetal
    conductance = n*(PROPERTIES["P"][0]+PROPERTIES["N"][0])*w*w/h
    if conductance+alpha*current_a <= 0:
        raise ValueError("Unstable analytical reference denominator")
    cold = (conductance*hot_k+load_w+.5*current_a**2*resistance)/(conductance+alpha*current_a)
    voltage = resistance*current_a+alpha*(hot_k-cold)
    return {"alpha_v_k": alpha, "leg_resistance_ohm": rlegs,
            "estimated_copper_resistance_ohm": rmetal, "resistance_ohm": resistance,
            "conductance_w_k": conductance, "cold_k": cold, "delta_t_k": hot_k-cold,
            "voltage_v": voltage, "power_w": current_a*voltage}


def write_sif(path, mesh, current_a, load_w=.008, fixed_cold_k=None):
    if not np.isfinite([current_a, load_w]).all() or load_w < 0:
        raise ValueError("Finite current and nonnegative load required")
    if fixed_cold_k is not None and (not np.isfinite(fixed_cold_k) or fixed_cold_k <= 0):
        raise ValueError("Positive finite cold temperature required")
    manifest = json.loads((mesh/"manifest.json").read_text())
    path.parent.mkdir(parents=True, exist_ok=True)
    for source in (mesh/"elmer").glob("mesh.*"):
        target = path.parent/source.name
        if not target.exists():
            target.symlink_to(source.resolve())
    text = f'''Check Keywords Warn
Header
  Mesh DB "{path.parent.resolve()}" "."
End
Simulation
  Coordinate System = Cartesian 3D
  Simulation Type = Steady State
  Steady State Max Iterations = 1
  Output Intervals(1) = 1
  Output File = "solution.result"
  Post File = "fields.vtu"
End
Initial Condition 1
  Temperature = Real 300
  Potential = Real 0
End
Body Force 1
  Heat Source = Real 0
  Current Source = Real 0
End
Equation 1
  Active Solvers(1) = 1
End
Solver 1
  Equation = "ThermoElectric"
  Variable = POT[Temperature:1 Potential:1]
  Procedure = "ThermoElectricSolver" "ThermoElectricSolver"
  Element = "p:1"
  Nonlinear System Convergence Tolerance = 1e-10
  Nonlinear System Max Iterations = 40
  Nonlinear System Newton After Iterations = 2
  Nonlinear System Newton After Tolerance = 1e-7
  Linear System Solver = Direct
  Linear System Direct Method = UMFPACK
  Linear System Row Equilibration = Logical True
  Linear System Residual Output = 1
  Steady State Convergence Tolerance = 1e-10
End
'''
    material_ids = {name: i for i, name in enumerate(PROPERTIES, 1)}
    for body in manifest["bodies"]:
        text += f'''Body {body['id']}
  Target Bodies(1) = {body['id']}
  Name = "{body['name']}"
  Equation = 1
  Material = {material_ids[body['material']]}
  Body Force = 1
  Initial Condition = 1
End
'''
    for name, values in PROPERTIES.items():
        text += f"Material {material_ids[name]}\n"
        for key, value in zip(("Heat Conductivity", "Electric Conductivity", "Seebeck Coefficient",
                               "Density", "Heat Capacity"), values):
            text += f"  {key} = Real {value:.16g}\n"
        text += "End\n"
    text += '''Boundary Condition 1
  Target Boundaries(1) = 101
  Temperature = Real 300
End
Boundary Condition 2
  Target Boundaries(1) = 102
'''
    text += (f"  Heat Flux = Real {load_w/manifest['cold_area_m2']:.16g}\n" if fixed_cold_k is None
             else f"  Temperature = Real {fixed_cold_k:.16g}\n")
    text += f'''End
Boundary Condition 3
  Target Boundaries(1) = 103
  Electric Flux = Real {current_a/manifest['terminal_planes']['103']['area_m2']:.16g}
End
Boundary Condition 4
  Target Boundaries(1) = 104
  Potential = Real 0
End
'''
    path.write_text(text)
    meta = {"current_a": current_a, "load_w": load_w if fixed_cold_k is None else None,
            "fixed_cold_k": fixed_cold_k, "hot_k": 300., "elmer_commit": ELMER_COMMIT,
            "couples": manifest["config"]["couples"],
            "boundary_case": "fixed_hot_load" if fixed_cold_k is None else "fixed_hot_fixed_cold"}
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2)+"\n")
