# myapp/models.py
from django.db import models
from django.contrib.auth.models import User

import uuid
import os


class AdminAction(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="admin_actions"
    )
    target_computer = models.CharField(max_length=200)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Producer(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


def user_computer_image_path(instance, filename):
    """Generuje unikalną ścieżkę dla zdjęcia komputera"""
    # Pobierz rozszerzenie pliku
    ext = filename.split(".")[-1].lower()

    # Wygeneruj unikalną nazwę używając UUID
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    # Organizuj według użytkownika: user_computers/user_123/abc123def456.jpg
    return f"user_computers/user_{instance.user.id}/{unique_filename}"


class UserComputer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="computers")
    name = models.CharField(max_length=200, verbose_name="Nazwa zestawu")
    description = models.TextField(blank=True, null=True, verbose_name="Opis")

    # Komponenty - nazwy tekstowe (jak w upgraderze)
    cpu_name = models.CharField(max_length=200, verbose_name="Procesor")
    gpu_name = models.CharField(max_length=200, verbose_name="Karta graficzna")
    motherboard_name = models.CharField(max_length=200, verbose_name="Płyta główna")
    ram_name = models.CharField(max_length=200, verbose_name="Pamięć RAM")

    # Dodatkowe informacje
    psu_watt = models.IntegerField(default=500, verbose_name="Moc PSU (W)")
    ssd_size = models.IntegerField(default=512, verbose_name="Rozmiar SSD (GB)")
    hdd_size = models.IntegerField(default=0, verbose_name="Rozmiar HDD (GB)")

    # Zdjęcie
    image = models.ImageField(
        upload_to=user_computer_image_path,  # Zamiast 'user_computers/'
        blank=True,
        null=True,
        verbose_name="Zdjęcie zestawu",
    )
    # Ustawienia prywatności
    is_public = models.BooleanField(default=False, verbose_name="Publiczny zestaw")
    allow_comments = models.BooleanField(
        default=True, verbose_name="Zezwalaj na komentarze"
    )

    # Metadane
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.IntegerField(default=0, verbose_name="Liczba wyświetleń")
    likes_count = models.IntegerField(default=0, verbose_name="Liczba polubień")

    class Meta:
        verbose_name = "Komputer użytkownika"
        verbose_name_plural = "Komputery użytkowników"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def get_estimated_price(self):
        """Szacuje cenę na podstawie nazw komponentów"""

        try:
            cpu, gpu, mobo, ram = find_current_components(
                self.cpu_name, self.gpu_name, self.motherboard_name, self.ram_name
            )

            total = 0
            components = [cpu, gpu, mobo, ram]

            for component in components:
                if component and hasattr(component, "price") and component.price:
                    try:
                        total += float(component.price)
                    except (ValueError, TypeError):
                        pass

            return total
        except:
            return 0


class UserComputerLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    computer = models.ForeignKey(
        UserComputer, on_delete=models.CASCADE, related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "computer")


class UserComputerComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    computer = models.ForeignKey(
        UserComputer, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField(verbose_name="Treść komentarza")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.computer.name}"


class ComputerCase(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, null=True, blank=True
    )
    mpn = models.CharField(max_length=255, null=True, blank=True)  # Model Part Number
    ean = models.CharField(max_length=255, null=True, blank=True)
    upc = models.CharField(max_length=255, null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)  # in mm
    depth = models.IntegerField(null=True, blank=True)  # in mm
    height = models.IntegerField(null=True, blank=True)  # in mm
    motherboard = models.CharField(max_length=255, null=True, blank=True)
    power_supply = models.CharField(max_length=255, null=True, blank=True)
    supported_gpu_length = models.IntegerField(null=True, blank=True)  # in mm
    supported_cpu_cooler_height = models.IntegerField(null=True, blank=True)  # in mm
    fans_80mm = models.CharField(max_length=50, null=True, blank=True)
    fans_120mm = models.CharField(max_length=50, null=True, blank=True)
    fans_140mm = models.CharField(max_length=50, null=True, blank=True)
    fans_200mm = models.CharField(max_length=50, null=True, blank=True)
    radiator_120mm = models.FloatField(null=True, blank=True)
    radiator_140mm = models.FloatField(null=True, blank=True)
    radiator_240mm = models.FloatField(null=True, blank=True)
    radiator_280mm = models.FloatField(null=True, blank=True)
    radiator_360mm = models.FloatField(null=True, blank=True)
    disk_25 = models.IntegerField(null=True, blank=True)
    disk_35 = models.IntegerField(null=True, blank=True)
    disk_25_35 = models.IntegerField(null=True, blank=True)
    disk_525 = models.IntegerField(null=True, blank=True)
    primary_color = models.CharField(max_length=255, null=True, blank=True)
    window = models.BooleanField(null=True, blank=True)
    dust_filter = models.BooleanField(null=True, blank=True)
    cable_management = models.BooleanField(null=True, blank=True)
    noise_isolation = models.BooleanField(null=True, blank=True)
    product_page = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class CPU(models.Model):
    part_number = models.CharField(max_length=255, null=True, blank=True)
    brand = models.CharField(max_length=255, null=True, blank=True)
    model = models.CharField(max_length=255)
    rank = models.IntegerField(null=True, blank=True)
    benchmark = models.FloatField(null=True, blank=True)
    samples = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    frequency = models.CharField(max_length=255, null=True, blank=True)
    cores = models.CharField(max_length=255, null=True, blank=True)
    socket = models.CharField(max_length=255, null=True, blank=True)
    unlocked_multiplier = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.model


