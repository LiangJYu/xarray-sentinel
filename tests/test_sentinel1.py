import pathlib
import tempfile

import numpy as np
import xarray as xr

from xarray_sentinel import sentinel1

DATA_FOLDER = pathlib.Path(__file__).parent / "data"


def test_filter_missing_path() -> None:
    existing_path = (
        DATA_FOLDER
        / "S1B_IW_SLC__1SDV_20210401T052622_20210401T052650_026269_032297_EFA4.SAFE"
    )

    missing_path = tempfile.mktemp()
    ancillary_data_paths = {
        "paths1": {"path1": existing_path, "path2": missing_path},
        "paths2": {"path1": missing_path, "path2": missing_path},
    }

    res = sentinel1.filter_missing_path(ancillary_data_paths)
    expected = {"paths1": {"path1": existing_path}, "paths2": {}}

    assert res == expected


def test_build_burst_id() -> None:
    product_attrs = {"sat:relative_orbit": 168}
    burst_centre = xr.Dataset(
        dict(
            latitude=xr.DataArray([11.8475875]), longitude=xr.DataArray([47.16626783]),
        )
    )
    burst_id = sentinel1.build_burst_id(product_attrs, burst_centre)
    assert burst_id == "R168-N118-E0472"


def test_get_burst_info() -> None:
    base_path = (
        DATA_FOLDER
        / "S1B_IW_SLC__1SDV_20210401T052622_20210401T052650_026269_032297_EFA4.SAFE"
    )
    subswath_data = {
        "annotation_path": {
            "vh": str(
                base_path
                / "annotation/s1b-iw1-slc-vh-20210401t052624-20210401t052649-026269-032297-001.xml"
            ),
        },
    }
    product_attrs = {"sat:relative_orbit": 168}

    partial_expected_burst_info = {
        "R168-N471-E0118": {
            "burst_centre_latitude": 47.086949354032605,
            "burst_centre_longitude": 11.806954918616803,
            "burst_pos": 0,
            "burst_first_line": 0,
            "burst_last_line": 1500,
            "burst_first_pixel": 0,
            "burst_last_pixel": 21631,
        },
    }

    burst_info = sentinel1.get_burst_info(product_attrs, subswath_data)

    assert burst_info is not None
    assert "R168-N471-E0118" in burst_info

    res = burst_info["R168-N471-E0118"]
    expected = partial_expected_burst_info["R168-N471-E0118"]

    assert np.isclose(res["burst_centre_longitude"], expected["burst_centre_longitude"])
    assert np.isclose(res["burst_centre_latitude"], expected["burst_centre_latitude"])
    assert res["burst_pos"] == expected["burst_pos"]
    assert res["burst_first_line"] == expected["burst_first_line"]
    assert res["burst_last_line"] == expected["burst_last_line"]
    assert res["burst_first_pixel"] == expected["burst_first_pixel"]
    assert res["burst_last_pixel"] == expected["burst_last_pixel"]


def test_find_avalable_groups() -> None:
    base_path = (
        DATA_FOLDER
        / "S1B_IW_SLC__1SDV_20210401T052622_20210401T052650_026269_032297_EFA4.SAFE"
    )
    ancillary_data_paths = {
        "iw1": {
            "annotation_path": {
                "vv": f"{base_path}/annotation/"
                + "s1b-iw1-slc-vv-20210401t052624-20210401t052649-026269-032297-004.xml",
            },
        },
    }
    product_attrs = {"sat:relative_orbit": 168}
    expected_groups = {
        "IW1",
        "IW1/attitude",
        "IW1/gcp",
        "IW1/orbit",
        "IW1/R168-N471-E0118",
        "IW1/R168-N469-E0118",
        "IW1/R168-N468-E0117",
        "IW1/R168-N466-E0117",
        "IW1/R168-N464-E0116",
        "IW1/R168-N463-E0116",
        "IW1/R168-N461-E0116",
        "IW1/R168-N459-E0115",
        "IW1/R168-N458-E0115",
    }

    groups = sentinel1.find_avalable_groups(ancillary_data_paths, product_attrs)
    assert set(groups) == expected_groups


def test_compute_burst_centre() -> None:
    gcp = xr.Dataset(
        {
            "latitude": xr.DataArray(
                np.arange(5).reshape(5, 1), dims=("azimuth_time", "slant_range_time")
            ),
            "longitude": xr.DataArray(
                np.arange(5).reshape(5, 1) * 10,
                dims=("azimuth_time", "slant_range_time"),
            ),
        },
        attrs={"burst_count": 4},
    )
    res = sentinel1.compute_burst_centre(gcp)
    assert np.allclose(res.latitude, [0.5, 1.5, 2.5, 3.5])
    assert np.allclose(res.longitude, [5, 15, 25, 35])
