from .helpers import normalize_socket, parse_gb, extract_ddr_type
from ..models import CPU, Motherboard, RAM, GPU
import re


def check_socket_compatibility(cpu_socket, motherboard_socket):
    """
    Sprawdza kompatybilność socketów CPU i płyty głównej.
    Zwraca True jeśli są kompatybilne, False jeśli nie.
    """
    if not cpu_socket or not motherboard_socket:
        return True  # Jeśli brak danych, zakładamy kompatybilność

    cpu_norm = normalize_socket(cpu_socket)
    mobo_norm = normalize_socket(motherboard_socket)

    # Jeśli sockety są identyczne - kompatybilne
    if cpu_norm == mobo_norm:
        return True

    # Sprawdź czy to różne rodziny (Intel vs AMD)
    intel_sockets = ["775", "1150", "1151", "1155", "1200", "1700"]
    amd_sockets = ["AM3+", "AM4", "AM5", "FM2+"]

    cpu_is_intel = any(socket in cpu_norm for socket in intel_sockets)
    cpu_is_amd = any(socket in cpu_norm for socket in amd_sockets)

    mobo_is_intel = any(socket in mobo_norm for socket in intel_sockets)
    mobo_is_amd = any(socket in mobo_norm for socket in amd_sockets)

    # Intel CPU + AMD płyta = NIEKOMPATYBILNE
    if cpu_is_intel and mobo_is_amd:
        return False

    # AMD CPU + Intel płyta = NIEKOMPATYBILNE
    if cpu_is_amd and mobo_is_intel:
        return False

    # Różne sockety tej samej rodziny też są niekompatybilne
    return False


def ram_fits_mobo(ram, mobo):
    """Sprawdza kompatybilność RAM z płytą główną - rozszerzona walidacja"""
    try:
        # 1. PODSTAWOWA WALIDACJA POJEMNOŚCI
        ram_gb = parse_gb(ram.size)
        mobo_limit_gb = parse_gb(mobo.memory_capacity)

        if ram_gb and mobo_limit_gb:
            if ram_gb > mobo_limit_gb:
                print(f"[DEBUG] RAM {ram_gb}GB > limit płyty {mobo_limit_gb}GB")
                return False

        # 2. WALIDACJA LICZBY SLOTÓW I KOŚCI
        if hasattr(mobo, "ram_slots") and mobo.ram_slots:
            mobo_slots = int(mobo.ram_slots)

            # Sprawdź liczbę kości RAM
            if hasattr(ram, "sticks") and ram.sticks:
                ram_sticks = int(ram.sticks)
                if ram_sticks > mobo_slots:
                    print(
                        f"[DEBUG] RAM wymaga {ram_sticks} slotów, płyta ma {mobo_slots}"
                    )
                    return False

            # Sprawdź czy pojedyncza kość nie przekracza limitu na slot
            if ram_gb and mobo_slots > 0:
                max_per_slot = mobo_limit_gb / mobo_slots if mobo_limit_gb else 32

                # Oblicz pojemność pojedynczej kości
                ram_sticks = getattr(ram, "sticks", 1) or 1
                gb_per_stick = ram_gb / ram_sticks

                if gb_per_stick > max_per_slot:
                    print(
                        f"[DEBUG] Kość {gb_per_stick}GB > limit na slot {max_per_slot}GB"
                    )
                    return False

        # 3. WALIDACJA TYPU DDR
        if mobo.memory_type and ram.ram_type:
            mobo_type = mobo.memory_type.upper().replace(" ", "")
            ram_type = ram.ram_type.upper().replace(" ", "")

            # Wyciągnij typ DDR
            mobo_ddr = extract_ddr_type(mobo_type)
            ram_ddr = extract_ddr_type(ram_type)

            if mobo_ddr and ram_ddr and mobo_ddr != ram_ddr:
                print(f"[DEBUG] Niekompatybilne DDR: RAM {ram_ddr} vs płyta {mobo_ddr}")
                return False

        # 4. WALIDACJA CZĘSTOTLIWOŚCI (ostrzeżenie, nie blokada)
        if hasattr(mobo, "max_memory_speed") and mobo.max_memory_speed and ram.clock:
            if ram.clock > mobo.max_memory_speed * 1.2:  # 20% tolerancji
                print(
                    f"[DEBUG] RAM {ram.clock}MHz może być za szybki dla płyty (max {mobo.max_memory_speed}MHz)"
                )
                # Nie blokujemy, tylko ostrzegamy

        return True

    except Exception as e:
        print(f"[WARN] Błąd sprawdzania kompatybilności RAM: {e}")
        return True  # W razie błędu, zakładamy kompatybilność


