import pytest
from types import SimpleNamespace

from hardware.utils import compatibility


def make_mobo(**kwargs):
    data = {
        "memory_capacity": "32 GB",
        "ram_slots": 2,
        "memory_type": "DDR4",
        "socket": "AM4",
        "max_memory_speed": 3200,
    }
    data.update(kwargs)
    return SimpleNamespace(**data)


def make_ram(**kwargs):
    data = {
        "size": "16 GB",
        "sticks": 2,
        "ram_type": "DDR4",
        "clock": 3200,
    }
    data.update(kwargs)
    return SimpleNamespace(**data)


@pytest.mark.unit
def test_check_socket_compatibility_matches_identical():
    assert compatibility.check_socket_compatibility("LGA1700", " LGA1700 ") is True
    assert compatibility.check_socket_compatibility("am4", "AM4") is True


@pytest.mark.unit
def test_check_socket_compatibility_rejects_cross_platform():
    assert compatibility.check_socket_compatibility("AM4", "1700") is False
    assert compatibility.check_socket_compatibility("1151", "AM5") is False


@pytest.mark.unit
def test_check_socket_compatibility_allows_missing_data():
    assert compatibility.check_socket_compatibility("", None) is True


@pytest.mark.unit
def test_ram_fits_mobo_fails_when_exceeding_capacity():
    mobo = make_mobo(memory_capacity="32 GB")
    ram = make_ram(size="64 GB", sticks=2)
    assert compatibility.ram_fits_mobo(ram, mobo) is False


@pytest.mark.unit
def test_ram_fits_mobo_fails_on_too_many_sticks():
    mobo = make_mobo(memory_capacity="64 GB", ram_slots=2)
    ram = make_ram(size="32 GB", sticks=4)
    assert compatibility.ram_fits_mobo(ram, mobo) is False


@pytest.mark.unit
def test_ram_fits_mobo_fails_when_single_stick_over_slot_limit():
    mobo = make_mobo(memory_capacity="32 GB", ram_slots=2)
    ram = make_ram(size="96 GB", sticks=2)  # 48 GB per stick > 16 GB per slot
    assert compatibility.ram_fits_mobo(ram, mobo) is False


@pytest.mark.unit
def test_ram_fits_mobo_rejects_mismatched_ddr_type():
    mobo = make_mobo(memory_type="DDR4")
    ram = make_ram(ram_type="DDR5")
    assert compatibility.ram_fits_mobo(ram, mobo) is False


@pytest.mark.unit
def test_ram_fits_mobo_warns_but_allows_speed_over_max():
    mobo = make_mobo(memory_capacity="64 GB", ram_slots=4, max_memory_speed=3200)
    ram = make_ram(clock=4000, size="32 GB", sticks=2)
    assert compatibility.ram_fits_mobo(ram, mobo) is True


class DummyGPU:
    def __init__(self, recomended_ps=None, model="GPU"):
        self.recomended_ps = recomended_ps
        self.model = model


class DummyCPU:
    def __init__(self, benchmark=None):
        self.benchmark = benchmark


def psu_for_combo(combo, current_cpu_tdp=65):
    return compatibility.calculate_total_psu_requirement(combo, current_cpu_tdp)


@pytest.mark.unit
def test_check_psu_warning_detects_insufficient_and_tight(monkeypatch):
    monkeypatch.setattr(compatibility, "GPU", DummyGPU)
    gpu = DummyGPU(recomended_ps="500W", model="Test GPU")

    warn_low = compatibility.check_psu_warning(gpu, psu_watt=400)
    warn_tight = compatibility.check_psu_warning(gpu, psu_watt=550)

    assert warn_low and warn_low[0]["type"] == "psu_insufficient"
    assert warn_tight and warn_tight[0]["type"] == "psu_tight"


@pytest.mark.unit
def test_check_psu_warning_returns_none_for_non_gpu(monkeypatch):
    monkeypatch.setattr(compatibility, "GPU", DummyGPU)

    class NotGpu:
        pass

    assert compatibility.check_psu_warning(NotGpu(), psu_watt=500) is None


@pytest.mark.unit
def test_calculate_total_psu_requirement_uses_benchmark_and_gpu(monkeypatch):
    monkeypatch.setattr(compatibility, "CPU", DummyCPU)
    monkeypatch.setattr(compatibility, "GPU", DummyGPU)

    combo = [DummyCPU(benchmark=100), DummyGPU(recomended_ps="600W")]
    total = psu_for_combo(combo, current_cpu_tdp=65)

    # base 100 + cpu(max 80) + gpu(~390) *1.15 ≈ 655
    assert total > 600


@pytest.mark.unit
def test_calculate_total_psu_requirement_handles_missing_recommended(monkeypatch):
    monkeypatch.setattr(compatibility, "CPU", DummyCPU)
    monkeypatch.setattr(compatibility, "GPU", DummyGPU)

    total = psu_for_combo([DummyGPU(recomended_ps=None)], current_cpu_tdp=95)
    assert total > 100  # base + cpu


@pytest.mark.unit
def test_get_psu_recommendation_rounded_to_standard_size(monkeypatch):
    monkeypatch.setattr(compatibility, "CPU", DummyCPU)
    monkeypatch.setattr(compatibility, "GPU", DummyGPU)

    combo = [DummyCPU(benchmark=150), DummyGPU(recomended_ps="900W")]
    rec = compatibility.get_psu_recommendation(combo, current_cpu_tdp=95)

    assert rec["recommended_psu"] in [1000, 1200]
    assert rec["recommended_psu"] >= rec["calculated_requirement"]


