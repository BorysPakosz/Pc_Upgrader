from django.db.models import Q
from ..models import CPU, GPU, RAM, Motherboard, HDD, SSD
from .helpers import parse_gb, normalize_socket, parse_size
from .filtering import smart_ram_filtering


def find_current_components(cpu_name, gpu_name, mobo_name, ram_name):
    """Znajduje obecne komponenty w bazie danych z naprawą socketu CPU"""

    # SPRAWDŹ CZY PARAMETRY ISTNIEJĄ
    if not cpu_name or cpu_name.strip() == "":
        print(f"[ERROR] Pusta nazwa CPU")
        return None, None, None, None

    # WYSZUKIWANIE CPU
    current_cpu = None

    # Najpierw spróbuj dokładnego dopasowania
    current_cpu = CPU.objects.filter(
        Q(title__iexact=cpu_name) | Q(model__iexact=cpu_name)
    ).first()

    if current_cpu:
        print(f"[INFO] Znaleziono CPU (dokładne dopasowanie): '{current_cpu.title}'")
    else:
        # Jeśli nie znaleziono dokładnego, spróbuj zawierania całej nazwy
        current_cpu = CPU.objects.filter(
            Q(title__icontains=cpu_name) | Q(model__icontains=cpu_name)
        ).first()

        if current_cpu:
            print(
                f"[INFO] Znaleziono CPU (częściowe dopasowanie): '{current_cpu.title}'"
            )

    if not current_cpu:
        print(f"[ERROR] Nie znaleziono CPU dla: {cpu_name}")
        return None, None, None, None

    # DOKŁADNE WYSZUKIWANIE GPU
    current_gpu = GPU.objects.filter(
        Q(title__iexact=gpu_name) | Q(title__icontains=gpu_name)
    ).first()

    if not current_gpu:
        print(f"[ERROR] Nie znaleziono GPU dla: {gpu_name}")
        return None, None, None, None

    # DOKŁADNE WYSZUKIWANIE MOBO
    current_mobo = Motherboard.objects.filter(
        Q(name__iexact=mobo_name) | Q(name__icontains=mobo_name)
    ).first()

    if not current_mobo:
        print(f"[ERROR] Nie znaleziono MOBO dla: {mobo_name}")
        return None, None, None, None

    # DOKŁADNE WYSZUKIWANIE RAM
    current_ram = None
    if ram_name and ram_name.strip():
        # Najpierw dokładne dopasowanie
        current_ram = RAM.objects.filter(Q(name__iexact=ram_name.strip())).first()

        if not current_ram:
            # Jeśli nie znaleziono dokładnego, spróbuj częściowego
            current_ram = RAM.objects.filter(
                Q(name__icontains=ram_name.strip())
            ).first()

        if current_ram:
            print(
                f"[DEBUG] Znaleziono RAM: {current_ram.name} - {current_ram.size} {current_ram.clock}MHz"
            )
        else:
            print(f"[DEBUG] Nie znaleziono RAM dla nazwy: '{ram_name}'")

    # NAPRAW SOCKET CPU (bez zmian)
    if current_cpu:
        if not current_cpu.socket or current_cpu.socket.strip() == "":
            if (
                current_mobo
                and current_mobo.socket
                and current_mobo.socket.strip() != ""
            ):
                print(
                    f"[INFO] CPU '{current_cpu.title}' nie ma socketu - używam socket z płyty głównej: '{current_mobo.socket}'"
                )
                current_cpu.socket = current_mobo.socket
            else:
                default_socket = get_default_socket_for_cpu(current_cpu.title)
                if default_socket:
                    print(
                        f"[INFO] CPU '{current_cpu.title}' nie ma socketu - używam domyślny: '{default_socket}'"
                    )
                    current_cpu.socket = default_socket
                else:
                    print(
                        f"[ERROR] Nie można ustalić socketu dla CPU '{current_cpu.title}'"
                    )

    return current_cpu, current_gpu, current_mobo, current_ram


