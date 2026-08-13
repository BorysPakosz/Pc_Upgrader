import pytest
from types import SimpleNamespace

from hardware.utils import proposal_generation


@pytest.fixture(autouse=True)
def stub_helpers(monkeypatch):
    monkeypatch.setattr(
        proposal_generation, "check_psu_warning", lambda part, psu: None
    )
    monkeypatch.setattr(
        proposal_generation, "check_socket_compatibility", lambda a, b: True
    )
    monkeypatch.setattr(proposal_generation, "ram_fits_mobo", lambda ram, mobo: True)
    monkeypatch.setattr(
        proposal_generation,
        "get_psu_recommendation",
        lambda combo, current_cpu_tdp: {
            "recommended_psu": 500,
            "calculated_requirement": 400,
        },
    )
    monkeypatch.setattr(
        proposal_generation,
        "filter_motherboards_by_budget_tier",
        lambda mobos, budget: mobos,
    )
    monkeypatch.setattr(
        proposal_generation, "sort_motherboards_by_quality", lambda mobos: mobos
    )
    monkeypatch.setattr(
        proposal_generation, "prune_dominated_by_bench_price", lambda items: items
    )
    monkeypatch.setattr(proposal_generation, "sort_by_value", lambda items: items)


def make_part(cls_name, **kwargs):
    cls = type(cls_name, (), {})
    obj = cls()
    defaults = {
        "recomended_ps": None,
        "socket": "",
        "price": 0,
        "benchmark": 0,
        "id": 0,
        "size": "",
        "clock": 0,
        "name": "",
        "title": "",
        "model": "",
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


@pytest.mark.unit
def test_generate_proposals_produces_within_budget():
    cpu_current = make_part(
        "CPU", id=1, price=150, benchmark=100, socket="AM4", title="oldcpu"
    )
    gpu_current = make_part("GPU", id=2, price=200, benchmark=150, title="oldgpu")

    better_cpu = make_part(
        "CPU", id=3, price=200, benchmark=200, socket="AM5", title="newcpu"
    )
    better_gpu = make_part("GPU", id=4, price=300, benchmark=300, title="newgpu")
    better_ram = make_part(
        "RAM", id=5, price=120, benchmark=None, size="32 GB", clock=3600
    )
    better_mobo = make_part(
        "Motherboard", id=6, price=180, benchmark=None, socket="AM5", name="mobo"
    )

    proposals = proposal_generation.generate_proposals(
        better_cpus=[better_cpu],
        better_gpus=[better_gpu],
        better_rams=[better_ram],
        better_mobos=[better_mobo],
        better_ssds=[],
        better_hdds=[],
        budget=1000,
        psu_watt=650,
        ram_size=16,
        ram_clock=3200,
        current_cpu=cpu_current,
        current_mobo=make_part(
            "Motherboard", id=7, price=100, socket="AM4", name="oldmobo"
        ),
    )

    assert proposals
    assert all(p["total_price"] <= 1000 for p in proposals)
    assert all("psu_recommendation" in p for p in proposals)


@pytest.mark.unit
def test_select_top_proposals_prioritizes_weight_then_price():
    proposals = [
        {"priority_weight": 1.0, "total_price": 800, "parts": [make_part("CPU", id=1)]},
        {"priority_weight": 2.0, "total_price": 900, "parts": [make_part("CPU", id=2)]},
        {"priority_weight": 2.0, "total_price": 850, "parts": [make_part("CPU", id=3)]},
    ]

    selected = proposal_generation.select_top_proposals(proposals, max_proposals=2)

    assert len(selected) == 2
    assert selected[0]["priority_weight"] >= selected[1]["priority_weight"]


@pytest.mark.unit
def test_generate_proposals_skips_below_min_budget():
    cpu_current = make_part(
        "CPU", id=1, price=50, benchmark=50, socket="AM4", title="oldcpu"
    )
    gpu_current = make_part("GPU", id=2, price=50, benchmark=50, title="oldgpu")

    better_cpu = make_part(
        "CPU", id=3, price=100, benchmark=120, socket="AM5", title="newcpu"
    )
    better_gpu = make_part("GPU", id=4, price=120, benchmark=130, title="newgpu")
    better_ram = make_part(
        "RAM", id=5, price=40, benchmark=None, size="16 GB", clock=3200
    )
    better_mobo = make_part(
        "Motherboard", id=6, price=80, benchmark=None, socket="AM5", name="mobo"
    )

    proposals = proposal_generation.generate_proposals(
        better_cpus=[better_cpu],
        better_gpus=[better_gpu],
        better_rams=[better_ram],
        better_mobos=[better_mobo],
        better_ssds=[],
        better_hdds=[],
        budget=1000,  # min threshold 750
        psu_watt=650,
        ram_size=16,
        ram_clock=3200,
        current_cpu=cpu_current,
        current_mobo=make_part(
            "Motherboard", id=7, price=50, socket="AM4", name="oldmobo"
        ),
    )

    assert len(proposals) == 1
    assert proposals[0]["total_price"] == pytest.approx(120.0)


@pytest.mark.unit
def test_generate_proposals_single_gpu_branch():
    cpu_current = make_part(
        "CPU", id=1, price=100, benchmark=100, socket="AM4", title="oldcpu"
    )
    gpu_current = make_part("GPU", id=2, price=100, benchmark=100, title="oldgpu")

    better_gpu = make_part(
        "GPU", id=4, price=800, benchmark=300, title="newgpu", recomended_ps="650W"
    )

    proposals = proposal_generation.generate_proposals(
        better_cpus=[],
        better_gpus=[better_gpu],
        better_rams=[],
        better_mobos=[],
        better_ssds=[],
        better_hdds=[],
        budget=1200,
        psu_watt=700,
        ram_size=16,
        ram_clock=3200,
        current_cpu=cpu_current,
        current_mobo=make_part(
            "Motherboard", id=7, price=100, socket="AM4", name="oldmobo"
        ),
    )

    assert any(p.get("combo_type", "").startswith("gpu_single") for p in proposals)


@pytest.mark.unit
def test_generate_proposals_adds_cpu_single_same_socket():
    cpu_current = make_part(
        "CPU", id=1, price=100, benchmark=100, socket="AM4", title="oldcpu"
    )
    better_cpu = make_part(
        "CPU", id=2, price=150, benchmark=150, socket="AM4", title="newcpu"
    )

    proposals = proposal_generation.generate_proposals(
        better_cpus=[better_cpu],
        better_gpus=[],
        better_rams=[],
        better_mobos=[],
        better_ssds=[],
        better_hdds=[],
        budget=500,
        psu_watt=500,
        ram_size=16,
        ram_clock=3200,
        current_cpu=cpu_current,
        current_mobo=make_part(
            "Motherboard", id=3, price=100, socket="AM4", name="oldmobo"
        ),
    )

    assert any(p.get("combo_type") == "cpu_single" for p in proposals)


@pytest.mark.unit
def test_select_top_proposals_limits_and_sorts(monkeypatch):
    proposals = [
        {"priority_weight": 1.0, "total_price": 900, "budget_usage": 90, "parts": [make_part("CPU", id=1)]},
        {"priority_weight": 1.5, "total_price": 800, "budget_usage": 80, "psu_insufficient": True, "parts": [make_part("CPU", id=2)]},
        {"priority_weight": 2.0, "total_price": 700, "budget_usage": 85, "parts": [make_part("CPU", id=3)]},
    ]

    monkeypatch.setattr(proposal_generation, "smart_proposal_selection", lambda props, max_proposals: props[:2])

    selected = proposal_generation.select_top_proposals(proposals, max_proposals=2)

    assert len(selected) == 2
    assert selected[0]["priority_weight"] >= selected[1]["priority_weight"]


@pytest.mark.unit
def test_select_top_proposals_prefers_sufficient_psu(monkeypatch):
    ok = {"priority_weight": 1.0, "total_price": 800, "budget_usage": 90, "psu_insufficient": False, "parts": [make_part("CPU", id=1)]}
    low = {"priority_weight": 1.0, "total_price": 800, "budget_usage": 90, "psu_insufficient": True, "parts": [make_part("CPU", id=2)]}

    monkeypatch.setattr(proposal_generation, "smart_proposal_selection", lambda props, max_proposals: props)

    selected = proposal_generation.select_top_proposals([low, ok], max_proposals=2)

    assert selected[0]["psu_insufficient"] is False

@pytest.mark.unit
def test_sort_proposals_prefers_combo_priority(monkeypatch):
    cpu = make_part("CPU", id=1, price=200, benchmark=200, socket="AM4", title="c1")
    gpu = make_part("GPU", id=2, price=300, benchmark=300, title="g1")
    mobo = make_part("Motherboard", id=3, price=150, socket="AM4", name="m1")
    ram = make_part("RAM", id=4, price=80, size="16 GB", clock=3200)

    p1 = {
        "parts": [cpu, mobo],
        "total_price": 430,
        "priority_weight": 1.0,
        "combo_type": "cpu_mobo",
    }
    p2 = {
        "parts": [gpu],
        "total_price": 300,
        "priority_weight": 2.0,
        "combo_type": "gpu_single",
    }

    monkeypatch.setattr(
        proposal_generation, "calculate_performance_gain", lambda *a, **k: 10
    )

    sorted_props = proposal_generation.sort_proposals(
        [p1, p2],
        current_cpu=make_part("CPU", benchmark=100, socket="AM4"),
        current_gpu=make_part("GPU", benchmark=100),
        ram_size=16,
        ssd_size=512,
        hdd_size=0,
    )

    assert sorted_props[0]["combo_type"] == "cpu_mobo"


@pytest.mark.unit
def test_generate_proposals_respects_gpu_categories_by_psu(monkeypatch):
    # psu_watt=500 -> low_power + medium_power, brak high/extreme
    gpu_low = make_part("GPU", id=1, price=400, benchmark=200, recomended_ps="450W", title="low")
    gpu_mid = make_part("GPU", id=2, price=500, benchmark=250, recomended_ps="600W", title="mid")
    gpu_high = make_part("GPU", id=3, price=800, benchmark=300, recomended_ps="750W", title="high")

    proposals = proposal_generation.generate_proposals(
        better_cpus=[],
        better_gpus=[gpu_low, gpu_mid, gpu_high],
        better_rams=[],
        better_mobos=[],
        better_ssds=[],
        better_hdds=[],
        budget=1200,
        psu_watt=500,
        ram_size=16,
        ram_clock=3200,
        current_cpu=make_part("CPU", socket="AM4"),
        current_mobo=make_part("Motherboard", socket="AM4"),
    )

    combo_types = {p.get("combo_type") for p in proposals}
    assert any(ct and "gpu_single_low_power" in ct for ct in combo_types)
    assert any(ct and "gpu_single_medium_power" in ct for ct in combo_types)
    assert not any(ct and "gpu_single_high_power" in ct for ct in combo_types)


@pytest.mark.unit
def test_generate_proposals_enforces_min_budget_for_low_psu_branch():
    # psu_watt<500 -> enforce_min_budget=True, więc zbyt tania propozycja wypada
    gpu = make_part("GPU", id=1, price=400, benchmark=200, recomended_ps="450W", title="low")

    proposals = proposal_generation.generate_proposals(
        better_cpus=[],
        better_gpus=[gpu],
        better_rams=[],
        better_mobos=[],
        better_ssds=[],
        better_hdds=[],
        budget=1000,  # min threshold 750
        psu_watt=450,
        ram_size=16,
        ram_clock=3200,
        current_cpu=make_part("CPU", socket="AM4"),
        current_mobo=make_part("Motherboard", socket="AM4"),
    )

    assert proposals == []


@pytest.mark.unit
def test_generate_proposals_marks_psu_insufficient(monkeypatch):
    gpu = make_part("GPU", id=1, price=800, benchmark=300, recomended_ps="800W", title="hungry")
    cpu = make_part("CPU", id=2, price=200, benchmark=200, socket="AM4", title="cpu")
    mobo = make_part("Motherboard", id=3, price=150, socket="AM4", name="m1")
    ram = make_part("RAM", id=4, price=100, size="16 GB", clock=3200)

    monkeypatch.setattr(
        proposal_generation, "check_socket_compatibility", lambda a, b: True
    )
    monkeypatch.setattr(proposal_generation, "ram_fits_mobo", lambda a, b: True)
    monkeypatch.setattr(
        proposal_generation,
        "check_psu_warning",
        lambda part, psu: [{"type": "psu_insufficient"}],
    )

    proposals = proposal_generation.generate_proposals(
        better_cpus=[cpu],
        better_gpus=[gpu],
        better_rams=[ram],
        better_mobos=[mobo],
        better_ssds=[],
        better_hdds=[],
        budget=2000,
        psu_watt=500,  # za mało
        ram_size=8,
        ram_clock=2400,
        current_cpu=cpu,
        current_mobo=mobo,
    )

    assert any(p.get("psu_insufficient") for p in proposals)


@pytest.mark.unit
def test_generate_proposals_high_power_gpu_category():
    gpu_extreme = make_part("GPU", id=1, price=1200, benchmark=500, recomended_ps="850W", title="beast")

    proposals = proposal_generation.generate_proposals(
        better_cpus=[],
        better_gpus=[gpu_extreme],
        better_rams=[],
        better_mobos=[],
        better_ssds=[],
        better_hdds=[],
        budget=2000,
        psu_watt=800,  # powinno dopuścić extreme
        ram_size=16,
        ram_clock=3200,
        current_cpu=make_part("CPU", socket="AM4"),
        current_mobo=make_part("Motherboard", socket="AM4"),
    )

    # Powinno się pojawić, a PSU status może być tight/insufficient
    assert any(p.get("combo_type") == "gpu_single_extreme_power" for p in proposals)