@pytest.mark.unit
def test_ram_fits_mobo_returns_true_on_exception(monkeypatch):
    class BadRam:
        def __init__(self):
            self.size = object()  # parse_gb will raise
            self.ram_type = None
            self.clock = None

    mobo = make_mobo(memory_capacity="32 GB")
    assert compatibility.ram_fits_mobo(BadRam(), mobo) is True


@pytest.mark.unit
def test_check_socket_compatibility_returns_false_for_different_same_family():
    assert compatibility.check_socket_compatibility("1151", "1150") is False


@pytest.mark.unit
def test_check_psu_warning_ignores_nonnumeric_recommendation(monkeypatch):
    monkeypatch.setattr(compatibility, "GPU", DummyGPU)
    gpu = DummyGPU(recomended_ps="N/A", model="Test GPU")
    assert compatibility.check_psu_warning(gpu, psu_watt=500) is None


@pytest.mark.unit
def test_check_psu_warning_handles_value_error_in_str(monkeypatch):
    class BadStr:
        def __str__(self):
            raise ValueError("boom")

    monkeypatch.setattr(compatibility, "GPU", DummyGPU)
    gpu = DummyGPU(recomended_ps=BadStr(), model="Test GPU")

    # Nie powinno rzucać, brak ostrzeżeń
    assert compatibility.check_psu_warning(gpu, psu_watt=500) is None


@pytest.mark.unit
def test_ram_fits_mobo_allows_high_clock_with_warning(capsys):
    mobo = make_mobo(memory_capacity="32 GB", ram_slots=4, max_memory_speed=2400)
    ram = make_ram(size="16 GB", sticks=2, clock=4000)

    assert compatibility.ram_fits_mobo(ram, mobo) is True
    out, _ = capsys.readouterr()
    assert "za szybki" in out


@pytest.mark.unit
def test_ram_fits_mobo_returns_true_on_missing_attribute():
    class NoSize:
        pass

    mobo = make_mobo(memory_capacity="32 GB")
    assert compatibility.ram_fits_mobo(NoSize(), mobo) is True


class DummyQS(list):
    def exists(self):
        return bool(self)


@pytest.mark.unit
def test_get_compatible_motherboards_fallbacks_case_insensitive(monkeypatch):
    class Manager:
        def filter(self, **kwargs):
            if "socket__iexact" in kwargs:
                return DummyQS()
            if "socket__icontains" in kwargs:
                return DummyQS([SimpleNamespace(socket="am4")])

    monkeypatch.setattr(
        compatibility, "Motherboard", type("Motherboard", (), {"objects": Manager()})
    )

    res = compatibility.get_compatible_motherboards(" am4 ")
    assert isinstance(res, DummyQS)
    assert res and res[0].socket == "am4"


@pytest.mark.unit
def test_get_compatible_motherboards_handles_empty(monkeypatch):
    class Manager:
        def none(self):
            return "EMPTY"

    monkeypatch.setattr(
        compatibility, "Motherboard", type("Motherboard", (), {"objects": Manager()})
    )

    assert compatibility.get_compatible_motherboards("") == "EMPTY"


@pytest.mark.unit
def test_get_compatible_cpus_case_insensitive(monkeypatch):
    class Manager:
        def filter(self, **kwargs):
            if "socket__iexact" in kwargs:
                return DummyQS()
            if "socket__icontains" in kwargs:
                return DummyQS([SimpleNamespace(socket="AM5")])

    monkeypatch.setattr(
        compatibility, "CPU", type("CPU", (), {"objects": Manager()})
    )

    res = compatibility.get_compatible_cpus(" am5 ")
    assert isinstance(res, DummyQS)
    assert res and res[0].socket == "AM5"


@pytest.mark.unit
def test_get_compatible_cpus_handles_empty(monkeypatch):
    class Manager:
        def none(self):
            return "NONE"

    monkeypatch.setattr(
        compatibility, "CPU", type("CPU", (), {"objects": Manager()})
    )

    assert compatibility.get_compatible_cpus(None) == "NONE"


@pytest.mark.unit
def test_get_psu_recommendation_scales_with_high_gpu(monkeypatch):
    monkeypatch.setattr(compatibility, "GPU", DummyGPU)
    gpu = DummyGPU(recomended_ps="950W")

    rec = compatibility.get_psu_recommendation([gpu], current_cpu_tdp=95)

    # Powinno dobrać standardowy rozmiar >= wyliczonego wymagania
    assert rec["recommended_psu"] >= rec["calculated_requirement"]


@pytest.mark.unit
def test_get_psu_recommendation_fallback_to_max(monkeypatch):
    monkeypatch.setattr(compatibility, "GPU", DummyGPU)
    gpu = DummyGPU(recomended_ps="3000W")

    rec = compatibility.get_psu_recommendation([gpu], current_cpu_tdp=95)

    assert rec["recommended_psu"] == 1200


@pytest.mark.unit
def test_ram_fits_mobo_prints_per_slot_limit(capsys):
    mobo = make_mobo(memory_capacity="32 GB", ram_slots=2)
    ram = make_ram(size="96 GB", sticks=2)  # 48 GB per stick > 16 GB per slot

    assert compatibility.ram_fits_mobo(ram, mobo) is False
    out, _ = capsys.readouterr()
    assert "limit płyty" in out or "limit na slot" in out


@pytest.mark.unit
def test_calculate_total_psu_requirement_handles_bad_recommended(monkeypatch):
    class BadStr:
        def __str__(self):
            raise ValueError("bad")

    monkeypatch.setattr(compatibility, "GPU", DummyGPU)
    bad_gpu = DummyGPU(recomended_ps=BadStr())
    total = compatibility.calculate_total_psu_requirement([bad_gpu], current_cpu_tdp=95)
    assert total >= 100  # co najmniej bazowy pobór
