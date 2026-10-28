"""G1: genuine coupled 3D Elmer thermoelectric benchmark, SI throughout.

This module generates solver input and checks geometry. It does not replace
Elmer's ThermoElectricSolver with a reduced-order temperature calculation.
Optional gmsh/meshio are imported only by the FEM workflow.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

ELMER_COMMIT = "a19504ac53ec222e3355e182b08f2ff280c2203a"
# k [W/m K], sigma [S/m], S [V/K], density [kg/m3], Cp [J/kg K].
# Mixed literature verification constants, NOT an OEM material calibration.
MATERIALS = {
    1: (1.5, 1.4e5, 160e-6, 7529., 544.),
    2: (1.5, 1.655e5, -170e-6, 7529., 544.),
    3: (400., 1/1.72e-8, 0., 8960., 385.),
    4: (400., 1/1.72e-8, 0., 8960., 385.),
    5: (400., 1/1.72e-8, 0., 8960., 385.),
    6: (30., 1e-12, 0., 3900., 880.),
    7: (30., 1e-12, 0., 3900., 880.),
}
NAMES = {1: "p_leg", 2: "n_leg", 3: "cold_bridge", 4: "p_hot_pad",
         5: "n_hot_pad", 6: "hot_alumina", 7: "cold_alumina"}
BOUNDARIES = {101: "hot_bath", 102: "cold_load", 103: "n_current_in",
              104: "p_ground"}
# Boxes: x,y,z, dx,dy,dz in metres; no artificial contact gaps.
BOXES = {
    1: (0., 0., .1e-3, .4e-3, .4e-3, 1e-3),
    2: (.8e-3, 0., .1e-3, .4e-3, .4e-3, 1e-3),
    3: (0., 0., 1.1e-3, 1.2e-3, .4e-3, .1e-3),
    4: (0., 0., 0., .4e-3, .4e-3, .1e-3),
    5: (.8e-3, 0., 0., .4e-3, .4e-3, .1e-3),
    6: (-.1e-3, -.1e-3, -.2e-3, 1.4e-3, .6e-3, .2e-3),
    7: (-.1e-3, -.1e-3, 1.2e-3, 1.4e-3, .6e-3, .2e-3),
}
COLD_AREA = 1.4e-3*.6e-3
TERMINAL_AREA = .4e-3*.1e-3


def reference(current_a: float, load_w: float = .002, hot_k: float = 300.) -> dict:
    """Independent ideal constant-property couple, isothermal end junctions.

    Omits finite Cu and alumina resistances/spreading; comparison is a limiting
    reference, not an assertion that finite 3D geometry is exactly one dimensional.
    """
    alpha = MATERIALS[1][2] - MATERIALS[2][2]
    resistance = (1/MATERIALS[1][1] + 1/MATERIALS[2][1])*1e-3/(.4e-3)**2
    conductance = (MATERIALS[1][0]+MATERIALS[2][0])*(.4e-3)**2/1e-3
    denominator = conductance + alpha*current_a
    if denominator <= 0:
        raise ValueError("No positive stable ideal-couple denominator")
    cold = (conductance*hot_k + load_w + .5*current_a**2*resistance)/denominator
    voltage = current_a*resistance + alpha*(hot_k-cold)
    return {"cold_k": cold, "delta_t_k": hot_k-cold, "voltage_v": voltage,
            "power_w": current_a*voltage, "alpha_v_k": alpha,
            "resistance_ohm": resistance, "conductance_w_k": conductance}


def generate_mesh(out: Path, size_m: float) -> dict:
    import gmsh
    out.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("Mesh.RandomSeed", 20261028)
        gmsh.model.add("G1_PN")
        originals = [(3, gmsh.model.occ.addBox(*BOXES[b])) for b in NAMES]
        _, maps = gmsh.model.occ.fragment(originals[:1], originals[1:])
        gmsh.model.occ.synchronize()
        volume_body = {}
        for b, fragments in zip(NAMES, maps):
            tags = [t for d, t in fragments if d == 3]
            gmsh.model.addPhysicalGroup(3, tags, b, NAMES[b])
            volume_body.update({t: b for t in tags})
        boundary_surfaces = {b: [] for b in BOUNDARIES}
        contact_surfaces = {}
        tol = 1e-10
        for _, s in gmsh.model.getEntities(2):
            adj, _ = gmsh.model.getAdjacencies(2, s)
            bodies = tuple(sorted({volume_body[int(v)] for v in adj}))
            x, y, z = gmsh.model.occ.getCenterOfMass(2, s)
            if len(bodies) == 2:
                contact_surfaces.setdefault(bodies, []).append(s)
            elif len(bodies) == 1:
                if abs(z+.2e-3) < tol:
                    boundary_surfaces[101].append(s)
                elif abs(z-1.4e-3) < tol:
                    boundary_surfaces[102].append(s)
                elif bodies == (5,) and abs(x-1.2e-3) < tol:
                    boundary_surfaces[103].append(s)
                elif bodies == (4,) and abs(x) < tol:
                    boundary_surfaces[104].append(s)
        for b, surfaces in boundary_surfaces.items():
            if not surfaces:
                raise ValueError(f"Missing boundary {b}")
            gmsh.model.addPhysicalGroup(2, surfaces, b, BOUNDARIES[b])
        for i, (pair, surfaces) in enumerate(sorted(contact_surfaces.items()), 201):
            gmsh.model.addPhysicalGroup(2, surfaces, i,
                                       "contact_"+"_".join(NAMES[b] for b in pair))
        # Tag every exposed sidewall as well: natural total q.n=J.n=0.
        tagged = {s for ss in boundary_surfaces.values() for s in ss}
        sides = [s for _, s in gmsh.model.getEntities(2)
                 if s not in tagged and len(gmsh.model.getAdjacencies(2, s)[0]) == 1]
        gmsh.model.addPhysicalGroup(2, sides, 105, "adiabatic_insulated_sides")
        gmsh.option.setNumber("Mesh.MeshSizeMin", size_m)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size_m)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.model.mesh.generate(3)
        gmsh.write(str(out/"couple.msh"))
        gmsh.write(str(out/"couple.geo_unrolled"))
        tags, coords, _ = gmsh.model.mesh.getNodes()
        points = np.asarray(coords).reshape(-1, 3)
        node_index = {int(t): i for i, t in enumerate(tags)}
        def indices(nodes, width):
            return np.fromiter((node_index[int(t)] for t in nodes), dtype=int).reshape(-1, width)
        cells, cell_tags, faces, face_tags = [], [], [], []
        for volume, b in volume_body.items():
            types, _, node_arrays = gmsh.model.mesh.getElements(3, volume)
            for typ, nodes in zip(types, node_arrays):
                if typ != 4:
                    raise ValueError("Only linear tetrahedra supported")
                conn = indices(nodes, 4)
                cells.append(conn)
                cell_tags.extend([b]*len(conn))
        for _, phys in gmsh.model.getPhysicalGroups(2):
            for s in gmsh.model.getEntitiesForPhysicalGroup(2, phys):
                types, _, node_arrays = gmsh.model.mesh.getElements(2, int(s))
                for typ, nodes in zip(types, node_arrays):
                    if typ != 2:
                        raise ValueError("Only triangular boundary faces supported")
                    conn = indices(nodes, 3)
                    faces.append(conn)
                    face_tags.extend([phys]*len(conn))
        cells, faces = np.concatenate(cells), np.concatenate(faces)
        cell_tags, face_tags = np.array(cell_tags), np.array(face_tags)
        np.savez_compressed(out/"mesh.npz", points=points, cells=cells, bodies=cell_tags,
                            faces=faces, boundaries=face_tags)
        audit = audit_mesh(points, cells, cell_tags, faces, face_tags)
        audit["mesh_size_m"] = size_m
        audit["gmsh_version"] = gmsh.__version__
        (out/"audit.json").write_text(json.dumps(audit, indent=2)+"\n")
        return audit
    finally:
        gmsh.finalize()


def tetra_geometry(points, cells):
    coords = points[cells]
    edge = coords[:, 1:]-coords[:, :1]
    volumes = np.abs(np.linalg.det(edge))/6
    inv = np.linalg.inv(edge)
    gradients = np.empty((len(cells), 4, 3))
    gradients[:, 1:, :] = inv.transpose(0, 2, 1)
    gradients[:, 0, :] = -gradients[:, 1:, :].sum(axis=1)
    return volumes, gradients


def audit_mesh(points, cells, bodies, faces, boundaries):
    volumes, _ = tetra_geometry(points, cells)
    if not np.all(volumes > 0):
        raise ValueError("Degenerate elements")
    measured = {b: float(volumes[bodies == b].sum()) for b in NAMES}
    for b, box in BOXES.items():
        if not math.isclose(measured[b], np.prod(box[3:]), rel_tol=1e-8):
            raise ValueError(f"Volume mismatch in body {b}")
    adjacency = {}
    for ci, c in enumerate(cells):
        for face in ((c[1], c[2], c[3]), (c[0], c[2], c[3]),
                     (c[0], c[1], c[3]), (c[0], c[1], c[2])):
            adjacency.setdefault(tuple(sorted(face)), []).append(ci)
    if any(len(a) > 2 for a in adjacency.values()):
        raise ValueError("Nonmanifold mesh")
    contacts = {}
    for f, adj in adjacency.items():
        if len(adj) == 2 and bodies[adj[0]] != bodies[adj[1]]:
            pair = tuple(sorted((int(bodies[adj[0]]), int(bodies[adj[1]]))))
            p = points[list(f)]
            contacts[pair] = contacts.get(pair, 0.) + np.linalg.norm(np.cross(p[1]-p[0], p[2]-p[0]))/2
    expected = {(1, 3): 1.6e-7, (2, 3): 1.6e-7, (1, 4): 1.6e-7,
                (2, 5): 1.6e-7, (4, 6): 1.6e-7, (5, 6): 1.6e-7,
                (3, 7): 4.8e-7}
    if set(contacts) != set(expected):
        raise ValueError(f"Unexpected contact graph: {contacts}")
    for pair, area in expected.items():
        if not math.isclose(contacts[pair], area, rel_tol=1e-8):
            raise ValueError(f"Gap or wrong interface area: {pair}")
    for f, b in zip(faces, boundaries):
        a = adjacency.get(tuple(sorted(f)), [])
        if len(a) != (2 if b >= 201 else 1):
            raise ValueError(f"Nonconformal tagged face {b}")
    # Deleting the bridge must separate both electrical terminal branches.
    def connected(remove_bridge=False):
        edges = [p for p in contacts if max(p) <= 5 and (not remove_bridge or 3 not in p)]
        seen, stack = set(), [4]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            stack.extend(w for p in edges if v in p for w in p if w not in seen)
        return 5 in seen
    if not connected() or connected(True):
        raise ValueError("Invalid conductor series path")
    return {"passed": True, "nodes": len(points), "tetrahedra": len(cells),
            "volumes_m3": {NAMES[b]: v for b, v in measured.items()},
            "contact_areas_m2": {f"{NAMES[a]}:{NAMES[b]}": v for (a, b), v in contacts.items()},
            "series_path": "N hot pad -> N leg -> cold Cu bridge -> P leg -> P hot pad",
            "bridge_removal_disconnects_terminals": True,
            "contact_resistances": "zero electrical and thermal contact resistance",
            "alumina_sigma_s_m": 1e-12}


def write_sif(path: Path, mesh: Path, current_a: float, load_w=.002,
              fixed_cold_k=None, slopes=False, alumina_sigma=1e-12):
    """Temperature slopes are explicit synthetic verification inputs, per kelvin.

    Material interpolation occurs in Elmer, including its coupled Peltier term;
    these slopes are not measured BiTe curves.
    """
    if not np.isfinite([current_a, load_w, alumina_sigma]).all() or alumina_sigma <= 0:
        raise ValueError("Finite BCs and positive insulating regularization required")
    if fixed_cold_k is not None and (not np.isfinite(fixed_cold_k) or fixed_cold_k <= 0):
        raise ValueError("Positive finite absolute temperature required")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Elmer writes restart files relative to Mesh.Name, even for an absolute
    # Output File. Present the shared mesh in each case via lightweight links.
    for source in mesh.glob("mesh.*"):
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
Constants
  Stefan Boltzmann = 5.670374419e-8
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
  Nonlinear System Max Iterations = 60
  Nonlinear System Newton After Iterations = 2
  Nonlinear System Newton After Tolerance = 1e-7
  Linear System Solver = Direct
  Linear System Direct Method = UMFPACK
  Linear System Row Equilibration = Logical True
  Linear System Residual Output = 1
  Steady State Convergence Tolerance = 1e-10
End
'''
    for b, props in MATERIALS.items():
        text += f'''Body {b}
  Target Bodies(1) = {b}
  Name = "{NAMES[b]}"
  Equation = 1
  Material = {b}
  Body Force = 1
  Initial Condition = 1
End
Material {b}
'''
        for name, value in zip(("Heat Conductivity", "Electric Conductivity", "Seebeck Coefficient",
                                "Density", "Heat Capacity"), props):
            if b >= 6 and name == "Electric Conductivity":
                value = alumina_sigma
            slope = {"Heat Conductivity": .0005, "Electric Conductivity": -.001,
                     "Seebeck Coefficient": .0002}.get(name, 0.) if slopes and b <= 2 else 0.
            if slope:
                text += f'  {name} = Variable Temperature\n    Real MATC "{value:.16g}*(1+{slope:.16g}*(tx-300))"\n'
            else:
                text += f"  {name} = Real {value:.16g}\n"
        text += "End\n"
    text += f'''Boundary Condition 1
  Target Boundaries(1) = 101
  Temperature = Real 300
End
Boundary Condition 2
  Target Boundaries(1) = 102
'''
    text += (f"  Temperature = Real {fixed_cold_k:.16g}\n" if fixed_cold_k is not None
             else f"  Heat Flux = Real {load_w/COLD_AREA:.16g}\n")
    text += f'''End
Boundary Condition 3
  Target Boundaries(1) = 103
  Electric Flux = Real {current_a/TERMINAL_AREA:.16g}
End
Boundary Condition 4
  Target Boundaries(1) = 104
  Potential = Real 0
End
'''
    path.write_text(text)
    metadata = {"current_a": current_a, "load_w": load_w if fixed_cold_k is None else None,
                "fixed_cold_k": fixed_cold_k, "temperature_slopes": slopes,
                "alumina_sigma_s_m": alumina_sigma, "elmer_commit": ELMER_COMMIT,
                "boundary_case": "fixed_hot_fixed_cold" if fixed_cold_k is not None else "fixed_hot_cold_heat_load"}
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2)+"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/fem-g1/mesh"))
    parser.add_argument("--size-mm", type=float, default=.12)
    args = parser.parse_args()
    print(json.dumps(generate_mesh(args.out, args.size_mm*1e-3), indent=2))


if __name__ == "__main__":
    main()
