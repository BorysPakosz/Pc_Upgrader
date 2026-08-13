import pytest
from types import SimpleNamespace

from hardware.utils import component_search


@pytest.mark.unit
@pytest.mark.parametrize(
    "title,expected",
    [
        ("Intel Core i5-12600K", "1700"),
        ("Intel Core i7-10700F", "1200"),
        ("Intel Core i5-9600K", "1151"),
        ("Ryzen 5 5600X", "AM4"),
        ("Ryzen 9 7900X", "AM5"),
        ("Unknown Model", None),
    ],
)
def test_get_default_socket_for_cpu_maps_known_models(title, expected):
    assert component_search.get_default_socket_for_cpu(title) == expected


@pytest.mark.unit
def test_get_socket_variants_returns_common_forms():
    variants = component_search.get_socket_variants("1200")
    assert "1200" in variants
    assert "Socket 1200" in variants
    assert "LGA1200" in variants
    assert "LGA 1200" in variants


@pytest.mark.unit
def test_find_current_components_fills_default_socket(monkeypatch):
    class Manager(list):
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return self[0] if self else None

        def none(self):
            return Manager()

    cpu = HashableNS(title="Intel Core i5-12600K", model="i5-12600K", socket="")
    gpu = HashableNS(title="RTX 3060")
    mobo = HashableNS(name="Z690 Board", socket="")

    monkeypatch.setattr(
        component_search, "CPU", type("CPU", (), {"objects": Manager([cpu])})
    )
    monkeypatch.setattr(
        component_search, "GPU", type("GPU", (), {"objects": Manager([gpu])})
    )
    monkeypatch.setattr(
        component_search,
        "Motherboard",
        type("Motherboard", (), {"objects": Manager([mobo])}),
    )
    monkeypatch.setattr(component_search, "RAM", type("RAM", (), {"objects": Manager()}))

    res_cpu, res_gpu, res_mobo, res_ram = component_search.find_current_components(
        cpu_name=cpu.title, gpu_name=gpu.title, mobo_name="Z690", ram_name=""
    )

    assert res_cpu.socket == "1700"  # domyślny socket dla 12. gen Intela