class CPUCooler(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, null=True, blank=True
    )
    mpn = models.CharField(max_length=255, null=True, blank=True)
    ean = models.CharField(max_length=255, null=True, blank=True)
    upc = models.CharField(max_length=255, null=True, blank=True)
    supported_sockets = models.CharField(max_length=255, null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)  # in mm
    tdp = models.IntegerField(null=True, blank=True)  # in W
    fans_80mm = models.IntegerField(null=True, blank=True)
    fans_92mm = models.IntegerField(null=True, blank=True)
    fans_120mm = models.IntegerField(null=True, blank=True)
    fans_140mm = models.IntegerField(null=True, blank=True)
    fans_200mm = models.IntegerField(null=True, blank=True)
    additional_fan_support = models.BooleanField(null=True, blank=True)
    product_page = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class GPU(models.Model):
    title = models.CharField(max_length=255, blank=True)
    brand = models.CharField(max_length=255, null=True, blank=True)
    model = models.CharField(max_length=255, null=True, blank=True)
    rank = models.FloatField(null=True, blank=True)
    benchmark = models.FloatField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    chipset = models.CharField(max_length=255, null=True, blank=True)
    ram = models.CharField(max_length=255, null=True, blank=True)  # VRAM karty
    dlugosc = models.CharField(
        max_length=255, null=True, blank=True
    )  # długość fizyczna
    taktowanie = models.CharField(max_length=255, null=True, blank=True)
    part_number = models.CharField(max_length=255, null=True, blank=True)
    samples = models.FloatField(null=True, blank=True)
    img_src = models.URLField(null=True, blank=True)
    link_produkt_href = models.URLField(null=True, blank=True)
    recomended_ps = models.CharField(max_length=255, null=True, blank=True)

    @property
    def display_name(self):
        """Zwraca najlepszą dostępną nazwę"""
        if self.title and self.title.strip():
            return self.title.strip()

        parts = []
        if self.brand and self.brand.strip():
            parts.append(self.brand.strip())
        if self.model and self.model.strip():
            parts.append(self.model.strip())

        if parts:
            return " ".join(parts)

        return f"GPU {self.id}"

    def _extract_vram_from_name(self, name_text):
        """Wyciąga ilość VRAM z nazwy karty graficznej"""
        if not name_text:
            return None

        import re

        # Wzorce dla VRAM (pamięć karty graficznej)
        vram_patterns = [
            r"(\d+)\s*GB(?!\s*DDR)",  # XGB ale nie "GB DDR" (to RAM systemowy)
            r"(\d+)\s*gb(?!\s*ddr)",  # Xgb ale nie "gb ddr"
            r"(\d+)G\b(?!B\s*DDR)",  # XG ale nie "GB DDR"
        ]

        for pattern in vram_patterns:
            matches = re.findall(pattern, name_text, re.IGNORECASE)
            if matches:
                # Weź pierwszą znalezioną wartość
                vram_size = int(matches[0])
                # Typowe rozmiary VRAM kart graficznych
                if vram_size in [1, 2, 3, 4, 6, 8, 10, 11, 12, 16, 20, 24, 32]:
                    return f"{vram_size}GB"

        return None

    def _is_length_value(self, value):
        """Sprawdza czy wartość to długość (zawiera mm, cm itp.)"""
        if not value:
            return False

        length_indicators = ["mm", "cm", "inch", '"', "długość", "length"]
        value_lower = str(value).lower()

        return any(indicator in value_lower for indicator in length_indicators)

    def save(self, *args, **kwargs):
        # 1. Wypełnij title jeśli pusty
        if not self.title or not self.title.strip():
            parts = []
            if self.brand and self.brand.strip():
                parts.append(self.brand.strip())
            if self.model and self.model.strip():
                parts.append(self.model.strip())

            if parts:
                self.title = " ".join(parts)

        # 2. Sprawdź czy RAM zawiera błędne dane (długość)
        if self.ram and self._is_length_value(self.ram):
            print(
                f"[WARNING] GPU {self.id}: RAM zawiera długość '{self.ram}' - czyszczę"
            )
            self.ram = None

        # 3. Wypełnij VRAM jeśli pusty
        if not self.ram or not self.ram.strip():
            # Spróbuj wyciągnąć z title
            vram_from_title = self._extract_vram_from_name(self.title)
            if vram_from_title:
                self.ram = vram_from_title
                print(f"[INFO] GPU {self.id}: VRAM z title: {vram_from_title}")
            else:
                # Spróbuj z model
                vram_from_model = self._extract_vram_from_name(self.model)
                if vram_from_model:
                    self.ram = vram_from_model
                    print(f"[INFO] GPU {self.id}: VRAM z model: {vram_from_model}")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name = "Karta graficzna"
        verbose_name_plural = "Karty graficzne"


