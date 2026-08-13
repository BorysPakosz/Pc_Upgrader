from collections import defaultdict
from .helpers import _price, _bench, extract_ddr_type, parse_gb
from .performance import value_score, get_chipset_tier
from .compatibility import ram_fits_mobo


def filter_motherboards_by_budget_tier(motherboards, budget):
    """Filtruje płyty główne według odpowiedniego tier dla budżetu"""
    budget_float = float(budget)

    if budget_float >= 8000:  # High-end
        min_tier = 7  # Z690+, X570+, B660+
        max_mobo_price = budget_float * 0.20  # Max 20% budżetu na płytę
    elif budget_float >= 5000:  # Mid-high
        min_tier = 5  # Z490+, B550+, B560+
        max_mobo_price = budget_float * 0.25  # Max 25% budżetu na płytę
    elif budget_float >= 3000:  # Mid
        min_tier = 3  # B450+, B360+
        max_mobo_price = budget_float * 0.30  # Max 30% budżetu na płytę
    else:  # Budget
        min_tier = 1  # Wszystkie
        max_mobo_price = budget_float * 0.35  # Max 35% budżetu na płytę

    # Filtruj według tier i budżetu
    filtered = []
    for mobo in motherboards:
        tier = get_chipset_tier(mobo.chipset)
        price = _price(mobo)

        # Płyta nie może przekroczyć limitu cenowego
        if price > max_mobo_price:
            continue

        # Musi mieć odpowiedni tier
        if tier >= min_tier:
            filtered.append(mobo)

    return filtered


def get_motherboard_score(motherboard):
    """Oblicza wynik płyty głównej na podstawie chipsetu, ceny i funkcji"""
    chipset_tier = get_chipset_tier(motherboard.chipset)
    price = _price(motherboard)

    if price == float("inf") or price <= 0:
        return 0

    # Podstawowy wynik = tier / cena
    base_score = chipset_tier / price * 1000

    # Bonusy za funkcje (jeśli masz takie pola w modelu)
    feature_bonus = 1.0

    # Bonus za WiFi w nazwie
    if hasattr(motherboard, "name") and motherboard.name:
        if "WIFI" in motherboard.name.upper() or "WI-FI" in motherboard.name.upper():
            feature_bonus += 0.1

    # Bonus za nowsze sockety
    socket_bonus = 1.0
    if motherboard.socket:
        if motherboard.socket in ["1700", "AM5"]:
            socket_bonus = 1.3  # Najnowsze
        elif motherboard.socket in ["1200", "AM4"]:
            socket_bonus = 1.1  # Aktualne
        elif motherboard.socket in ["1151"]:
            socket_bonus = 0.9  # Starsze

    return base_score * feature_bonus * socket_bonus


def sort_motherboards_by_quality(motherboards):
    """Sortuje płyty główne według jakości (chipset + stosunek jakości do ceny)"""
    return sorted(motherboards, key=lambda m: (-get_motherboard_score(m), _price(m)))


