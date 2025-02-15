import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.collections import PatchCollection
from modflow_devtools.markers import requires_pkg

import flopy
from flopy.mf6 import MFSimulation


@pytest.mark.mf6
@pytest.mark.xfail(reason="sometimes get LineCollections instead of PatchCollections")
def test_cross_section_bc_gwfs_disv(example_data_path):
    mpath = example_data_path / "mf6" / "test003_gwfs_disv"
    sim = MFSimulation.load(sim_ws=mpath)
    ml6 = sim.get_model("gwf_1")
    xc = flopy.plot.PlotCrossSection(ml6, line={"line": ([0, 5.5], [10, 5.5])})
    xc.plot_bc("CHD")
    ax = xc.ax

    assert len(ax.collections) != 0, "Boundary condition was not drawn"

    for col in ax.collections:
        assert isinstance(
            col, PatchCollection
        ), f"Unexpected collection type: {type(col)}"


@pytest.mark.mf6
@pytest.mark.xfail(reason="sometimes get LineCollections instead of PatchCollections")
def test_cross_section_bc_lake2tr(example_data_path):
    mpath = example_data_path / "mf6" / "test045_lake2tr"
    sim = MFSimulation.load(sim_ws=mpath)
    ml6 = sim.get_model("lakeex2a")
    xc = flopy.plot.PlotCrossSection(ml6, line={"row": 10})
    xc.plot_bc("LAK")
    xc.plot_bc("SFR")

    ax = xc.ax
    assert len(ax.collections) != 0, "Boundary condition was not drawn"

    for col in ax.collections:
        assert isinstance(
            col, PatchCollection
        ), f"Unexpected collection type: {type(col)}"


@pytest.mark.mf6
@pytest.mark.xfail(reason="sometimes get LineCollections instead of PatchCollections")
def test_cross_section_bc_2models_mvr(example_data_path):
    mpath = example_data_path / "mf6" / "test006_2models_mvr"
    sim = MFSimulation.load(sim_ws=mpath)
    ml6 = sim.get_model("parent")
    xc = flopy.plot.PlotCrossSection(ml6, line={"column": 1})
    xc.plot_bc("MAW")

    ax = xc.ax
    assert len(ax.collections) > 0, "Boundary condition was not drawn"

    for col in ax.collections:
        assert isinstance(
            col, PatchCollection
        ), f"Unexpected collection type: {type(col)}"


@pytest.mark.mf6
@pytest.mark.xfail(reason="sometimes get LineCollections instead of PatchCollections")
def test_cross_section_bc_UZF_3lay(example_data_path):
    mpath = example_data_path / "mf6" / "test001e_UZF_3lay"
    sim = MFSimulation.load(sim_ws=mpath)
    ml6 = sim.get_model("gwf_1")

    xc = flopy.plot.PlotCrossSection(ml6, line={"row": 0})
    xc.plot_bc("UZF")

    ax = xc.ax
    assert len(ax.collections) != 0, "Boundary condition was not drawn"

    for col in ax.collections:
        assert isinstance(
            col, PatchCollection
        ), f"Unexpected collection type: {type(col)}"


def structured_square_grid(side: int = 10, thick: int = 10):
    """
    Creates a basic 1-layer structured grid with the given thickness and number of
    cells per side
    Parameters
    ----------
    side : The number of cells per side
    thick : The thickness of the grid's single layer
    Returns
    -------
    A single-layer StructuredGrid of the given size and thickness
    """

    from flopy.discretization.structuredgrid import StructuredGrid

    delr = np.ones(side)
    delc = np.ones(side)
    top = np.ones((side, side)) * thick
    botm = np.ones((side, side)) * (top - thick).reshape(1, side, side)
    return StructuredGrid(delr=delr, delc=delc, top=top, botm=botm)


@requires_pkg("shapely")
@pytest.mark.parametrize(
    "line",
    [(), [], (()), [[]], (0, 0), [0, 0], [[0, 0]]],
)
def test_cross_section_invalid_lines_raise_error(line):
    grid = structured_square_grid(side=10)
    with pytest.raises(ValueError):
        flopy.plot.PlotCrossSection(modelgrid=grid, line={"line": line})