class HDD(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, null=True, blank=True
    )
    mpn = models.CharField(max_length=255, null=True, blank=True)
    ean = models.CharField(max_length=255, null=True, blank=True)
    upc = models.CharField(max_length=255, null=True, blank=True)
    form_factor = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=255, null=True, blank=True)
    rpm = models.FloatField(null=True, blank=True)
    cache = models.CharField(max_length=255, null=True, blank=True)
    product_page = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class Motherboard(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, null=True, blank=True
    )
    mpn = models.CharField(max_length=255, null=True, blank=True)
    ean = models.CharField(max_length=255, null=True, blank=True)
    upc = models.CharField(max_length=255, null=True, blank=True)
    socket = models.CharField(max_length=255, null=True, blank=True)
    chipset = models.CharField(max_length=255, null=True, blank=True)
    unlocked = models.BooleanField(null=True, blank=True)
    form_factor = models.CharField(max_length=255, null=True, blank=True)
    memory_type = models.CharField(max_length=255, null=True, blank=True)
    memory_capacity = models.CharField(max_length=255, null=True, blank=True)
    ram_slots = models.IntegerField(null=True, blank=True)
    sata = models.IntegerField(null=True, blank=True)
    vga = models.IntegerField(null=True, blank=True)
    dvi = models.FloatField(null=True, blank=True)
    display_port = models.FloatField(null=True, blank=True)
    hdmi = models.FloatField(null=True, blank=True)
    wifi = models.BooleanField(null=True, blank=True)
    integrated_graphics = models.BooleanField(null=True, blank=True)
    product_page = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class PSU(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, null=True, blank=True
    )
    mpn = models.CharField(max_length=255, null=True, blank=True)
    ean = models.CharField(max_length=255, null=True, blank=True)
    upc = models.CharField(max_length=255, null=True, blank=True)
    watt = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=255, null=True, blank=True)
    efficiency_rating = models.CharField(max_length=255, null=True, blank=True)
    product_page = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class RAM(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, null=True, blank=True
    )
    mpn = models.CharField(max_length=255, null=True, blank=True)
    ean = models.CharField(max_length=255, null=True, blank=True)
    upc = models.CharField(max_length=255, null=True, blank=True)
    ram_type = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=255, null=True, blank=True)
    clock = models.IntegerField(null=True, blank=True)
    timings = models.CharField(max_length=255, null=True, blank=True)
    sticks = models.IntegerField(null=True, blank=True)
    product_page = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class SSD(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, null=True, blank=True
    )
    mpn = models.CharField(max_length=255, null=True, blank=True)
    ean = models.CharField(max_length=255, null=True, blank=True)
    upc = models.CharField(max_length=255, null=True, blank=True)
    form_factor = models.CharField(max_length=255, null=True, blank=True)
    protocol = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=255, null=True, blank=True)
    nand = models.CharField(max_length=255, null=True, blank=True)
    controller = models.CharField(max_length=255, null=True, blank=True)
    product_page = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name