def smart_proposal_selection(proposals, max_proposals=15):
    """
    Inteligentny wybór propozycji z różnorodnością typów zestawów.
    Zachowuje różne typy zestawów nawet przy podobnych cenach.
    """
    if not proposals:
        return proposals

    print(f"[DEBUG] SMART SELECTION: {len(proposals)} propozycji na wejściu")

    # Krok 1: Usuń bardzo podobne propozycje TYLKO W RAMACH TEGO SAMEGO TYPU
    deduplicated = deduplicate_similar_proposals(
        proposals, similarity_threshold=0.80, max_per_type=3
    )

    # Krok 2: Dodaj różnorodność cenową TYLKO W RAMACH TEGO SAMEGO TYPU
    price_diverse = add_price_diversity_filter(
        deduplicated, min_price_gap=100
    )  # Zmniejszony gap

    # Krok 3: Wybierz najlepsze z każdego typu zestawu
    by_combo_type = defaultdict(list)
    for proposal in price_diverse:
        combo_type = proposal.get("combo_type", "other")
        by_combo_type[combo_type].append(proposal)

    # Limity dla różnych typów zestawów
    type_limits = {
        "full_upgrade": 4,  # Pełne upgrade'y - najważniejsze
        "cpu_mobo_ram": 3,  # Platform upgrade'y
        "gpu_cpu": 3,  # GPU+CPU combo
        "gpu_single_high_power": 2,  # Pojedyncze GPU wysokiej mocy
        "gpu_single_medium_power": 2,  # Pojedyncze GPU średniej mocy
        "gpu_single_low_power": 1,  # Pojedyncze GPU niskiej mocy
        "cpu_single": 2,  # Pojedyncze CPU
        "gpu_single_extreme_power": 1,  # Pojedyncze GPU ekstremalnej mocy
    }

    final_proposals = []

    for combo_type, type_proposals in by_combo_type.items():
        # Określ limit dla tego typu
        limit = type_limits.get(combo_type, 2)  # Domyślnie 2

        # Sortuj według priorytetu
        type_proposals.sort(
            key=lambda p: (-p.get("priority_weight", 0), p.get("total_price", 0))
        )

        # Weź najlepsze z tego typu
        selected = type_proposals[:limit]
        final_proposals.extend(selected)

        print(
            f"[DEBUG] Typ '{combo_type}': wybrano {len(selected)} z {len(type_proposals)} (limit: {limit})"
        )

    # Sortuj końcowy wynik według priorytetu
    final_proposals.sort(
        key=lambda p: (-p.get("priority_weight", 0), p.get("total_price", 0))
    )

    # Ogranicz do maksymalnej liczby
    final_proposals = final_proposals[:max_proposals]

    print(f"[DEBUG] SMART SELECTION: {len(final_proposals)} propozycji na wyjściu")

    # Debug - pokaż typy zestawów w końcowym wyniku
    final_types = defaultdict(int)
    for proposal in final_proposals:
        combo_type = proposal.get("combo_type", "other")
        final_types[combo_type] += 1

    print(f"[DEBUG] Końcowe typy zestawów:")
    for combo_type, count in final_types.items():
        print(f"  {combo_type}: {count}")

    return final_proposals


def deduplicate_similar_proposals(proposals, similarity_threshold=0.85, max_per_type=4):
    """
    Usuwa bardzo podobne propozycje TYLKO W RAMACH TEGO SAMEGO TYPU zestawu.
    Różne typy zestawów (full_upgrade vs gpu_single) są zawsze zachowywane.
    similarity_threshold: próg podobieństwa (0.85 = 85% podobne)
    max_per_type: maksymalna liczba propozycji tego samego typu
    """
    if not proposals:
        return proposals

    print(f"[DEBUG] DEDUPLIKACJA: {len(proposals)} propozycji przed filtrowaniem")

    # Grupuj według typu kombinacji - TO JEST KLUCZOWE!
    by_combo_type = defaultdict(list)
    for proposal in proposals:
        combo_type = proposal.get("combo_type", "other")
        by_combo_type[combo_type].append(proposal)

    deduplicated = []

    for combo_type, type_proposals in by_combo_type.items():
        print(f"[DEBUG] Typ '{combo_type}': {len(type_proposals)} propozycji")

        # Sortuj według priorytetu (najlepsze pierwsze)
        type_proposals.sort(
            key=lambda p: (-p.get("priority_weight", 0), p.get("total_price", 0))
        )

        kept_proposals = []

        for proposal in type_proposals:
            is_similar = False

            # TYLKO sprawdzaj podobieństwo do propozycji TEGO SAMEGO TYPU
            for kept in kept_proposals:
                similarity = calculate_combo_similarity(
                    proposal["parts"], kept["parts"]
                )

                if similarity >= similarity_threshold:
                    # Bardzo podobne - sprawdź która jest lepsza
                    current_score = proposal.get("priority_weight", 0) / max(
                        proposal.get("total_price", 1), 1
                    )
                    kept_score = kept.get("priority_weight", 0) / max(
                        kept.get("total_price", 1), 1
                    )

                    if current_score > kept_score * 1.1:  # 10% lepszy stosunek
                        # Zamień na lepszą propozycję
                        kept_proposals.remove(kept)
                        kept_proposals.append(proposal)
                        print(
                            f"[DEBUG] Zamieniono podobną propozycję w typie '{combo_type}' (similarity: {similarity:.2f})"
                        )
                    else:
                        print(
                            f"[DEBUG] Odrzucono podobną propozycję w typie '{combo_type}' (similarity: {similarity:.2f})"
                        )

                    is_similar = True
                    break

            if not is_similar and len(kept_proposals) < max_per_type:
                kept_proposals.append(proposal)

        print(
            f"[DEBUG] Typ '{combo_type}': zachowano {len(kept_proposals)} z {len(type_proposals)}"
        )
        deduplicated.extend(kept_proposals)

    print(f"[DEBUG] DEDUPLIKACJA: {len(deduplicated)} propozycji po filtrowaniu")
    return deduplicated


