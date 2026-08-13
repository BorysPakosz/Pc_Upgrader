# myapp/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
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
    UserComputer,
    UserComputerLike,
    UserComputerComment,
)

admin.site.register(ComputerCase)


@admin.register(CPU)
class CPUAdmin(admin.ModelAdmin):
    list_display = (
        "model",
        "brand",
        "title",
        "price",
        "socket",
        "frequency",
        "cores",
        "benchmark",
    )
    list_filter = ("brand", "socket", "unlocked_multiplier")
    search_fields = ("model", "brand", "title", "part_number")

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" width="100" />', obj.image_url)
        return "Brak obrazu"

    image_preview.short_description = "Obraz"

    readonly_fields = ("image_preview",)
    fieldsets = (
        (
            "Podstawowe informacje",
            {
                "fields": (
                    "model",
                    "brand",
                    "title",
                    "price",
                    "image_url",
                    "image_preview",
                )
            },
        ),
        (
            "Specyfikacja",
            {"fields": ("frequency", "cores", "socket", "unlocked_multiplier")},
        ),
        ("Benchmarki", {"fields": ("rank", "benchmark", "samples")}),
        ("Numery produktów", {"fields": ("part_number",), "classes": ("collapse",)}),
    )


@admin.register(CPUCooler)
class CPUCoolerAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "price", "height", "tdp")
    list_filter = ("producer", "additional_fan_support")
    search_fields = ("name", "producer__name")
    fieldsets = (
        (
            "Podstawowe informacje",
            {"fields": ("name", "producer", "price", "product_page")},
        ),
        ("Specyfikacja", {"fields": ("height", "tdp", "supported_sockets")}),
        (
            "Wentylatory",
            {
                "fields": (
                    "fans_80mm",
                    "fans_92mm",
                    "fans_120mm",
                    "fans_140mm",
                    "fans_200mm",
                    "additional_fan_support",
                )
            },
        ),
        (
            "Numery produktów",
            {"fields": ("mpn", "ean", "upc"), "classes": ("collapse",)},
        ),
    )


@admin.register(GPU)
class GPUAdmin(admin.ModelAdmin):
    list_display = ("title", "brand", "model", "price", "benchmark", "chipset")
    list_filter = ("brand", "chipset")
    search_fields = ("title", "brand", "model", "chipset")

    def image_preview(self, obj):
        if obj.img_src:
            return format_html('<img src="{}" width="100" />', obj.img_src)
        return "Brak obrazu"

    image_preview.short_description = "Obraz"

    readonly_fields = ("image_preview",)
    fieldsets = (
        (
            "Podstawowe informacje",
            {
                "fields": (
                    "title",
                    "brand",
                    "model",
                    "price",
                    "img_src",
                    "image_preview",
                    "link_produkt_href",
                )
            },
        ),
        (
            "Specyfikacja",
            {"fields": ("chipset", "ram", "dlugosc", "taktowanie", "recomended_ps")},
        ),
        ("Benchmarki", {"fields": ("rank", "benchmark", "samples")}),
        ("Numery produktów", {"fields": ("part_number",), "classes": ("collapse",)}),
    )


@admin.register(HDD)
class HDDAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "price", "size", "rpm")
    list_filter = ("producer", "rpm")
    search_fields = ("name", "producer__name")
    fieldsets = (
        (
            "Podstawowe informacje",
            {"fields": ("name", "producer", "price", "product_page")},
        ),
        ("Specyfikacja", {"fields": ("form_factor", "size", "rpm", "cache")}),
        (
            "Numery produktów",
            {"fields": ("mpn", "ean", "upc"), "classes": ("collapse",)},
        ),
    )


@admin.register(Motherboard)
class MotherboardAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "price", "socket", "chipset", "form_factor")
    list_filter = ("producer", "socket", "chipset", "form_factor", "memory_type")
    search_fields = ("name", "producer__name")
    fieldsets = (
        (
            "Podstawowe informacje",
            {"fields": ("name", "producer", "price", "product_page")},
        ),
        (
            "Specyfikacja główna",
            {"fields": ("socket", "chipset", "form_factor", "unlocked")},
        ),
        ("Pamięć", {"fields": ("memory_type", "memory_capacity", "ram_slots")}),
        ("Złącza", {"fields": ("sata", "vga", "dvi", "display_port", "hdmi")}),
        ("Cechy dodatkowe", {"fields": ("wifi", "integrated_graphics")}),
        (
            "Numery produktów",
            {"fields": ("mpn", "ean", "upc"), "classes": ("collapse",)},
        ),
    )


