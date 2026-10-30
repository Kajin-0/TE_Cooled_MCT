"""New scoped verification utilities; no modification of accepted FEM modules."""
import json
from pathlib import Path
import numpy as np
from .g2d_data import ROOT, sha, dump


def affine_geometry(points, cells):
    """Independent affine-system construction, not the baseline cofactor routine."""
    xyz = points[cells]
    matrix = np.concatenate([np.ones((*xyz.shape[:2], 1)), xyz], axis=2)
    gradients = np.linalg.inv(matrix)[:, 1:, :].transpose(0, 2, 1)
    volume = np.abs(np.linalg.det(xyz[:, 1:] - xyz[:, :1])) / 6
    if np.any(volume <= 0):
        raise ValueError('Degenerate tetrahedron')
    return volume, gradients


def boundary_owners(cells, faces):
    """Search only stars of boundary nodes; require exactly one owning cell."""
    nodes = np.unique(faces)
    candidates = np.flatnonzero(np.isin(cells, nodes).any(axis=1))
    wanted = {tuple(sorted(row)): [] for row in faces}
    for ci in candidates:
        row = cells[ci]
        for omit in range(4):
            key = tuple(sorted(np.delete(row, omit)))
            if key in wanted:
                wanted[key].append(int(ci))
    if any(len(v) != 1 for v in wanted.values()):
        raise ValueError('Boundary face is missing, internal or duplicated')
    return np.array([wanted[tuple(sorted(row))][0] for row in faces])


def outward_vectors(points, cells, faces, owners):
    xyz = points[faces]
    area_vector = np.cross(xyz[:, 1]-xyz[:, 0], xyz[:, 2]-xyz[:, 0])/2
    distance = xyz.mean(1)-points[cells[owners]].mean(1)
    signed = np.einsum('ij,ij->i', area_vector, distance)
    if np.any(abs(signed) < 1e-30):
        raise ValueError('Ambiguous boundary normal')
    area_vector[signed < 0] *= -1
    return area_vector


def guard():
    from reports.fem_report_data import verify_baseline
    from reports.validate_report import verify_files
    result = verify_baseline()
    verify_files(ROOT/'reports/generated')
    pdf = ROOT/'reports/generated/HgCdTe_Engineering_Assessment.pdf'
    if sha(pdf) != '751284cabaffa34f7f338f85ffa05cd88c59e157831f3dc9f1837d7758f3ac1c':
        raise ValueError('Protected Revision 2 PDF changed')
    result['revision2_pdf_sha256'] = sha(pdf)
    return result
