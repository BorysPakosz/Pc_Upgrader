import pytest
from types import SimpleNamespace

from hardware.utils import filtering


def make_proposal(combo_type, parts, total_price, priority_weight):
    return {
        "combo_type": combo_type,
        "parts": parts,
        "total_price": total_price,
        "priority_weight": priority_weight,
    }


def make_mobo(**kwargs):
    data = {"chipset": "", "price": 0, "name": "", "socket": ""}
    data.update(kwargs)
    return SimpleNamespace(**data)


@pytest.mark.unit
def test_filter_motherboards_by_budget_tier_limits_price_and_tier():
    mobos = [
        make_mobo(chipset="B660", price=1400),
        make_mobo(chipset="B550", price=2000),
        make_mobo(chipset="H410", price=500),
    ]

    allowed = filtering.filter_motherboards_by_budget_tier(mobos, budget="6000")

    assert allowed == [mobos[0]]


@pytest.mark.unit
def test_get_motherboard_score_adds_wifi_and_socket_bonus():
    mobo = make_mobo(chipset="B660", price=1000, name="Tomahawk WiFi", socket="1700")

    score = filtering.get_motherboard_score(mobo)

    assert score == pytest.approx(8.58, rel=1e-3)


@pytest.mark.unit
def test_get_motherboard_score_returns_zero_for_missing_price():
    mobo = make_mobo(chipset="B660", price=None)
    assert filtering.get_motherboard_score(mobo) == 0


@pytest.mark.unit
def test_sort_motherboards_by_quality_prefers_higher_score_then_price():
    high = make_mobo(chipset="B660", price=1000, socket="1700")
    low = make_mobo(chipset="B450", price=600, socket="AM4")

    ordered = filtering.sort_motherboards_by_quality([high, low])

    assert ordered == [low, high]


@pytest.mark.unit
def test_deduplicate_similar_proposals_swaps_in_better_option():
    combo_best = [
        SimpleNamespace(price=3200, benchmark=200),
        SimpleNamespace(price=2000, benchmark=500),
    ]
    combo_ok = [
        SimpleNamespace(price=3200, benchmark=200),
        SimpleNamespace(price=1800, benchmark=500),
    ]
    combo_other = [SimpleNamespace(price=1200, benchmark=400)]

    proposal_best = make_proposal(
        "full_upgrade", combo_best, total_price=5200, priority_weight=20
    )
    proposal_ok = make_proposal(
        "full_upgrade", combo_ok, total_price=3500, priority_weight=18
    )
    proposal_other = make_proposal(
        "gpu_single_low_power", combo_other, total_price=1200, priority_weight=5
    )

    deduped = filtering.deduplicate_similar_proposals(
        [proposal_best, proposal_ok, proposal_other]
    )

    assert proposal_best not in deduped
    assert proposal_ok in deduped
    assert proposal_other in deduped


@pytest.mark.unit
def test_add_price_diversity_filter_keeps_distance_only_within_type():
    proposals = [
        make_proposal(
            "full_upgrade", [SimpleNamespace(price=1000, benchmark=200)], 1000, 10
        ),
        make_proposal(
            "full_upgrade", [SimpleNamespace(price=1100, benchmark=210)], 1050, 9
        ),
        make_proposal(
            "full_upgrade", [SimpleNamespace(price=1500, benchmark=220)], 1200, 8
        ),
        make_proposal(
            "gpu_single", [SimpleNamespace(price=800, benchmark=300)], 1010, 7
        ),
        make_proposal(
            "gpu_single", [SimpleNamespace(price=850, benchmark=310)], 1110, 6
        ),
    ]

    filtered = filtering.add_price_diversity_filter(proposals, min_price_gap=100)

    assert proposals[0] in filtered
    assert proposals[1] not in filtered
    assert proposals[2] in filtered
    assert proposals[3] in filtered and proposals[4] in filtered


@pytest.mark.unit
def test_prune_dominated_by_bench_price_drops_only_weaker_duplicates():
    weaker = SimpleNamespace(price=1000, benchmark=400)
    stronger = SimpleNamespace(price=900, benchmark=420)
    unknown = SimpleNamespace(price=None, benchmark=None)

    kept = filtering.prune_dominated_by_bench_price([weaker, stronger, unknown])

    assert stronger in kept
    assert weaker not in kept
    assert unknown in kept


@pytest.mark.unit
def test_sort_by_value_uses_value_then_bench_then_price():
    parts = [
        SimpleNamespace(name="mid", price=180, benchmark=90),
        SimpleNamespace(name="low", price=200, benchmark=80),
        SimpleNamespace(name="top", price=200, benchmark=100),
    ]

    ordered = filtering.sort_by_value(parts)

    assert [p.name for p in ordered] == ["top", "mid", "low"]


@pytest.mark.unit
def test_calculate_ram_score_combines_gains_and_penalties():
    mobo = SimpleNamespace(ram_slots=4)
    ram_upgrade = SimpleNamespace(
        size="32 GB", clock=5200, price=400, ram_type="DDR5", sticks=2
    )

    score = filtering.calculate_ram_score(
        ram_upgrade, mobo, current_gb=16, current_speed=3200
    )
    assert score == pytest.approx(45.3125, rel=1e-3)

    ram_over_slots = SimpleNamespace(
        size="16 GB", clock=3200, price=400, sticks=8, ram_type="DDR4"
    )
    penalty = filtering.calculate_ram_score(
        ram_over_slots, mobo, current_gb=16, current_speed=3200
    )
    assert penalty < score


@pytest.mark.unit
def test_smart_ram_filtering_checks_budget_compatibility_and_upgrade(monkeypatch):
    monkeypatch.setattr(
        filtering, "ram_fits_mobo", lambda ram, mobo: getattr(ram, "fits", True)
    )

    mobo = SimpleNamespace(
        name="Board",
        ram_slots=4,
        memory_capacity="128 GB",
        memory_type="DDR4",
        max_memory_speed=4000,
    )

    ram_ok = SimpleNamespace(
        size="32 GB", clock=3600, price=450, ram_type="DDR4", sticks=2, label="good"
    )
    ram_pricey = SimpleNamespace(
        size="32 GB", clock=3600, price=900, ram_type="DDR4", sticks=2, label="exp"
    )
    ram_bad = SimpleNamespace(
        size="64 GB",
        clock=3600,
        price=400,
        ram_type="DDR4",
        sticks=2,
        label="bad",
        fits=False,
    )
    ram_ddr5 = SimpleNamespace(
        size="16 GB", clock=5200, price=500, ram_type="DDR5", sticks=2, label="ddr5"
    )

    result = filtering.smart_ram_filtering(
        [ram_ok, ram_pricey, ram_bad, ram_ddr5],
        mobo,
        current_ram_gb=16,
        current_ram_speed=3200,
        budget=4000,
    )

    assert [ram.label for ram in result] == ["good", "ddr5"]
    assert hasattr(result[0], "compatibility_score")