def calculate_combo_similarity(combo1, combo2):
    """Oblicza podobieństwo między dwoma kombinacjami (0-1, gdzie 1 = identyczne)"""
    if len(combo1) != len(combo2):
        return 0.0

    same_types = 0
    price_similarity = 0.0
    performance_similarity = 0.0

    # Grupuj komponenty według typu
    combo1_by_type = {type(part).__name__: part for part in combo1}
    combo2_by_type = {type(part).__name__: part for part in combo2}

    for part_type in combo1_by_type:
        if part_type in combo2_by_type:
            same_types += 1
            part1 = combo1_by_type[part_type]
            part2 = combo2_by_type[part_type]

            # Podobieństwo cen (im bliższe, tym wyższy wynik)
            price1 = _price(part1)
            price2 = _price(part2)
            if price1 > 0 and price2 > 0:
                price_diff = abs(price1 - price2) / max(price1, price2)
                price_similarity += max(0, 1 - price_diff)

            # Podobieństwo wydajności
            bench1 = _bench(part1)
            bench2 = _bench(part2)
            if bench1 > 0 and bench2 > 0:
                perf_diff = abs(bench1 - bench2) / max(bench1, bench2)
                performance_similarity += max(0, 1 - perf_diff)

    if same_types == 0:
        return 0.0

    # Średnie podobieństwo
    avg_price_sim = price_similarity / same_types
    avg_perf_sim = performance_similarity / same_types
    type_similarity = same_types / len(combo1)

    # Kombinacja wszystkich czynników
    return avg_price_sim * 0.4 + avg_perf_sim * 0.4 + type_similarity * 0.2


def add_price_diversity_filter(proposals, min_price_gap=150):
    """
    Dodatkowy filtr - usuwa propozycje o bardzo podobnych cenach
    TYLKO W RAMACH TEGO SAMEGO TYPU zestawu.
    min_price_gap: minimalna różnica cen między propozycjami tego samego typu (w zł)
    """
    if not proposals:
        return proposals

    print(f"[DEBUG] FILTR CENOWY: {len(proposals)} propozycji przed filtrowaniem")

    # Grupuj według typu kombinacji
    by_combo_type = defaultdict(list)
    for proposal in proposals:
        combo_type = proposal.get("combo_type", "other")
        by_combo_type[combo_type].append(proposal)

    filtered = []

    for combo_type, type_proposals in by_combo_type.items():
        print(
            f"[DEBUG] Filtr cenowy dla typu '{combo_type}': {len(type_proposals)} propozycji"
        )

        # Sortuj według ceny TYLKO W RAMACH TYPU
        type_proposals.sort(key=lambda p: p.get("total_price", 0))

        type_filtered = []
        last_price = 0

        for proposal in type_proposals:
            current_price = proposal.get("total_price", 0)

            if not type_filtered or current_price - last_price >= min_price_gap:
                type_filtered.append(proposal)
                last_price = current_price
                print(f"[DEBUG] Zachowano {combo_type} za {current_price:.0f}zł")
            else:
                print(
                    f"[DEBUG] Odrzucono {combo_type} za {current_price:.0f}zł (za blisko {last_price:.0f}zł)"
                )

        filtered.extend(type_filtered)
        print(
            f"[DEBUG] Typ '{combo_type}': zachowano {len(type_filtered)} z {len(type_proposals)}"
        )

    print(f"[DEBUG] FILTR CENOWY: {len(filtered)} propozycji po filtrowaniu")
    return filtered


def prune_dominated_by_bench_price(parts):
    """
    Usuwa elementy zdominowane: jeśli istnieje inny element, który ma
    >= benchmark i <= cenę (i przynajmniej jedna nierówność ostra),
    to słabszy-droższy wylatuje.
    """
    items = list(parts)
    kept = []
    n = len(items)
    for i in range(n):
        a = items[i]
        a_b = _bench(a)
        a_p = _price(a)
        dominated = False
        # Jeśli brak danych – zachowaj (opcjonalnie możesz wyrzucić)
        if a_b <= 0 or a_p == float("inf"):
            kept.append(a)
            continue
        for j in range(n):
            if i == j:
                continue
            b = items[j]
            b_b = _bench(b)
            b_p = _price(b)
            if b_b <= 0 or b_p == float("inf"):
                continue
            if (b_b >= a_b and b_p <= a_p) and (b_b > a_b or b_p < a_p):
                dominated = True
                break
        if not dominated:
            kept.append(a)
    return kept


