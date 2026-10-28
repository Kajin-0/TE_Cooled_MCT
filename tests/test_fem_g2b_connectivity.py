"""Reject disconnected fragments hidden behind one valid material/body tag."""
import numpy as np
import pytest

from tecooledmct.fem_g2b_connectivity import connectivity


def test_actual_face_connection_passes():
    cells=np.array([[0,1,2,3],[0,1,2,4]])
    assert connectivity(cells,np.array([1,2]),{1,2})["passed"]


@pytest.mark.parametrize("second",[[4,5,6,7],[3,4,5,6]])
def test_disconnected_or_point_only_same_tag_rejected(second):
    cells=np.array([[0,1,2,3],second])
    with pytest.raises(ValueError,match="disconnected"):
        connectivity(cells,np.array([1,1]),{1})
