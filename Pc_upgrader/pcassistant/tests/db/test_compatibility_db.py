import pytest
from model_bakery import baker

from hardware.utils import compatibility


@pytest.mark.db
@pytest.mark.django_db
def test_get_compatible_motherboards_prefers_exact_then_normalized():
    exact = baker.make("hardware.Motherboard", socket="AM4")
    normalized = baker.make("hardware.Motherboard", socket="am4")

    res_exact = compatibility.get_compatible_motherboards("AM4")
    assert exact in res_exact

    res_norm = compatibility.get_compatible_motherboards(" am4 ")
    assert normalized in res_norm


@pytest.mark.db
@pytest.mark.django_db
def test_get_compatible_cpus_prefers_normalized_when_exact_missing():
    normalized_cpu = baker.make("hardware.CPU", socket="AM5")

    res = compatibility.get_compatible_cpus(" AM5 ")
    assert normalized_cpu in res
