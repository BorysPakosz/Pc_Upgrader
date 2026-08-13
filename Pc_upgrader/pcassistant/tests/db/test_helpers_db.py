import pytest
from model_bakery import baker
from hardware.utils.helpers import find_similar_ssd, find_similar_hdd, parse_size


@pytest.mark.db
@pytest.mark.django_db
def test_find_similar_ssd_db_filters_by_size():
    # Jeśli size to CharField – używamy stringów:
    baker.make("hardware.SSD", size="256", price=149.99)
    baker.make("hardware.SSD", size="500", price=199.99)  # w środku zakresu
    baker.make("hardware.SSD", size="1000", price=299.99)

    res = find_similar_ssd(512)  # zakres 80–120% → 409–614
    assert res is not None
    size = parse_size(res.size)
    assert 409 <= size <= 614


@pytest.mark.db
@pytest.mark.django_db
def test_find_similar_hdd_db_fallback_to_any():
    # Brak dopasowania w zakresie → powinien zwrócić jakikolwiek z ceną
    baker.make("hardware.HDD", size="1000", price=199.99)
    res = find_similar_hdd(2000)
    assert res is not None
    assert res.price is not None


@pytest.mark.db
@pytest.mark.django_db
def test_find_similar_returns_none_for_non_positive():
    assert find_similar_hdd(0) is None
    assert find_similar_ssd(-5) is None


@pytest.mark.db
@pytest.mark.django_db
def test_find_similar_hdd_db_returns_similar_in_range():
    # tylko 2000 GB pasuje do zakresu 80–120% z 2000 (czyli 1600–2400)
    baker.make("hardware.HDD", size="1000", price=149.99)
    target = baker.make("hardware.HDD", size="2000", price=199.99)  # jedyny w zakresie
    baker.make("hardware.HDD", size="3000", price=299.99)

    res = find_similar_hdd(2000)
    assert res is not None
    assert parse_size(res.size) == 2000
    # opcjonalnie: upewnij się, że to dokładnie 'target'
    assert res.pk == target.pk


@pytest.mark.db
@pytest.mark.django_db
def test_find_similar_ssd_returns_none_on_type_error():
    # "abc" * 0.8 → TypeError → except → None
    assert find_similar_ssd("abc") is None


@pytest.mark.db
@pytest.mark.django_db
def test_find_similar_hdd_returns_none_on_type_error():
    # "abc" * 0.8 → TypeError → except → None
    assert find_similar_hdd("abc") is None
