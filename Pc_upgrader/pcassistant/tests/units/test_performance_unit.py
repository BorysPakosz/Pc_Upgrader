import pytest
from types import SimpleNamespace

from hardware.utils import performance


class DummyCPU:
    def __init__(self, benchmark=None, price=0):
        self.benchmark = benchmark
        self.price = price


class DummyGPU:
    def __init__(self, benchmark=None, price=0, recomended_ps=None, model="GPU"):
        self.benchmark = benchmark
        self.price = price
        self.recomended_ps = recomended_ps
        self.model = model


class DummyRAM:
    def __init__(self, size="16 GB", clock=3200, price=0):
        self.size = size
        self.clock = clock
        self.price = price


class DummySSD:
    def __init__(self, size="512GB", price=0):
        self.size = size
        self.price = price


class DummyHDD:
    def __init__(self, size="1 TB", price=0):
        self.size = size
        self.price = price


class DummyMobo:
    def __init__(self, socket="AM4"):
        self.socket = socket


@pytest.fixture(autouse=True)
def patch_models(monkeypatch):
    monkeypatch.setattr(performance, "CPU", DummyCPU)
    monkeypatch.setattr(performance, "GPU", DummyGPU)
    monkeypatch.setattr(performance, "RAM", DummyRAM)
    monkeypatch.setattr(performance, "SSD", DummySSD)
    monkeypatch.setattr(performance, "HDD", DummyHDD)
    monkeypatch.setattr(performance, "Motherboard", DummyMobo)


@pytest.mark.unit
def test_value_score_returns_ratio_and_zero_on_missing():
    part = DummyCPU(price=200, benchmark=1000)
    assert performance.value_score(part) == 5
    assert performance.value_score(DummyCPU(price=None, benchmark=None)) == 0


@pytest.mark.unit
def test_calculate_performance_gain_for_cpu_and_gpu():
    current_cpu = DummyCPU(benchmark=100)
    part_cpu = DummyCPU(benchmark=150)
    current_gpu = DummyGPU(benchmark=200)
    part_gpu = DummyGPU(benchmark=260)

    cpu_gain = performance.calculate_performance_gain(
        part_cpu, current_cpu, current_gpu, ram_size=0, ssd_size=0, hdd_size=0
    )
    gpu_gain = performance.calculate_performance_gain(
        part_gpu, current_cpu, current_gpu, ram_size=0, ssd_size=0, hdd_size=0
    )

    assert cpu_gain == 0.5
    assert gpu_gain == 0.3


@pytest.mark.unit
def test_calculate_performance_gain_for_memory_and_storage():
    current_cpu = DummyCPU()
    current_gpu = DummyGPU()

    ram_gain = performance.calculate_performance_gain(
        DummyRAM(size="32 GB"),
        current_cpu,
        current_gpu,
        ram_size=16,
        ssd_size=0,
        hdd_size=0,
    )
    ssd_gain = performance.calculate_performance_gain(
        DummySSD(size="1024GB"),
        current_cpu,
        current_gpu,
        ram_size=0,
        ssd_size=512,
        hdd_size=0,
    )
    hdd_gain = performance.calculate_performance_gain(
        DummyHDD(size="2000"),
        current_cpu,
        current_gpu,
        ram_size=0,
        ssd_size=0,
        hdd_size=1000,
    )

    assert ram_gain == 1.0
    assert ssd_gain == pytest.approx(1.0)
    assert hdd_gain == pytest.approx(1.0)


@pytest.mark.unit
@pytest.mark.parametrize(
    "chipset,expected",
    [
        ("Z690", 10),
        ("B450", 5),
        ("X670E", 10),
        ("A320", 2),
        ("Unknown", 1),
    ],
)
def test_get_chipset_tier_matches_known_values(chipset, expected):
    assert performance.get_chipset_tier(chipset) == expected


@pytest.mark.unit
def test_prepare_comparison_data_builds_gain_and_sets_types(monkeypatch):
    monkeypatch.setattr(
        performance, "find_similar_ssd", lambda size: DummySSD(size="512GB")
    )
    monkeypatch.setattr(
        performance, "find_similar_hdd", lambda size: DummyHDD(size="1 TB")
    )

    current_cpu = DummyCPU(benchmark=100)
    current_gpu = DummyGPU(benchmark=200)
    current_mobo = DummyMobo(socket="AM4")
    current_ram = DummyRAM(size="16 GB", clock=3200)

    proposal = {
        "parts": [
            DummyCPU(benchmark=150),
            DummyGPU(benchmark=260),
            DummyRAM(size="32 GB", clock=3600),
            DummySSD(size="1024GB"),
            DummyHDD(size="2000GB"),
            DummyMobo(socket="AM5"),
        ],
        "total_price": 1234.567,
        "psu_warning": None,
    }

    result = performance.prepare_comparison_data(
        [proposal],
        current_cpu=current_cpu,
        current_gpu=current_gpu,
        current_mobo=current_mobo,
        current_ram=current_ram,
        ssd_size=512,
        hdd_size=1000,
    )

    assert len(result) == 1
    comparison = result[0]
    assert comparison["total_price"] == 1234.57
    assert comparison["performance_gain"] > 10
    assert all(hasattr(p["new"], "type") for p in comparison["parts"])


@pytest.mark.unit
def test_prepare_comparison_data_filters_low_gain(monkeypatch):
    monkeypatch.setattr(
        performance, "find_similar_ssd", lambda size: DummySSD(size="512GB")
    )
    current_cpu = DummyCPU(benchmark=100)
    proposal = {
        "parts": [DummyCPU(benchmark=101)],
        "total_price": 100,
        "psu_warning": None,
    }

    result = performance.prepare_comparison_data(
        [proposal],
        current_cpu=current_cpu,
        current_gpu=DummyGPU(benchmark=200),
        current_mobo=DummyMobo(socket="AM4"),
        current_ram=DummyRAM(size="16 GB", clock=3200),
        ssd_size=256,
        hdd_size=500,
    )

    assert result == []
