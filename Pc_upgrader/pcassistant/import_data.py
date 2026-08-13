# import_data.py
import os
import csv
import django
import decimal
from decimal import Decimal

# Ustaw środowisko Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pcassistant.settings")
django.setup()

from hardware.models import (
    Producer,
    ComputerCase,
    CPU,
    CPUCooler,
    GPU,
    HDD,
    Motherboard,
    PSU,
    RAM,
    SSD,
)


def clean_decimal(value):
    """Konwertuje string ceny na Decimal"""
    if not value or value == "":
        return None
    # Usuń znaki walutowe i spacje
    value = value.replace("zł", "").replace(" ", "").strip()
    # Zamień przecinek na kropkę
    value = value.replace(",", ".")
    try:
        return Decimal(value)
    except (decimal.InvalidOperation, ValueError):
        return None


def clean_int(value):
    """Konwertuje string na int"""
    if not value or value == "":
        return None
    try:
        # Usuń "mm", "W" itp.
        value = value.split(" ")[0].strip()
        return int(float(value))
    except (ValueError, IndexError):
        return None


def clean_float(value):
    """Konwertuje string na float"""
    if not value or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def clean_bool(value):
    """Konwertuje string na boolean"""
    if not value or value == "":
        return None
    return value.lower() in ["true", "tak", "yes", "1", "t"]


def get_or_create_producer(name):
    """Pobiera lub tworzy producenta"""
    if not name or name == "":
        return None
    producer, created = Producer.objects.get_or_create(name=name)
    return producer


def import_computer_cases(file_path):
    """Import danych o obudowach komputerowych"""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            producer = get_or_create_producer(row.get("Producer", ""))

            ComputerCase.objects.create(
                name=row.get("Name", ""),
                price=clean_decimal(row.get("Price", "")),
                producer=producer,
                mpn=row.get("MPN", ""),
                ean=row.get("EAN", ""),
                upc=row.get("UPC", ""),
                width=clean_int(row.get("Width", "")),
                depth=clean_int(row.get("Depth", "")),
                height=clean_int(row.get("Height", "")),
                motherboard=row.get("Motherboard", ""),
                power_supply=row.get("Power Supply", ""),
                supported_gpu_length=clean_int(row.get("Supported GPU Length", "")),
                supported_cpu_cooler_height=clean_int(
                    row.get("Supported CPU Cooler Height", "")
                ),
                fans_80mm=row.get("80mm Fans", ""),
                fans_120mm=row.get("120mm Fans", ""),
                fans_140mm=row.get("140mm Fans", ""),
                fans_200mm=row.get("200mm Fans", ""),
                radiator_120mm=clean_float(row.get("120mm Radiator Support", "")),
                radiator_140mm=clean_float(row.get("140mm Radiator Support", "")),
                radiator_240mm=clean_float(row.get("240mm Radiator Support", "")),
                radiator_280mm=clean_float(row.get("280mm Radiator Support", "")),
                radiator_360mm=clean_float(row.get("360mm Radiator Support", "")),
                disk_25=clean_int(row.get('Disk 2.5"', "")),
                disk_35=clean_int(row.get('Disk 3.5"', "")),
                disk_25_35=clean_int(row.get('Disk 2.5"/3.5"', "")),
                disk_525=clean_int(row.get('Disk 5.25"', "")),
                primary_color=row.get("Primary Color(s)", ""),
                window=clean_bool(row.get("Window", "")),
                dust_filter=clean_bool(row.get("Dust Filter", "")),
                cable_management=clean_bool(row.get("Cable Management", "")),
                noise_isolation=clean_bool(row.get("Noise Isolation", "")),
                product_page=row.get("Product Page", ""),
            )
    print(f"Zaimportowano obudowy komputerowe z {file_path}")


def import_cpus(file_path):
    """Import danych o procesorach"""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            CPU.objects.create(
                part_number=row.get("Part Number", ""),
                brand=row.get("brand", ""),
                model=row.get("Model", ""),
                rank=clean_int(row.get("Rank", "")),
                benchmark=clean_float(row.get("Benchmark", "")),
                samples=clean_int(row.get("Samples", "")),
                title=row.get("Title", ""),
                price=clean_decimal(row.get("Price", "")),
                image_url=row.get("Image URL", ""),
                frequency=row.get("Frequency", ""),
                cores=row.get("Cores", ""),
                socket=row.get("Socket", ""),
                unlocked_multiplier=row.get("Unlocked Multiplier", ""),
            )
    print(f"Zaimportowano procesory z {file_path}")


def import_cpu_coolers(file_path):
    """Import danych o chłodzeniach CPU"""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            producer = get_or_create_producer(row.get("Producer", ""))

            CPUCooler.objects.create(
                name=row.get("Name", ""),
                price=clean_decimal(row.get("Price", "")),
                producer=producer,
                mpn=row.get("MPN", ""),
                ean=row.get("EAN", ""),
                upc=row.get("UPC", ""),
                supported_sockets=row.get("Supported Sockets", ""),
                height=clean_int(row.get("Height", "")),
                tdp=clean_int(row.get("TDP", "")),
                fans_80mm=clean_int(row.get("80mm Fans", "")),
                fans_92mm=clean_int(row.get("92mm Fans", "")),
                fans_120mm=clean_int(row.get("120mm Fans", "")),
                fans_140mm=clean_int(row.get("140mm Fans", "")),
                fans_200mm=clean_int(row.get("200mm Fans", "")),
                additional_fan_support=clean_bool(
                    row.get("Additional Fan Support", "")
                ),
                product_page=row.get("Product Page", ""),
            )
    print(f"Zaimportowano chłodzenia CPU z {file_path}")


