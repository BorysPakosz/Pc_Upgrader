import pytest
from types import SimpleNamespace

from hardware.utils.helpers import (
    _to_float,
    _price,
    _bench,
    parse_gb,
    parse_size,
    normalize_socket,
    extract_ddr_type,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "x,expected",
    [
        ("10", 10.0),
        (10, 10.0),
        ("10.5", 10.5),
        (None, None),
        ("abc", None),
    ],
)
def test__to_float(x, expected):
    assert _to_float(x, default=None) == expected


@pytest.mark.unit
def test__price_reads_attr_or_inf():
    part = SimpleNamespace(price="123.45")
    assert _price(part) == 123.45
    assert _price(SimpleNamespace()) == float("inf")


@pytest.mark.unit
def test__bench_reads_attr_or_zero():
    part = SimpleNamespace(benchmark="99.9")
    assert _bench(part) == 99.9
    assert _bench(SimpleNamespace()) == 0.0


@pytest.mark.unit
@pytest.mark.parametrize(
    "val,expected",
    [
        ("16 GB", 16),
        ("32GB", 32),
        ("64 gb (dual)", 64),
        ("8 (cośtam)", 8),
        ("nope", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_gb(val, expected):
    assert parse_gb(val) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "val,expected",
    [
        (512, 512),
        (512.9, 512),
        ("512GB", 512),
        ("  1 024  MB ", 1024),
        ("abc", 0),
        (None, 0),
    ],
)
def test_parse_size(val, expected):
    assert parse_size(val) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "socket,expected",
    [
        (" AM5 ", "AM5"),
        ("LGA1700", "LGA1700"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_socket(socket, expected):
    assert normalize_socket(socket) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "mem,expected",
    [
        ("DDR5 6000", "DDR5"),
        ("G.SKILL DDR4 Ripjaws", "DDR4"),
        ("SO-DIMM DDR3", "DDR3"),
        ("Unknown", None),
        (None, None),
    ],
)
def test_extract_ddr_type(mem, expected):
    assert extract_ddr_type(mem) == expected
