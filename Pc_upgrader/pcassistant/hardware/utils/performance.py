from .helpers import (
    _price,
    _bench,
    parse_size,
    parse_gb,
    find_similar_hdd,
    find_similar_ssd,
)
from ..models import CPU, GPU, RAM, SSD, HDD, Motherboard


def value_score(part):
    p = _price(part)
    b = _bench(part)
    if p and p != float("inf") and b and b > 0:
        return b / p
    return 0.0


def calculate_performance_gain(
    part, current_cpu, current_gpu, ram_size, ssd_size, hdd_size
):
    """Oblicza przyrost wydajności dla danej części"""
    if isinstance(part, CPU) and current_cpu.benchmark:
        return (part.benchmark - current_cpu.benchmark) / current_cpu.benchmark
    elif isinstance(part, GPU) and current_gpu.benchmark:
        return (part.benchmark - current_gpu.benchmark) / current_gpu.benchmark
    elif isinstance(part, RAM):
        try:
            part_size = parse_size(part.size)
            if ram_size > 0 and part_size > ram_size:
                return (part_size - ram_size) / ram_size
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    elif isinstance(part, SSD):
        try:
            part_size = parse_size(part.size)
            if ssd_size > 0 and part_size > ssd_size:
                return (part_size - ssd_size) / ssd_size
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    elif isinstance(part, HDD):
        try:
            part_size = parse_size(part.size)
            if hdd_size > 0 and part_size > hdd_size:
                return (part_size - hdd_size) / hdd_size
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    return 0


def get_chipset_tier(chipset):
    """Zwraca tier chipsetu na podstawie rzeczywistych danych z bazy (wyższy = lepszy)"""
    if not chipset:
        return 0

    chipset_upper = chipset.upper()

    # Intel chipsety (na podstawie Twojej analizy)
    intel_tiers = {
        # Z-series (enthusiast/gaming) - najlepsze
        "Z790": 10,
        "Z690": 10,
        "Z590": 9,
        "Z490": 9,
        "Z390": 8,
        "Z370": 8,
        "Z270": 8,
        "Z170": 7,
        # X-series (HEDT) - wysokiej klasy
        "X299": 9,
        "X99": 7,
        # B-series (mainstream) - średnia klasa
        "B760": 7,
        "B660": 6,
        "B560": 5,
        "B460": 4,
        "B360": 4,
        "B250": 3,
        "B150": 3,
        "B85": 2,
        # H-series (budget) - podstawowe
        "H770": 5,
        "H670": 4,
        "H570": 4,
        "H470": 3,
        "H370": 3,
        "H310": 2,
        "H270": 2,
        "H110": 2,
        "H610": 2,
        "H510": 2,
        "H410": 1,
        "H81": 1,
        "H97": 2,
        "H61": 1,
        # Workstation
        "C236": 6,
        "C232": 5,
        "C612": 7,
        "C222": 3,
        "C246": 6,
        "W480": 5,
        # Starsze
        "Z97": 4,
        "Z87": 3,
        "Q170": 3,
        "Q270": 2,
        "Q87": 2,
    }

    # AMD chipsety (na podstawie Twojej analizy)
    amd_tiers = {
        # X-series (enthusiast) - najlepsze
        "X670E": 10,
        "X670": 9,
        "X570S": 8,
        "X570": 8,
        "X470": 6,
        "X370": 6,
        "X399": 9,
        "X99": 7,
        # B-series (mainstream) - średnia klasa
        "B650E": 7,
        "B650": 6,
        "B550": 6,
        "B450": 5,
        "B350": 4,
        # A-series (budget) - podstawowe
        "A520": 3,
        "A320": 2,
        # Starsze chipsety
        "990FX": 4,
        "990X": 3,
        "970": 3,
        "760G": 2,
        # Workstation/HEDT
        "TRX40": 10,
        "WRX80": 10,
        # APU/integrowane
        "A88X": 2,
        "A68H": 1,
        "A58": 1,
        "A50": 1,
    }

    # Sprawdź Intel
    for chipset_name, tier in intel_tiers.items():
        if chipset_name in chipset_upper:
            return tier

    # Sprawdź AMD
    for chipset_name, tier in amd_tiers.items():
        if chipset_name in chipset_upper:
            return tier

    # Fallback dla nieznanych chipsetów
    return 1