def import_gpus(file_path):
    """Import danych o kartach graficznych"""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            GPU.objects.create(
                title=row.get("title", ""),
                brand=row.get("Brand", ""),
                model=row.get("Model", ""),
                rank=clean_float(row.get("Rank", "")),
                benchmark=clean_float(row.get("Benchmark", "")),
                price=clean_decimal(row.get("price", "")),
                chipset=row.get("chipset", ""),
                ram=row.get("ram", ""),
                dlugosc=row.get("dlugosc", ""),
                taktowanie=row.get("taktowanie", ""),
                part_number=row.get("part_number", "") or row.get("Part Number", ""),
                samples=clean_float(row.get("Samples", "")),
                img_src=row.get("img-src", ""),
                link_produkt_href=row.get("link_produkt-href", ""),
                recomended_ps=row.get("recomended_ps", ""),
            )
    print(f"Zaimportowano karty graficzne z {file_path}")


def import_hdds(file_path):
    """Import danych o dyskach HDD"""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            producer = get_or_create_producer(row.get("Producer", ""))

            HDD.objects.create(
                name=row.get("Name", ""),
                price=clean_decimal(row.get("Price", "")),
                producer=producer,
                mpn=row.get("MPN", ""),
                ean=row.get("EAN", ""),
                upc=row.get("UPC", ""),
                form_factor=row.get("Form Factor", ""),
                size=row.get("Size", ""),
                rpm=clean_float(row.get("RPM", "")),
                cache=row.get("Cache", ""),
                product_page=row.get("Product Page", ""),
            )
    print(f"Zaimportowano dyski HDD z {file_path}")


def import_motherboards(file_path):
    """Import danych o płytach głównych"""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            producer = get_or_create_producer(row.get("Producer", ""))

            Motherboard.objects.create(
                name=row.get("Name", ""),
                price=clean_decimal(row.get("Price", "")),
                producer=producer,
                mpn=row.get("MPN", ""),
                ean=row.get("EAN", ""),
                upc=row.get("UPC", ""),
                socket=row.get("Socket", ""),
                chipset=row.get("Chipset", ""),
                unlocked=clean_bool(row.get("Unlocked", "")),
                form_factor=row.get("Form Factor", ""),
                memory_type=row.get("Memory Type", ""),
                memory_capacity=row.get("Memory Capacity", ""),
                ram_slots=clean_int(row.get("RAM Slots", "")),
                sata=clean_int(row.get("SATA", "")),
                vga=clean_int(row.get("VGA", "")),
                dvi=clean_float(row.get("DVI", "")),
                display_port=clean_float(row.get("Display Port", "")),
                hdmi=clean_float(row.get("HDMI", "")),
                wifi=clean_bool(row.get("WiFi", "")),
                integrated_graphics=clean_bool(row.get("Integrated Graphics", "")),
                product_page=row.get("Product Page", ""),
            )
    print(f"Zaimportowano płyty główne z {file_path}")


def import_psus(file_path):
    """Import danych o zasilaczach"""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            producer = get_or_create_producer(row.get("Producer", ""))

            PSU.objects.create(
                name=row.get("Name", ""),
                price=clean_decimal(row.get("Price", "")),
                producer=producer,
                mpn=row.get("MPN", ""),
                ean=row.get("EAN", ""),
                upc=row.get("UPC", ""),
                watt=row.get("Watt", ""),
                size=row.get("Size", ""),
                efficiency_rating=row.get("Efficiency Rating", ""),
                product_page=row.get("Product Page", ""),
            )
    print(f"Zaimportowano zasilacze z {file_path}")


def import_rams(file_path):
    """Import danych o pamięciach RAM"""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            producer = get_or_create_producer(row.get("Producer", ""))

            RAM.objects.create(
                name=row.get("Name", ""),
                price=clean_decimal(row.get("Price", "")),
                producer=producer,
                mpn=row.get("MPN", ""),
                ean=row.get("EAN", ""),
                upc=row.get("UPC", ""),
                ram_type=row.get("Ram Type", ""),
                size=row.get("Size", ""),
                clock=clean_int(row.get("Clock", "")),
                timings=row.get("Timings", ""),
                sticks=clean_int(row.get("Sticks", "")),
                product_page=row.get("Product Page", ""),
            )
    print(f"Zaimportowano pamięci RAM z {file_path}")


def import_ssds(file_path):
    """Import danych o dyskach SSD"""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            producer = get_or_create_producer(row.get("Producer", ""))

            SSD.objects.create(
                name=row.get("Name", ""),
                price=clean_decimal(row.get("Price", "")),
                producer=producer,
                mpn=row.get("MPN", ""),
                ean=row.get("EAN", ""),
                upc=row.get("UPC", ""),
                form_factor=row.get("Form Factor", ""),
                protocol=row.get("Protocol", ""),
                size=row.get("Size", ""),
                nand=row.get("NAND", ""),
                controller=row.get("Controller", ""),
                product_page=row.get("Product Page", ""),
            )
    print(f"Zaimportowano dyski SSD z {file_path}")


if __name__ == "__main__":
    # Ścieżki do plików CSV - dostosuj do swojej struktury katalogów
    import_computer_cases("data/CaseData.csv")
    import_cpus("data/cpu_data.csv")
    import_cpu_coolers("data/CPUCoolerData.csv")
    import_gpus("data/gpu_data.csv")
    import_hdds("data/HDDData.csv")
    import_motherboards("data/MotherboardData.csv")
    import_psus("data/PSUData.csv")
    import_rams("data/RAMData.csv")
    import_ssds("data/SSDData.csv")

    print("Import zakończony pomyślnie!")