def sort_by_value(parts):
    return sorted(parts, key=lambda p: (-value_score(p), -_bench(p), _price(p)))


def smart_ram_filtering(rams, mobo, current_ram_gb, current_ram_speed, budget):
    """Inteligentne filtrowanie RAM z uwzględnieniem płyty głównej"""
    if not mobo:
        return rams

    compatible_rams = []
    budget_float = float(budget)
    max_ram_budget = budget_float * 0.15  # Max 15% budżetu na RAM

    print(f"[DEBUG] SMART RAM FILTERING:")
    print(f"  Płyta: {mobo.name}")
    print(f"  Sloty RAM: {mobo.ram_slots}")
    print(f"  Max pojemność: {mobo.memory_capacity}")
    print(f"  Typ pamięci: {mobo.memory_type}")
    print(f"  Obecny RAM: {current_ram_gb}GB {current_ram_speed}MHz")
    print(f"  Budżet na RAM: {max_ram_budget}zł")

    # Statystyki
    total_checked = 0
    passed_compatibility = 0
    passed_budget = 0
    passed_improvement = 0

    for ram in rams:
        total_checked += 1

        # 1. Sprawdź kompatybilność
        if not ram_fits_mobo(ram, mobo):
            continue
        passed_compatibility += 1

        # 2. Sprawdź budżet
        if _price(ram) > max_ram_budget:
            continue
        passed_budget += 1

        # 3. Sprawdź czy to upgrade
        ram_gb = parse_gb(ram.size)
        ram_speed = ram.clock or 0

        is_upgrade = False
        if ram_gb and ram_gb > current_ram_gb:
            is_upgrade = True
        elif ram_gb == current_ram_gb and ram_speed > current_ram_speed * 1.1:
            is_upgrade = True
        elif extract_ddr_type(ram.ram_type) == "DDR5" and current_ram_speed < 4800:
            is_upgrade = True  # DDR5 to zawsze upgrade z DDR4

        if not is_upgrade:
            continue
        passed_improvement += 1

        # 4. Dodaj score dla sortowania
        ram.compatibility_score = calculate_ram_score(
            ram, mobo, current_ram_gb, current_ram_speed
        )
        compatible_rams.append(ram)

    print(f"[DEBUG] RAM filtering stats:")
    print(f"  Sprawdzono: {total_checked}")
    print(f"  Kompatybilne: {passed_compatibility}")
    print(f"  W budżecie: {passed_budget}")
    print(f"  Upgrade: {passed_improvement}")
    print(f"  Finalne: {len(compatible_rams)}")

    # Sortuj według score
    compatible_rams.sort(key=lambda r: r.compatibility_score, reverse=True)

    return compatible_rams[:50]


def calculate_ram_score(ram, mobo, current_gb, current_speed):
    """Oblicza score RAM uwzględniając kompatybilność i wydajność"""
    score = 0

    ram_gb = parse_gb(ram.size) or 0
    ram_speed = ram.clock or 0
    price = _price(ram)

    if price <= 0:
        return 0

    # 1. Bonus za pojemność
    if ram_gb > current_gb:
        capacity_bonus = (ram_gb - current_gb) / current_gb * 100
        score += capacity_bonus

    # 2. Bonus za prędkość
    if ram_speed > current_speed:
        speed_bonus = (ram_speed - current_speed) / current_speed * 50
        score += speed_bonus

    # 3. Bonus za DDR5
    if extract_ddr_type(ram.ram_type) == "DDR5":
        score += 30

    # 4. Bonus za dual channel
    if hasattr(ram, "sticks") and ram.sticks == 2:
        score += 20

    # 5. Kara za przepełnienie slotów
    if hasattr(mobo, "ram_slots") and hasattr(ram, "sticks"):
        if ram.sticks > int(mobo.ram_slots or 4):
            score -= 50

    # 6. Stosunek wydajności do ceny
    performance_per_price = score / price * 100

    return performance_per_price
