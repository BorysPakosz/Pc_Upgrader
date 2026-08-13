from .helpers import _price, _bench, normalize_socket
from .compatibility import (
    check_socket_compatibility,
    ram_fits_mobo,
    check_psu_warning,
    get_psu_recommendation,
)
from .performance import calculate_performance_gain
from .filtering import (
    prune_dominated_by_bench_price,
    sort_by_value,
    filter_motherboards_by_budget_tier,
    sort_motherboards_by_quality,
    smart_proposal_selection,
)
from ..models import CPU, GPU, RAM, SSD, Motherboard
import re


def generate_proposals(
    better_cpus,
    better_gpus,
    better_rams,
    better_mobos,
    better_ssds,
    better_hdds,
    budget,
    psu_watt,
    ram_size,
    ram_clock,
    current_cpu,
    current_mobo,
):
    """Generuje propozycje upgrade'ów z lepszym dopasowaniem do budżetu (min 75%) i PSU"""

    budget_float = float(budget)
    proposals = []
    min_budget_threshold = budget_float * 0.75  # 75% budżetu jako minimum

    seen_combinations = set()

    def add_proposal(
        combo, priority_weight=1.0, combo_type="other", enforce_min_budget=True
    ):
        """Dodaje propozycję z sprawdzaniem PSU i budżetu (min 75%)"""
        combo_key = tuple(
            sorted(
                [f"{part.__class__.__name__}_{part.id}_{part.price}" for part in combo]
            )
        )

        if combo_key in seen_combinations:
            return  # Pomiń duplikat

        seen_combinations.add(combo_key)
        total_price = sum(float(part.price) for part in combo)

        if enforce_min_budget and total_price < min_budget_threshold:
            return

        if total_price > budget_float:
            return  # Za drogie - przekracza budżet

        # Sprawdź wszystkie ostrzeżenia PSU dla kombinacji
        psu_warnings = []
        psu_insufficient = False

        for part in combo:
            warnings = check_psu_warning(part, psu_watt)
            if warnings:
                psu_warnings.extend(warnings)
                for warning in warnings:
                    if warning["type"] == "psu_insufficient":
                        psu_insufficient = True

        # Oblicz rekomendację PSU dla całej kombinacji
        psu_recommendation = get_psu_recommendation(combo, current_cpu.benchmark or 65)

        # Jeśli PSU jest niewystarczający, obniż priorytet ale nie odrzucaj
        if psu_insufficient:
            priority_weight *= 0.5

        # Oblicz przyrost wydajności
        improvement = 0.0
        for part in combo:
            if hasattr(part, "benchmark") and part.benchmark:
                improvement += part.benchmark * 0.01

        # Oblicz % wykorzystania budżetu
        budget_usage = (total_price / budget_float) * 100

        budget_bonus = 1.0
        if 90 <= budget_usage <= 98:
            budget_bonus = 1.4  # Najlepsze wykorzystanie
        elif 85 <= budget_usage < 90:
            budget_bonus = 1.3
        elif 80 <= budget_usage < 85:
            budget_bonus = 1.2
        elif 75 <= budget_usage < 80:
            budget_bonus = 1.1

        priority_weight *= budget_bonus

        proposals.append(
            {
                "parts": combo,
                "total_price": total_price,
                "priority_weight": priority_weight,
                "improvement": improvement,
                "psu_warnings": psu_warnings,
                "psu_recommendation": psu_recommendation,
                "psu_insufficient": psu_insufficient,
                "combo_type": combo_type,
                "budget_usage": budget_usage,
                "budget_bonus": budget_bonus,
            }
        )

    print(
        f"[INFO] Generowanie propozycji z budżetem {budget} zł (min {min_budget_threshold} zł - 75%)"
    )
    print(f"[INFO] PSU: {psu_watt}W")
    print(
        f"[INFO] Komponenty: {len(better_cpus)} CPU, {len(better_gpus)} GPU, {len(better_rams)} RAM, {len(better_mobos)} MOBO"
    )

    # Najpierw filtr budżetu i danych + usuń zdominowane, potem sortuj po opłacalności
    budget_float = float(budget)
    filtered_gpus = [
        g for g in better_gpus if _price(g) <= budget_float and _bench(g) > 0
    ]
    filtered_cpus = [
        c for c in better_cpus if _price(c) <= budget_float and _bench(c) > 0
    ]

    filtered_gpus = prune_dominated_by_bench_price(filtered_gpus)
    filtered_cpus = prune_dominated_by_bench_price(filtered_cpus)

    # Sortowanie po value (benchmark/cena), następnie benchmark, następnie cena
    sorted_gpus = sort_by_value(filtered_gpus)
    sorted_cpus = sort_by_value(filtered_cpus)

    # Filtruj płyty według budżetu i tier chipsetu
    budget_appropriate_mobos = filter_motherboards_by_budget_tier(better_mobos, budget)

    # Sortuj według jakości (chipset + stosunek jakości do ceny)
    sorted_mobos = sort_motherboards_by_quality(budget_appropriate_mobos)

    print(
        f"[DEBUG] Płyty po filtracji: {len(budget_appropriate_mobos)} z {len(better_mobos)}"
    )

    sorted_rams = sorted(better_rams, key=lambda x: x.price)

    for gpu in sorted_gpus:
        gpu.price = float(gpu.price)
    for cpu in sorted_cpus:
        cpu.price = float(cpu.price)
    for mobo in sorted_mobos:
        mobo.price = float(mobo.price)
    for ram in sorted_rams:
        ram.price = float(ram.price)

    # PRIORYTET 1: PEŁNE UPGRADE'Y PLATFORMY (GPU + CPU + MOBO + RAM)
    print("[INFO] PRIORYTET 1: PEŁNE UPGRADE'Y PLATFORMY")
    full_upgrade_count = 0
    max_full_upgrades = 15
    # INTELIGENTNE DOPASOWANIE DO BUDŻETU
    target_ranges = [
        (budget_float * 0.90, budget_float),  # 90-100% budżetu
        (budget_float * 0.85, budget_float * 0.90),  # 85-90% budżetu
        (budget_float * 0.80, budget_float * 0.85),  # 80-85% budżetu
        (budget_float * 0.75, budget_float * 0.80),  # 75-80% budżetu
    ]

    for min_target, max_target in target_ranges:

        for gpu in sorted_gpus:
            if gpu.price > max_target * 0.6:  # GPU nie może być więcej niż 60% budżetu
                continue

            remaining_after_gpu = max_target - gpu.price
            if remaining_after_gpu < 300:
                continue

            for cpu in sorted_cpus:
                if normalize_socket(cpu.socket) == normalize_socket(current_cpu.socket):
                    continue

                if (
                    cpu.price > remaining_after_gpu * 0.6
                ):  # CPU nie więcej niż 60% pozostałego
                    continue

                remaining_after_cpu = remaining_after_gpu - cpu.price
                if remaining_after_cpu < 200:
                    continue

                for mobo in sorted_mobos:
                    if not check_socket_compatibility(cpu.socket, mobo.socket):
                        continue

                    if (
                        mobo.price > remaining_after_cpu * 0.7
                    ):  # MOBO nie więcej niż 70% pozostałego
                        continue

                    remaining_after_mobo = remaining_after_cpu - mobo.price
                    if remaining_after_mobo < 50:
                        continue

                    for ram in sorted_rams:
                        if (
                            ram.price > budget_float * 0.15
                        ):  # RAM nie więcej niż 15% całego budżetu
                            continue

                        if not ram_fits_mobo(ram, mobo):
                            continue

                        total_price = gpu.price + cpu.price + mobo.price + ram.price

                        # SPRAWDŹ CZY MIEŚCI SIĘ W DOCELOWYM PRZEDZIALE
                        if min_target <= total_price <= max_target:
                            add_proposal([gpu, cpu, mobo, ram], 20.0, "full_upgrade")
                            full_upgrade_count += 1

                            if full_upgrade_count >= max_full_upgrades:
                                break
                        if full_upgrade_count >= max_full_upgrades:
                            break
                    if full_upgrade_count >= max_full_upgrades:
                        break
                if full_upgrade_count >= max_full_upgrades:
                    break
            if full_upgrade_count >= max_full_upgrades:
                break

        if (
            full_upgrade_count >= max_full_upgrades
        ):  # WYJDŹ Z PĘTLI JEŚLI OSIĄGNIĘTO LIMIT
            break

    # Ogranicz liczbę propozycji przed końcowym sortowaniem
    if len(proposals) > 50:
        # Sortuj tymczasowo i weź najlepsze 50
        temp_sorted = sorted(
            proposals,
            key=lambda p: (-p.get("priority_weight", 0), p.get("total_price", 0)),
        )
        proposals = temp_sorted[:50]
        print(
            f"[INFO] Ograniczono do {len(proposals)} najlepszych propozycji przed deduplikacją"
        )

    # PRIORYTET 2: PLATFORM UPGRADE (CPU + MOBO + RAM)
    print("[INFO] 🔥 PRIORYTET 2: PLATFORM UPGRADE (CPU + MOBO + RAM)")
    platform_count = 0
    max_platform_upgrades = 15

    for min_target, max_target in target_ranges:
        for cpu in sorted_cpus:
            if normalize_socket(cpu.socket) == normalize_socket(current_cpu.socket):
                continue

            if cpu.price > max_target * 0.7:  # CPU nie więcej niż 70% budżetu
                continue

            remaining_after_cpu = max_target - cpu.price
            if remaining_after_cpu < 150:
                continue

            for mobo in sorted_mobos:
                if normalize_socket(cpu.socket) != normalize_socket(mobo.socket):
                    continue

                if mobo.price > remaining_after_cpu * 0.8:
                    continue

                remaining_after_mobo = remaining_after_cpu - mobo.price
                if remaining_after_mobo < 50:
                    continue

                for ram in sorted_rams:
                    if ram.price > budget_float * 0.20:
                        continue
                    if not ram_fits_mobo(ram, mobo):
                        continue

                    total_price = cpu.price + mobo.price + ram.price

                    if min_target <= total_price <= max_target:
                        add_proposal([cpu, mobo, ram], 18.0, "cpu_mobo_ram")
                        platform_count += 1

                        if platform_count >= max_platform_upgrades:
                            break
                    if platform_count >= max_platform_upgrades:
                        break
                if platform_count >= max_platform_upgrades:
                    break
            if platform_count >= max_platform_upgrades:
                break

        if platform_count >= max_platform_upgrades:
            break

    print(f"[INFO] Dodano {platform_count} platform upgrade'ów")

    # PRIORYTET 3: GPU + CPU COMBO (ten sam socket)
    print("[INFO] PRIORYTET 3: GPU + CPU COMBO")
    gpu_cpu_count = 0

    for min_target, max_target in target_ranges:
        for gpu in sorted_gpus:
            if gpu.price > max_target * 0.8:  # GPU nie więcej niż 80% budżetu
                continue

            remaining_after_gpu = max_target - gpu.price
            if remaining_after_gpu < 200:
                continue

            for cpu in sorted_cpus:
                if normalize_socket(cpu.socket) != normalize_socket(current_cpu.socket):
                    continue  # Tylko ten sam socket

                total_price = gpu.price + cpu.price

                if min_target <= total_price <= max_target:
                    add_proposal([gpu, cpu], 16.0, "gpu_cpu")
                    gpu_cpu_count += 1

                    if gpu_cpu_count >= 30:
                        break
            if gpu_cpu_count >= 30:
                break

        if gpu_cpu_count >= 10:
            break

    print(f"[INFO] Dodano {gpu_cpu_count} kombinacji GPU+CPU")

    # PRIORYTET 4: POJEDYNCZE UPGRADE'Y - DOPASOWANE DO BUDŻETU
    print("[INFO] PRIORYTET 4: POJEDYNCZE UPGRADE'Y (75%+ budżetu)")

    # GPU pojedyncze - tylko te które wykorzystują min 75% budżetu
    gpu_single_count = 0

    # Kategoryzuj GPU według wymagań PSU
    gpu_categories = {
        "low_power": [],
        "medium_power": [],
        "high_power": [],
        "extreme_power": [],
    }

    for gpu in sorted_gpus:
        #  TYLKO GPU KTÓRE WYKORZYSTUJĄ MIN 75% BUDŻETU

        if gpu.recomended_ps:
            try:
                recommended_match = re.search(r"(\d+)", str(gpu.recomended_ps))
                if recommended_match:
                    required_psu = int(recommended_match.group(1))

                    if required_psu <= 500:
                        gpu_categories["low_power"].append(gpu)
                    elif required_psu <= 650:
                        gpu_categories["medium_power"].append(gpu)
                    elif required_psu <= 750:
                        gpu_categories["high_power"].append(gpu)
                    else:
                        gpu_categories["extreme_power"].append(gpu)
            except (ValueError, AttributeError):
                gpu_categories["medium_power"].append(gpu)
        else:
            gpu_categories["medium_power"].append(gpu)

    # Dodaj GPU z odpowiednich kategorii w zależności od PSU użytkownika
    if psu_watt >= 750:
        for category in ["low_power", "medium_power", "high_power", "extreme_power"]:
            for gpu in gpu_categories[category][
                :6
            ]:  # Mniej GPU, ale lepiej dopasowanych
                add_proposal(
                    [gpu], 14.0, f"gpu_single_{category}", enforce_min_budget=False
                )

                gpu_single_count += 1
    elif psu_watt >= 650:
        for category in ["low_power", "medium_power", "high_power"]:
            for gpu in gpu_categories[category][:8]:
                add_proposal(
                    [gpu], 14.0, f"gpu_single_{category}", enforce_min_budget=False
                )
                gpu_single_count += 1
    elif psu_watt >= 500:
        for category in ["low_power", "medium_power"]:
            for gpu in gpu_categories[category][:10]:
                add_proposal(
                    [gpu], 14.0, f"gpu_single_{category}", enforce_min_budget=False
                )
                gpu_single_count += 1
    else:
        for gpu in gpu_categories["low_power"][:12]:
            add_proposal([gpu], 14.0, "gpu_single_low_power")
            gpu_single_count += 1

    print(
        f"[INFO] Dodano {gpu_single_count} pojedynczych GPU (75%+ budżetu, dopasowanych do PSU {psu_watt}W)"
    )

    # CPU pojedyncze (tylko ten sam socket i 75%+ budżetu)
    cpu_single_count = 0
    for cpu in sorted_cpus:
        if normalize_socket(cpu.socket) == normalize_socket(current_cpu.socket):
            add_proposal([cpu], 12.0, "cpu_single", enforce_min_budget=False)
            cpu_single_count += 1
            if cpu_single_count >= 10:
                break

    print(f"[INFO] Dodano {cpu_single_count} pojedynczych CPU (75%+ budżetu)")

    print(f"[INFO] 🎯 ŁĄCZNIE WYGENEROWANO {len(proposals)} PROPOZYCJI")

    # Pokaż statystyki wykorzystania budżetu
    budget_stats = {}
    for proposal in proposals:
        usage = proposal["budget_usage"]
        if usage >= 95:
            range_key = "95-100%"
        elif usage >= 90:
            range_key = "90-95%"
        elif usage >= 85:
            range_key = "85-90%"
        elif usage >= 80:
            range_key = "80-85%"
        elif usage >= 75:
            range_key = "75-80%"
        else:
            range_key = "<75%"

        budget_stats[range_key] = budget_stats.get(range_key, 0) + 1

    print("[INFO] 📊 WYKORZYSTANIE BUDŻETU:")
    for range_name in ["95-100%", "90-95%", "85-90%", "80-85%", "75-80%", "<75%"]:
        count = budget_stats.get(range_name, 0)
        if count > 0:
            print(f"  {range_name}: {count} propozycji")

    # Pokaż statystyki PSU
    psu_stats = {"sufficient": 0, "insufficient": 0, "tight": 0}

    for proposal in proposals:
        if proposal.get("psu_insufficient"):
            psu_stats["insufficient"] += 1
        elif proposal.get("psu_warnings"):
            psu_stats["tight"] += 1
        else:
            psu_stats["sufficient"] += 1

    print("[INFO] ⚡ STATYSTYKI PSU:")
    print(f"  Wystarczający PSU: {psu_stats['sufficient']} propozycji")
    print(f"  Ciasny PSU: {psu_stats['tight']} propozycji")
    print(f"  Niewystarczający PSU: {psu_stats['insufficient']} propozycji")

    return proposals