def prepare_comparison_data(
    proposals, current_cpu, current_gpu, current_mobo, current_ram, ssd_size, hdd_size
):
    """Przygotowuje dane do porównania z lepszą logiką dla płyt głównych"""

    comparison_data = []

    for proposal in proposals:
        comparison = {
            "parts": [],
            "total_price": round(proposal["total_price"], 2),
            "psu_warning": proposal.get("psu_warning"),
            "performance_gain": 0,
        }

        total_gain = 0

        for part in proposal["parts"]:
            current_part = None
            gain = 0

            if isinstance(part, CPU):
                current_part = current_cpu
                if current_cpu.benchmark and part.benchmark:
                    gain = (
                        (part.benchmark - current_cpu.benchmark)
                        / current_cpu.benchmark
                        * 100
                    )

            elif isinstance(part, GPU):
                current_part = current_gpu
                if current_gpu.benchmark and part.benchmark:
                    gain = (
                        (part.benchmark - current_gpu.benchmark)
                        / current_gpu.benchmark
                        * 100
                    )

            if isinstance(part, RAM):

                current_part = current_ram

                try:

                    part_size = parse_gb(part.size)

                    current_size = parse_gb(current_ram.size) if current_ram else 16

                    current_clock = current_ram.clock if current_ram else 3200

                    if current_size > 0 and part_size:
                        size_gain = (
                            (part_size - current_size) / current_size * 100
                            if part_size > current_size
                            else 0
                        )

                        freq_gain = (
                            (part.clock - current_clock) / current_clock * 100
                            if part.clock > current_clock
                            else 0
                        )

                        gain = max(size_gain, freq_gain)

                except (ValueError, TypeError, ZeroDivisionError):

                    gain = 0

            elif isinstance(part, Motherboard):
                current_part = current_mobo
                socket_generations = {
                    "775": 1,
                    "1155": 2,
                    "1150": 3,
                    "1151": 4,
                    "1200": 5,
                    "1700": 6,
                    "AM3+": 2,
                    "FM2+": 2,
                    "AM4": 5,
                    "AM5": 6,
                }

                current_gen = socket_generations.get(current_mobo.socket, 0)
                new_gen = socket_generations.get(part.socket, 0)

                if new_gen > current_gen:
                    gain = 40 + (new_gen - current_gen) * 15
                elif new_gen == current_gen:
                    gain = 10
                else:
                    gain = -30

            elif isinstance(part, SSD):
                current_part = find_similar_ssd(ssd_size)
                try:
                    part_size = parse_size(part.size)
                    if ssd_size > 0 and part_size > ssd_size:
                        gain = (part_size - ssd_size) / ssd_size * 100
                except (ValueError, TypeError, ZeroDivisionError):
                    gain = 0

            elif isinstance(part, HDD):
                current_part = find_similar_hdd(hdd_size)
                try:
                    part_size = parse_size(part.size)
                    if hdd_size > 0 and part_size > hdd_size:
                        gain = (part_size - hdd_size) / hdd_size * 100
                except (ValueError, TypeError, ZeroDivisionError):
                    gain = 0

            gain = round(gain, 2)

            comparison["parts"].append(
                {"new": part, "current": current_part, "gain": gain}
            )

            total_gain += gain

        comparison["performance_gain"] = round(total_gain, 2)

        if comparison["performance_gain"] < 10:
            continue

        comparison_data.append(comparison)

    # Ustaw typy komponentów
    for comparison in comparison_data:
        for part_data in comparison["parts"]:
            part = part_data["new"]
            part.type = part.__class__.__name__

    return comparison_data