def get_compatible_motherboards(cpu_socket):
    """Zwraca płyty główne kompatybilne z danym socketem CPU"""
    if not cpu_socket:
        return Motherboard.objects.none()

    cpu_norm = normalize_socket(cpu_socket)

    # Znajdź płyty z tym samym socketem
    compatible_mobos = Motherboard.objects.filter(socket__iexact=cpu_norm)

    # Jeśli nie znaleziono, spróbuj z normalizowanym socketem
    if not compatible_mobos.exists():
        compatible_mobos = Motherboard.objects.filter(socket__icontains=cpu_norm)

    return compatible_mobos


def check_psu_warning(part, psu_watt):
    """Sprawdza czy PSU jest wystarczający dla danego komponentu"""
    warnings = []

    if isinstance(part, GPU) and part.recomended_ps:
        try:
            # Wyciągnij liczbę z pola recomended_ps
            recommended_match = re.search(r"(\d+)", str(part.recomended_ps))
            if recommended_match:
                recommended = int(recommended_match.group(1))

                if psu_watt < recommended:
                    shortage = recommended - psu_watt
                    warnings.append(
                        {
                            "type": "psu_insufficient",
                            "component": f"GPU {part.model}",
                            "current_psu": psu_watt,
                            "required_psu": recommended,
                            "shortage": shortage,
                            "message": f"⚠️ GPU wymaga {recommended}W, masz {psu_watt}W (brakuje {shortage}W)",
                        }
                    )
                elif psu_watt < recommended * 1.2:  # Mniej niż 20% zapasu
                    warnings.append(
                        {
                            "type": "psu_tight",
                            "component": f"GPU {part.model}",
                            "current_psu": psu_watt,
                            "required_psu": recommended,
                            "message": f"⚡ GPU wymaga {recommended}W, masz {psu_watt}W (mały zapas)",
                        }
                    )
        except (ValueError, IndexError, AttributeError):
            pass

    return warnings if warnings else None


def get_psu_recommendation(combo, current_cpu_tdp=65):
    """Zwraca rekomendację PSU dla danej kombinacji"""
    required_power = calculate_total_psu_requirement(combo, current_cpu_tdp)

    # Standardowe moce PSU
    standard_psu_sizes = [450, 500, 550, 600, 650, 700, 750, 800, 850, 1000, 1200]

    # Znajdź najmniejszy PSU z 10% zapasem
    recommended_psu = None
    for psu_size in standard_psu_sizes:
        if psu_size >= required_power * 1.1:  # 10% dodatkowego zapasu
            recommended_psu = psu_size
            break

    if not recommended_psu:
        recommended_psu = 1200  # Fallback dla bardzo mocnych konfiguracji

    return {
        "calculated_requirement": required_power,
        "recommended_psu": recommended_psu,
        "efficiency_rating": "80+ Bronze minimum, 80+ Gold recommended",
    }


def calculate_total_psu_requirement(combo, current_cpu_tdp=65):
    """Oblicza całkowite zapotrzebowanie na moc dla kombinacji komponentów"""
    total_power = 0

    # Bazowe zużycie systemu (płyta główna, RAM, dyski, wentylatory)
    base_system_power = 100
    total_power += base_system_power

    # CPU - użyj obecnego CPU TDP jako bazę
    cpu_power = current_cpu_tdp
    for part in combo:
        if isinstance(part, CPU):
            # Szacunkowe TDP na podstawie benchmarku (bardzo przybliżone)
            if part.benchmark:
                cpu_power = min(125, max(65, part.benchmark * 0.8))  # 65-125W
            break
    total_power += cpu_power

    # GPU - najważniejszy komponent pod względem mocy
    gpu_power = 0
    for part in combo:
        if isinstance(part, GPU) and part.recomended_ps:
            try:
                recommended_match = re.search(r"(\d+)", str(part.recomended_ps))
                if recommended_match:
                    # Zalecane PSU zawiera już zapas, więc GPU zużywa ~60-70% z tego
                    recommended_psu = int(recommended_match.group(1))
                    gpu_power = recommended_psu * 0.65  # Szacunkowe zużycie GPU
                    break
            except (ValueError, AttributeError):
                pass

    total_power += gpu_power

    # Dodaj 15% zapasu bezpieczeństwa
    total_power *= 1.15

    return int(total_power)


def get_compatible_cpus(motherboard_socket):
    """Zwraca CPU kompatybilne z danym socketem płyty głównej"""
    if not motherboard_socket:
        return CPU.objects.none()

    mobo_norm = normalize_socket(motherboard_socket)

    # Znajdź CPU z tym samym socketem
    compatible_cpus = CPU.objects.filter(socket__iexact=mobo_norm)

    # Jeśli nie znaleziono, spróbuj z normalizowanym socketem
    if not compatible_cpus.exists():
        compatible_cpus = CPU.objects.filter(socket__icontains=mobo_norm)

    return compatible_cpus