@pytest.mark.unit
def test_get_better_components_ignores_storage_parse_errors(monkeypatch):
    class DummyManager(list):
        def filter(self, *args, **kwargs):
            return self

        def exclude(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def exists(self):
            return bool(self)

    class BadSize:
        price = 100

        @property
        def size(self):
            raise ValueError("bad size")

    dummy_cpu = HashableNS(socket="AM4", benchmark=100, price=100, title="cpu")
    dummy_gpu = HashableNS(benchmark=100, price=200, model="gpu")
    dummy_mobo = HashableNS(
        socket="AM4",
        name="board",
        memory_type="DDR4",
        memory_capacity="16 GB",
        ram_slots=2,
        price=150,
    )
    dummy_ram = HashableNS(size="8 GB", clock=2400)

    monkeypatch.setattr(
        component_search, "CPU", type("CPU", (), {"objects": DummyManager([dummy_cpu])})
    )
    monkeypatch.setattr(
        component_search, "GPU", type("GPU", (), {"objects": DummyManager([dummy_gpu])})
    )
    monkeypatch.setattr(
        component_search,
        "Motherboard",
        type("Motherboard", (), {"objects": DummyManager([dummy_mobo])}),
    )
    monkeypatch.setattr(
        component_search, "RAM", type("RAM", (), {"objects": DummyManager([dummy_ram])})
    )
    monkeypatch.setattr(
        component_search, "SSD", type("SSD", (), {"objects": DummyManager([BadSize()])})
    )
    monkeypatch.setattr(
        component_search, "HDD", type("HDD", (), {"objects": DummyManager([BadSize()])})
    )

    result = component_search.get_better_components(
        current_cpu=dummy_cpu,
        current_gpu=dummy_gpu,
        current_mobo=dummy_mobo,
        current_ram=dummy_ram,
        ssd_size=512,
        hdd_size=1024,
        budget=5000,
    )

    _, _, _, _, better_ssds, better_hdds = result

    assert better_ssds == []
    assert better_hdds == []


class HashableNS(SimpleNamespace):
    def __hash__(self):
        return id(self)


class DummyManager(list):
    def filter(self, *args, **kwargs):
        return DummyManager(self)

    def exclude(self, *args, **kwargs):
        return DummyManager(self)

    def order_by(self, *args, **kwargs):
        return DummyManager(self)

    def first(self):
        return self[0] if self else None

    def exists(self):
        return bool(self)


@pytest.mark.unit
def test_get_better_components_returns_empty_if_no_sockets(monkeypatch):
    monkeypatch.setattr(component_search, "CPU", HashableNS)
    monkeypatch.setattr(component_search, "GPU", HashableNS)
    monkeypatch.setattr(component_search, "RAM", HashableNS)
    monkeypatch.setattr(component_search, "Motherboard", HashableNS)
    monkeypatch.setattr(component_search, "SSD", HashableNS)
    monkeypatch.setattr(component_search, "HDD", HashableNS)

    current_cpu = HashableNS(socket="", benchmark=0, title="cpu")
    current_gpu = HashableNS(benchmark=0)
    current_mobo = HashableNS(socket="", name="")
    current_ram = HashableNS(size="16 GB", clock=3200)

    result = component_search.get_better_components(
        current_cpu,
        current_gpu,
        current_mobo,
        current_ram,
        ssd_size=512,
        hdd_size=0,
        budget=1000,
    )

    assert result == ([], [], [], [], [], [])


@pytest.mark.unit
def test_get_better_components_collects_candidates(monkeypatch):
    monkeypatch.setattr(
        component_search, "smart_ram_filtering", lambda r, m, *a, **k: r[:1]
    )

    cpu_candidates = DummyManager(
        [
            HashableNS(id=1, price=200, benchmark=200, socket="AM4", model="cpu1"),
        ]
    )
    gpu_candidates = DummyManager(
        [
            HashableNS(id=2, price=250, benchmark=220, model="gpu1"),
        ]
    )
    mobo_candidates = DummyManager(
        [
            HashableNS(
                id=3,
                price=150,
                benchmark=None,
                socket="AM4",
                name="am4 board",
                memory_type="DDR4",
                memory_capacity="64 GB",
                ram_slots=4,
            )
        ]
    )
    ram_candidates = DummyManager(
        [
            HashableNS(
                id=4,
                price=80,
                benchmark=None,
                ram_type="DDR4",
                size="32 GB",
                clock=3600,
                sticks=2,
            )
        ]
    )
    ssd_candidates = DummyManager(
        [HashableNS(id=5, price=100, benchmark=None, size="1024")]
    )
    hdd_candidates = DummyManager(
        [HashableNS(id=6, price=80, benchmark=None, size="2000")]
    )

    monkeypatch.setattr(
        component_search, "CPU", type("CPU", (), {"objects": cpu_candidates})
    )
    monkeypatch.setattr(
        component_search, "GPU", type("GPU", (), {"objects": gpu_candidates})
    )
    monkeypatch.setattr(
        component_search,
        "Motherboard",
        type("Motherboard", (), {"objects": mobo_candidates}),
    )
    monkeypatch.setattr(
        component_search, "RAM", type("RAM", (), {"objects": ram_candidates})
    )
    monkeypatch.setattr(
        component_search, "SSD", type("SSD", (), {"objects": ssd_candidates})
    )
    monkeypatch.setattr(
        component_search, "HDD", type("HDD", (), {"objects": hdd_candidates})
    )

    current_cpu = HashableNS(socket="AM4", benchmark=150, title="oldcpu")
    current_gpu = HashableNS(benchmark=150, model="oldgpu")
    current_mobo = HashableNS(socket="AM4", name="board", memory_type="DDR4")
    current_ram = HashableNS(size="16 GB", clock=3200)

    better = component_search.get_better_components(
        current_cpu,
        current_gpu,
        current_mobo,
        current_ram,
        ssd_size=512,
        hdd_size=1000,
        budget=1000,
    )

    better_cpus, better_gpus, better_rams, better_mobos, better_ssds, better_hdds = (
        better
    )
    assert (
        better_cpus
        and better_gpus
        and better_rams
        and better_mobos
        and better_ssds
        and better_hdds
    )