def get_default_socket_for_cpu(cpu_title):
    """Ustala domyślny socket na podstawie nazwy CPU"""
    if not cpu_title:
        return None

    cpu_upper = cpu_title.upper()

    # Intel 11th gen (Rocket Lake) - socket 1200
    if any(model in cpu_upper for model in ["I5-11600", "I7-11700", "I9-11900"]):
        return "1200"

    # Intel 12th gen (Alder Lake) - socket 1700
    if any(model in cpu_upper for model in ["I5-12", "I7-12", "I9-12"]):
        return "1700"

    # Intel 13th gen (Raptor Lake) - socket 1700
    if any(model in cpu_upper for model in ["I5-13", "I7-13", "I9-13"]):
        return "1700"

    # Intel 10th gen (Comet Lake) - socket 1200
    if any(model in cpu_upper for model in ["I5-10", "I7-10", "I9-10"]):
        return "1200"

    # Intel 9th gen (Coffee Lake) - socket 1151
    if any(model in cpu_upper for model in ["I5-9", "I7-9", "I9-9"]):
        return "1151"

    # Intel 8th gen (Coffee Lake) - socket 1151
    if any(model in cpu_upper for model in ["I5-8", "I7-8", "I9-8"]):
        return "1151"

    # AMD Ryzen 5000 series - socket AM4
    if any(model in cpu_upper for model in ["RYZEN 5 5", "RYZEN 7 5", "RYZEN 9 5"]):
        return "AM4"

    # AMD Ryzen 7000 series - socket AM5
    if any(model in cpu_upper for model in ["RYZEN 5 7", "RYZEN 7 7", "RYZEN 9 7"]):
        return "AM5"

    # AMD Ryzen 3000 series - socket AM4
    if any(model in cpu_upper for model in ["RYZEN 5 3", "RYZEN 7 3", "RYZEN 9 3"]):
        return "AM4"

    print(f"[WARN] Nie można ustalić domyślnego socketu dla CPU: {cpu_title}")
    return None