@admin.register(PSU)
class PSUAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "price", "watt", "efficiency_rating")
    list_filter = ("producer", "efficiency_rating")
    search_fields = ("name", "producer__name")
    fieldsets = (
        (
            "Podstawowe informacje",
            {"fields": ("name", "producer", "price", "product_page")},
        ),
        ("Specyfikacja", {"fields": ("watt", "size", "efficiency_rating")}),
        (
            "Numery produktów",
            {"fields": ("mpn", "ean", "upc"), "classes": ("collapse",)},
        ),
    )


@admin.register(RAM)
class RAMAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "price", "ram_type", "size", "clock")
    list_filter = ("producer", "ram_type", "clock")
    search_fields = ("name", "producer__name")
    fieldsets = (
        (
            "Podstawowe informacje",
            {"fields": ("name", "producer", "price", "product_page")},
        ),
        (
            "Specyfikacja",
            {"fields": ("ram_type", "size", "clock", "timings", "sticks")},
        ),
        (
            "Numery produktów",
            {"fields": ("mpn", "ean", "upc"), "classes": ("collapse",)},
        ),
    )


@admin.register(SSD)
class SSDAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "price", "form_factor", "protocol", "size")
    list_filter = ("producer", "form_factor", "protocol", "nand")
    search_fields = ("name", "producer__name")
    fieldsets = (
        (
            "Podstawowe informacje",
            {"fields": ("name", "producer", "price", "product_page")},
        ),
        (
            "Specyfikacja",
            {"fields": ("form_factor", "protocol", "size", "nand", "controller")},
        ),
        (
            "Numery produktów",
            {"fields": ("mpn", "ean", "upc"), "classes": ("collapse",)},
        ),
    )


@admin.register(UserComputer)
class UserComputerAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "is_public",
        "created_at",
        "views_count",
        "likes_count",
    ]
    list_filter = ["is_public", "created_at", "user"]
    search_fields = ["name", "user__username", "cpu_name", "gpu_name"]
    readonly_fields = ["created_at", "updated_at", "views_count", "likes_count"]

    fieldsets = (
        ("Podstawowe informacje", {"fields": ("user", "name", "description", "image")}),
        (
            "Komponenty",
            {
                "fields": (
                    "cpu_name",
                    "gpu_name",
                    "motherboard_name",
                    "ram_name",
                    "psu_watt",
                    "ssd_size",
                    "hdd_size",
                )
            },
        ),
        ("Ustawienia", {"fields": ("is_public", "allow_comments")}),
        (
            "Statystyki",
            {"fields": ("views_count", "likes_count", "created_at", "updated_at")},
        ),
    )

    actions = ["make_private", "make_public", "reset_views"]

    def make_private(self, request, queryset):
        queryset.update(is_public=False)
        self.message_user(
            request, f"Ustawiono {queryset.count()} komputerów jako prywatne."
        )

    make_private.short_description = "Ustaw jako prywatne"

    def make_public(self, request, queryset):
        queryset.update(is_public=True)
        self.message_user(
            request, f"Ustawiono {queryset.count()} komputerów jako publiczne."
        )

    make_public.short_description = "Ustaw jako publiczne"

    def reset_views(self, request, queryset):
        queryset.update(views_count=0)
        self.message_user(
            request,
            f"Zresetowano licznik wyświetleń dla {queryset.count()} komputerów.",
        )

    reset_views.short_description = "Zresetuj wyświetlenia"


@admin.register(UserComputerComment)
class UserComputerCommentAdmin(admin.ModelAdmin):
    list_display = ["user", "computer", "content_preview", "created_at"]
    list_filter = ["created_at", "user"]
    search_fields = ["user__username", "computer__name", "content"]

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Treść"


@admin.register(UserComputerLike)
class UserComputerLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "computer", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "computer__name"]