def sort_proposals(proposals, current_cpu, current_gpu, ram_size, ssd_size, hdd_size):
    """Sortowanie propozycji z priorytetem dla CPU+MOBO kombinacji"""

    print(f"[DEBUG] PRZED SORTOWANIEM:")
    combo_types_before = {}
    for proposal in proposals:
        combo_type = proposal.get("combo_type", "other")
        combo_types_before[combo_type] = combo_types_before.get(combo_type, 0) + 1

    for combo_type, count in combo_types_before.items():
        print(f"  {combo_type}: {count}")

    def get_sort_key(proposal):
        performance_gain = 0
        combo_type = proposal.get("combo_type", "other")

        # BONUS PRIORYTETOWY dla kombinacji CPU+MOBO
        priority_bonus = {
            "full_upgrade": 15.0,
            "cpu_mobo_ram": 12.0,
            "gpu_cpu_mobo": 11.0,
            "cpu_mobo": 10.0,
            "gpu_cpu": 7.0,
            "gpu_single": 6.0,
            "cpu_single": 5.5,
            "gpu_cpu_ram": 5.0,
            "gpu_mobo": 4.5,
            "mobo_ram": 4.0,
            "cpu_ram": 3.5,
            "gpu_ram": 3.0,
            "mobo_single": 2.5,
            "ram_single": 2.0,
        }.get(combo_type, 1.0)

        # Oblicz przyrost wydajności
        for part in proposal["parts"]:
            gain = calculate_performance_gain(
                part, current_cpu, current_gpu, ram_size, ssd_size, hdd_size
            )

            if isinstance(part, CPU):
                performance_gain += gain * 3.0
            elif isinstance(part, GPU):
                performance_gain += gain * 4.0
            elif isinstance(part, Motherboard):
                performance_gain += 15.0
            elif isinstance(part, RAM):
                performance_gain += gain * 2.0
            elif isinstance(part, SSD):
                performance_gain += gain * 0.5

        total_price = proposal.get("total_price", 0)
        base_priority = proposal.get("priority_weight", 1.0)

        # Oblicz końcowy wynik
        if total_price > 0:
            performance_per_price = (
                performance_gain * priority_bonus * base_priority
            ) / float(total_price)
        else:
            performance_per_price = 0

        return (-priority_bonus, -performance_per_price, -performance_gain, total_price)

    proposals.sort(key=get_sort_key)
    return proposals