@requires_pkg("shapely")
@pytest.mark.parametrize(
    "line",
    [
        # diagonal
        [(0, 0), (10, 10)],
        ([0, 0], [10, 10]),
        # horizontal
        ([0, 5.5], [10, 5.5]),
        [(0, 5.5), (10, 5.5)],
        # vertical
        [(5.5, 0), (5.5, 10)],
        ([5.5, 0], [5.5, 10]),
        # multiple segments
        [(0, 0), (4, 6), (10, 10)],
        ([0, 0], [4, 6], [10, 10]),
    ],
)
def test_cross_section_valid_line_representations(line):
    from shapely.geometry import LineString as SLS

    from flopy.utils.geometry import LineString as FLS

    grid = structured_square_grid(side=10)

    fls = FLS(line)
    sls = SLS(line)

    # use raw, flopy.utils.geometry and shapely.geometry representations
    lxc = flopy.plot.PlotCrossSection(modelgrid=grid, line={"line": line})
    fxc = flopy.plot.PlotCrossSection(modelgrid=grid, line={"line": fls})
    sxc = flopy.plot.PlotCrossSection(modelgrid=grid, line={"line": sls})

    # make sure parsed points are identical for all line representations
    assert np.allclose(lxc.pts, fxc.pts) and np.allclose(lxc.pts, sxc.pts)
    assert set(lxc.xypts.keys()) == set(fxc.xypts.keys()) == set(sxc.xypts.keys())
    for k in lxc.xypts.keys():
        assert np.allclose(lxc.xypts[k], fxc.xypts[k]) and np.allclose(
            lxc.xypts[k], sxc.xypts[k]
        )


@pytest.mark.parametrize(
    "line",
    [
        0,
        [0],
        [0, 0],
        (0, 0),
        [(0, 0)],
        ([0, 0]),
    ],
)
@requires_pkg("shapely", "geojson")
def test_cross_section_invalid_line_representations_fail(line):
    grid = structured_square_grid(side=10)
    with pytest.raises(ValueError):
        flopy.plot.PlotCrossSection(modelgrid=grid, line={"line": line})


def test_plot_limits():
    xymin, xymax = 0, 1000
    cellsize = 50
    nrow = (xymax - xymin) // cellsize
    ncol = nrow
    nlay = 1

    delc = np.full((nrow,), cellsize)
    delr = np.full((ncol,), cellsize)

    top = np.full((nrow, ncol), 100)
    botm = np.full((nlay, nrow, ncol), 0)
    idomain = np.ones(botm.shape, dtype=int)

    grid = flopy.discretization.StructuredGrid(
        delc=delc, delr=delr, top=top, botm=botm, idomain=idomain
    )

    fig, ax = plt.subplots()
    user_extent = 0, 500, 0, 25
    ax.axis(user_extent)

    pxc = flopy.plot.PlotCrossSection(modelgrid=grid, ax=ax, line={"column": 4})
    pxc.plot_grid()

    lims = ax.axes.viewLim
    if (lims.x0, lims.x1, lims.y0, lims.y1) != user_extent:
        raise AssertionError("PlotMapView not checking for user scaling")

    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 8))
    pxc = flopy.plot.PlotCrossSection(modelgrid=grid, ax=ax, line={"column": 4})
    pxc.plot_grid()

    lims = ax.axes.viewLim
    if (lims.x0, lims.x1, lims.y0, lims.y1) != pxc.extent:
        raise AssertionError("PlotMapView auto extent setting not working")

    plt.close(fig)


def test_plot_centers():
    from matplotlib.collections import PathCollection

    nlay = 1
    nrow = 10
    ncol = 10

    delc = np.ones((nrow,))
    delr = np.ones((ncol,))
    top = np.ones((nrow, ncol))
    botm = np.zeros((nlay, nrow, ncol))
    idomain = np.ones(botm.shape, dtype=int)

    idomain[0, :, 0:3] = 0

    grid = flopy.discretization.StructuredGrid(
        delc=delc, delr=delr, top=top, botm=botm, idomain=idomain
    )

    line = {"line": [(0, 0), (10, 10)]}
    active_xc_cells = 7

    pxc = flopy.plot.PlotCrossSection(modelgrid=grid, line=line)
    pc = pxc.plot_centers()

    if not isinstance(pc, PathCollection):
        raise AssertionError("plot_centers() not returning PathCollection object")

    verts = pc._offsets
    if not verts.shape[0] == active_xc_cells:
        raise AssertionError("plot_centers() not properly masking inactive cells")

    center_dict = pxc.projctr
    edge_dict = pxc.projpts

    for node, center in center_dict.items():
        verts = np.array(edge_dict[node]).T
        xmin = np.min(verts[0])
        xmax = np.max(verts[0])
        if xmax < center < xmin:
            raise AssertionError("Cell center not properly drawn on cross-section")
