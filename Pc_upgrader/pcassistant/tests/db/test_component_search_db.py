import pytest
from model_bakery import baker

from hardware.utils import component_search


@pytest.mark.db
@pytest.mark.django_db
def test_find_current_components_returns_all_and_sets_cpu_socket_from_mobo():
    cpu = baker.make(
        "hardware.CPU",
        title="Ryzen 5 5600X",
        model="Ryzen 5 5600X",
        socket="",
        benchmark=100,
    )
    gpu = baker.make("hardware.GPU", title="RTX 3060")
    mobo = baker.make("hardware.Motherboard", name="B550 TOMAHAWK", socket="AM4")
    ram = baker.make("hardware.RAM", name="Corsair 16GB", size="16 GB", clock=3200)

    res_cpu, res_gpu, res_mobo, res_ram = component_search.find_current_components(
        cpu_name="Ryzen 5 5600X",
        gpu_name="RTX 3060",
        mobo_name="B550",
        ram_name="Corsair 16GB",
    )

    assert res_cpu == cpu
    assert res_cpu.socket == "AM4"  # zapożyczony z płyty
    assert res_gpu == gpu
    assert res_mobo == mobo
    assert res_ram == ram


@pytest.mark.db
@pytest.mark.django_db
def test_find_current_components_returns_none_if_cpu_missing():
    res = component_search.find_current_components("", "any", "any", "any")
    assert res == (None, None, None, None)


@pytest.mark.db
@pytest.mark.django_db
def test_find_current_components_stops_when_gpu_missing():
    baker.make("hardware.CPU", title="Ryzen 5 5600X", model="Ryzen 5 5600X")
    baker.make("hardware.Motherboard", name="B550 TOMAHAWK")

    res = component_search.find_current_components(
        cpu_name="Ryzen 5 5600X", gpu_name="NON_EXIST", mobo_name="B550", ram_name=""
    )

    assert res == (None, None, None, None)