def get_better_components(
    current_cpu, current_gpu, current_mobo, current_ram, ssd_size, hdd_size, budget
):
    """Główna funkcja znajdująca lepsze komponenty - TYLKO UPGRADE'Y W GÓRĘ"""

    budget_float = float(budget)
    # NAPRAW SOCKET CPU JEŚLI JEST PUSTY
    if not current_cpu.socket or current_cpu.socket.strip() == "":
        if current_mobo.socket:
            print(
                f"[INFO] CPU '{current_cpu.title}' nie ma socketu - używam socket z płyty głównej: '{current_mobo.socket}'"
            )
            current_cpu.socket = current_mobo.socket
        else:
            print(f"[ERROR] Ani CPU ani płyta główna nie mają socketu!")
            return [], [], [], [], [], []

    if current_ram:
        ram_size = parse_gb(current_ram.size) or 16
        ram_clock = current_ram.clock or 3200

    else:
        ram_size = 16  # DOMYŚLNE WARTOŚCI
        ram_clock = 3200

    # Ustal obecny socket
    current_socket = current_cpu.socket
    current_mobo_socket = current_mobo.socket
    if not current_mobo_socket or current_mobo_socket.strip() == "":
        if "B560" in current_mobo.name.upper():
            current_mobo_socket = "1200"
            print(f"[INFO] Ustalono socket płyty na podstawie nazwy B560: 1200")
        else:
            current_mobo_socket = current_socket

    # Ustal obecny typ DDR na podstawie socketu CPU
    current_ddr_type = None
    if current_socket in ["1700", "AM5"]:
        current_ddr_type = "DDR5"
    elif current_socket in ["1200", "1151", "AM4"]:
        current_ddr_type = "DDR4"
    elif current_socket in ["1150", "1155", "AM3+", "FM2+"]:
        current_ddr_type = "DDR3"
    elif current_socket in ["775"]:
        current_ddr_type = "DDR2"

    # Mapa socketów - TYLKO UPGRADE'Y W GÓRĘ
    socket_upgrade_paths = {
        # Intel
        "775": ["1155", "1150", "1151", "1200", "1700"],
        "1155": ["1150", "1151", "1200", "1700"],
        "1150": ["1151", "1200", "1700"],
        "1151": ["1200", "1700"],
        "1200": ["1700"],
        "Socket 1200": ["1700", "Socket 1700"],
        "Socket 1200 (Rocket Lake)": ["1700", "Socket 1700"],
        "1700": [],
        "Socket 1700": [],
        # AMD
        "AM3+": ["AM4", "AM5"],
        "FM2+": ["AM4", "AM5"],
        "AM4": ["AM5"],
        "Socket AM4": ["AM5", "Socket AM5"],
        "AM5": [],
        "Socket AM5": [],
    }

    # Znajdź możliwe upgrade'y socketów
    possible_socket_upgrades = []
    current_socket_variants = get_socket_variants(current_socket)
    for variant in current_socket_variants:
        if variant in socket_upgrade_paths:
            possible_socket_upgrades.extend(socket_upgrade_paths[variant])

    possible_socket_upgrades = list(set(possible_socket_upgrades))

    # ZNAJDŹ CPU - TYLKO UPGRADE'Y
    better_cpus = []

    # 1. CPU z tym samym socketem (ale lepsze)
    same_socket_cpus = CPU.objects.filter(
        socket=current_socket,
        benchmark__gt=current_cpu.benchmark * 1.10,
        price__isnull=False,
        price__gt=0,
        benchmark__isnull=False,
    ).order_by("-benchmark")[:50]

    better_cpus.extend(same_socket_cpus)

    # 2. CPU z nowszymi socketami
    for upgrade_socket in possible_socket_upgrades:
        upgrade_variants = get_socket_variants(upgrade_socket)

        for variant in upgrade_variants:
            upgrade_cpus = CPU.objects.filter(
                Q(socket__icontains=variant) | Q(socket__exact=variant),
                benchmark__gt=current_cpu.benchmark * 1.05,
                price__isnull=False,
                price__gt=0,
                benchmark__isnull=False,
            ).order_by("-benchmark")[:30]

            if upgrade_cpus:
                better_cpus.extend(upgrade_cpus)

    # LEPSZE GPU
    better_gpus = GPU.objects.filter(
        benchmark__gt=current_gpu.benchmark * 1.08,
        price__isnull=False,
        price__gt=0,
        benchmark__isnull=False,
    ).order_by("-benchmark")[:150]

    # PŁYTY GŁÓWNE - TYLKO NOWSZE SOCKETY
    better_mobos = []

    for upgrade_socket in possible_socket_upgrades:
        upgrade_variants = get_socket_variants(upgrade_socket)

        for variant in upgrade_variants:
            upgrade_mobos = (
                Motherboard.objects.filter(
                    Q(socket__icontains=variant) | Q(socket__exact=variant),
                    socket__isnull=False,
                    price__isnull=False,
                    price__gt=0,
                )
                .exclude(socket="")
                .order_by("price")[:50]
            )

            if upgrade_mobos:
                better_mobos.extend(upgrade_mobos)

    # INTELIGENTNE RAM-y
    better_rams = []

    # Określ typy DDR dla nowszych socketów
    newer_ddr_types = set()
    for socket in possible_socket_upgrades:
        if socket in ["1700", "AM5"]:
            newer_ddr_types.update(["DDR4", "DDR5"])
        elif socket in ["1200", "1151", "AM4"]:
            newer_ddr_types.add("DDR4")
        elif socket in ["1150", "AM3+"]:
            newer_ddr_types.add("DDR3")

    # RAM dla nowszych socketów
    all_candidate_rams = []
    for ddr_type in newer_ddr_types:
        type_rams = RAM.objects.filter(
            Q(ram_type__icontains=ddr_type), price__isnull=False, price__gt=0
        )[
            :100
        ]  # Więcej kandydatów do filtrowania
        all_candidate_rams.extend(type_rams)

    # Dodaj RAM kompatybilny z obecnym socketem
    if current_ddr_type and ram_size < 32:
        current_compatible_rams = RAM.objects.filter(
            Q(ram_type__icontains=current_ddr_type), price__isnull=False, price__gt=0
        )[:50]
        all_candidate_rams.extend(current_compatible_rams)

    # Usuń duplikaty
    all_candidate_rams = list(set(all_candidate_rams))

    # SMART FILTERING dla każdej płyty głównej
    # Użyj obecnej płyty jako referencji
    better_rams = smart_ram_filtering(
        all_candidate_rams, current_mobo, ram_size, ram_clock, budget_float
    )

    # Dodaj RAM dla nowszych płyt głównych
    for mobo in better_mobos[:10]:  # Top 10 płyt
        mobo_compatible_rams = smart_ram_filtering(
            all_candidate_rams, mobo, ram_size, ram_clock, budget_float
        )
        better_rams.extend(mobo_compatible_rams[:10])  # Top 10 na płytę

    # Usuń duplikaty i sortuj
    better_rams = list(set(better_rams))
    better_rams.sort(key=lambda r: getattr(r, "compatibility_score", 0), reverse=True)
    better_rams = better_rams[:100]

    # DYSKI
    better_ssds = []
    for ssd in SSD.objects.filter(price__isnull=False, price__gt=0)[:200]:
        try:
            ssd_gb = parse_size(ssd.size)
            if ssd_gb >= ssd_size * 1.3:
                better_ssds.append(ssd)
        except:
            continue
    better_ssds = better_ssds[:60]

    better_hdds = []
    if hdd_size > 0:
        for hdd in HDD.objects.filter(price__isnull=False, price__gt=0)[:100]:
            try:
                hdd_gb = parse_size(hdd.size)
                if hdd_gb >= hdd_size * 1.3:
                    better_hdds.append(hdd)
            except:
                continue
        better_hdds = better_hdds[:40]

    print(f"[DEBUG] FINALNE WYNIKI (TYLKO UPGRADE'Y):")
    print(f"  CPU: {len(better_cpus)}")
    print(f"  GPU: {len(better_gpus)}")
    print(f"  RAM: {len(better_rams)} (DDR dla nowszych socketów)")
    print(f"  MOBO: {len(better_mobos)} (TYLKO NOWSZE SOCKETY!)")
    print(f"  SSD: {len(better_ssds)}")
    print(f"  HDD: {len(better_hdds)}")

    # Debug platform upgrades
    print(f"[DEBUG] PLATFORM UPGRADE ANALYSIS:")
    print(
        f"  Current socket: {current_socket} (generation: {socket_upgrade_paths.get(current_socket, [])})"
    )
    print(f"  Better MOBOs found: {len(better_mobos)}")
    print(f"  Better RAMs found: {len(better_rams)}")

    platform_combos = 0
    for mobo in better_mobos[:5]:
        for cpu in better_cpus[:5]:
            if cpu.socket == mobo.socket:
                for ram in better_rams[:3]:
                    platform_combos += 1
                    if platform_combos <= 3:
                        print(
                            f"  Example platform: {cpu.socket} - {cpu.model[:20]}... + {ram.size}"
                        )

    print(f"  Possible platform combinations: {platform_combos}")

    return better_cpus, better_gpus, better_rams, better_mobos, better_ssds, better_hdds


def get_socket_variants(socket_name):
    """Zwraca wszystkie możliwe warianty nazwy socketu"""
    base = normalize_socket(socket_name)
    variants = [
        base,  # "1200"
        f"Socket {base}",  # "Socket 1200"
        f"LGA{base}",  # "LGA1200" (dla Intel)
        f"LGA {base}",  # "LGA 1200"
    ]

    if socket_name not in variants:
        variants.append(socket_name)

    return variants