def select_top_proposals(proposals, max_proposals=15):
    """Wybierz najlepszych propozycji z inteligentną deduplikacją"""

    if not proposals:
        return []

    # Sortuj propozycje - priorytet dla wystarczającego PSU
    def sort_key(proposal):
        combo_type = proposal.get("combo_type", "other")
        budget_usage = proposal.get("budget_usage", 0)
        priority_weight = proposal.get("priority_weight", 1.0)
        psu_insufficient = proposal.get("psu_insufficient", False)

        # Bonus za wystarczający PSU
        psu_bonus = 1.2 if not psu_insufficient else 0.8

        # Bonus za dobre wykorzystanie budżetu
        budget_bonus = (
            1.3
            if 85 <= budget_usage <= 98
            else 1.1 if 70 <= budget_usage <= 85 else 1.0
        )

        return (-priority_weight * psu_bonus * budget_bonus, -budget_usage)

    proposals.sort(key=sort_key)

    smart_proposals = smart_proposal_selection(proposals, max_proposals)

    # Debug info
    for i, proposal in enumerate(smart_proposals):
        combo_type = proposal.get("combo_type", "other")
        budget_usage = proposal.get("budget_usage", 0)
        psu_status = "PSU!" if proposal.get("psu_insufficient") else "PSU OK"

        print(
            f"[INFO] #{i + 1}: {combo_type} - {proposal['total_price']:.0f}zł ({budget_usage:.1f}% budżetu) {psu_status}"
        )

    return smart_proposals
