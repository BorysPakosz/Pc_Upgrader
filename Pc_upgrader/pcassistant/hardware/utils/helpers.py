import re


def _to_float(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _price(part):
    return _to_float(getattr(part, "price", None), float("inf"))


def _bench(part):
    return _to_float(getattr(part, "benchmark", None), 0.0)


def parse_gb(value):
    """Wyciąga liczbę GB z tekstu, np. '16 GB' -> 16"""
    if not value:
        return None

    value = re.sub(r"\(.*?\)", "", str(value))
    match = re.search(r"(\d+)\s?GB?", value, re.IGNORECASE)
    if match:
        return int(match.group(1))

    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else None


def parse_size(size_value):
    """Konwertuje rozmiar na liczbę całkowitą"""
    if isinstance(size_value, (int, float)):
        return int(size_value)
    elif isinstance(size_value, str):
        size_str = "".join(filter(str.isdigit, size_value))
        return int(size_str) if size_str else 0
    return 0


def normalize_socket(socket_name):
    """Normalizuje nazwę socketu do standardowego formatu"""
    if not socket_name:
        return ""
    return socket_name.strip().upper()


def extract_ddr_type(memory_type):
    """Wyciąga typ DDR z nazwy pamięci"""
    if not memory_type:
        return None

    for ddr_type in ["DDR5", "DDR4", "DDR3", "DDR2"]:
        if ddr_type in memory_type:
            return ddr_type
    return None


def find_similar_ssd(ssd_size):
    """Znajduje podobny SSD w bazie danych"""
    from ..models import SSD  # Import lokalny

    try:
        # Znajdź SSD o podobnej pojemności
        similar_ssd = SSD.objects.filter(
            size__gte=ssd_size * 0.8,  # 80-120% pojemności
            size__lte=ssd_size * 1.2,
            price__isnull=False,
        ).first()

        if similar_ssd:
            return similar_ssd

        # Fallback - znajdź jakikolwiek SSD
        return SSD.objects.filter(price__isnull=False).first()

    except Exception:
        return None


def find_similar_hdd(hdd_size):
    """Znajduje podobny HDD w bazie danych"""
    from ..models import HDD  # Import lokalny

    try:
        if hdd_size <= 0:
            return None

        # Znajdź HDD o podobnej pojemności
        similar_hdd = HDD.objects.filter(
            size__gte=hdd_size * 0.8,  # 80-120% pojemności
            size__lte=hdd_size * 1.2,
            price__isnull=False,
        ).first()

        if similar_hdd:
            return similar_hdd

        # Fallback - znajdź jakikolwiek HDD
        return HDD.objects.filter(price__isnull=False).first()

    except Exception:
        return None
