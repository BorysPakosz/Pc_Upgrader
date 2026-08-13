from django.shortcuts import render, redirect
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
    AdminAction,
)
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from decimal import Decimal

from .utils import (
    find_current_components,
    check_socket_compatibility,
    generate_proposals,
    sort_proposals,
    select_top_proposals,
    parse_gb,
)
from .utils.component_search import get_better_components
from .utils.performance import prepare_comparison_data
from .utils.compatibility import get_compatible_motherboards, get_compatible_cpus
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib import messages


def index(request):
    """Strona główna"""
    return render(
        request,
        "hardware/index.html",
        {
            "case_count": ComputerCase.objects.count(),
            "cpu_count": CPU.objects.count(),
            "gpu_count": GPU.objects.count(),
            "motherboard_count": Motherboard.objects.count(),
            "ram_count": RAM.objects.count(),
            "psu_count": PSU.objects.count(),
            "cooler_count": CPUCooler.objects.count(),
            "hdd_count": HDD.objects.count(),
            "ssd_count": SSD.objects.count(),
        },
    )


def computer_cases(request):
    """Lista obudów komputerowych"""
    cases = ComputerCase.objects.all().order_by("name")

    # Filtrowanie
    producer = request.GET.get("producer")
    if producer:
        cases = cases.filter(producer__name=producer)

    motherboard = request.GET.get("motherboard")
    if motherboard:
        cases = cases.filter(motherboard__icontains=motherboard)

    window = request.GET.get("window")
    if window:
        cases = cases.filter(window=window == "true")

    paginator = Paginator(cases, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Pobranie unikalnych wartości dla filtrów
    producers = Producer.objects.filter(computercase__isnull=False).distinct()
    motherboards = ComputerCase.objects.values_list("motherboard", flat=True).distinct()

    return render(
        request,
        "hardware/cases.html",
        {
            "computer_cases": page_obj,
            "page_obj": page_obj,
            "cases": cases,
            "producers": producers,
            "motherboards": motherboards,
            "selected_producer": producer,
            "selected_motherboard": motherboard,
            "selected_window": window,
        },
    )


from django.core.paginator import Paginator


def cpus(request):
    """Lista procesorów z paginacją"""
    processors = CPU.objects.all().order_by("-benchmark", "title")

    # Filtry
    selected_brand = request.GET.get("brand")
    selected_socket = request.GET.get("socket")

    if selected_brand:
        processors = processors.filter(brand=selected_brand)
    if selected_socket:
        processors = processors.filter(socket=selected_socket)

    paginator = Paginator(processors, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Pobierz unikalne wartości dla filtrów
    brands = CPU.objects.values_list("brand", flat=True).distinct().order_by("brand")
    sockets = CPU.objects.values_list("socket", flat=True).distinct().order_by("socket")

    return render(
        request,
        "hardware/cpus.html",
        {
            "processors": page_obj,
            "page_obj": page_obj,
            "brands": brands,
            "sockets": sockets,
            "selected_brand": selected_brand,
            "selected_socket": selected_socket,
        },
    )


def gpus(request):
    """Lista kart graficznych z paginacją"""
    graphics_cards = GPU.objects.all().order_by("-benchmark", "title")

    # Filtry
    selected_brand = request.GET.get("brand")
    selected_chipset = request.GET.get("chipset")

    if selected_brand:
        graphics_cards = graphics_cards.filter(brand=selected_brand)
    if selected_chipset:
        graphics_cards = graphics_cards.filter(chipset=selected_chipset)

    paginator = Paginator(graphics_cards, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Filtry
    brands = GPU.objects.values_list("brand", flat=True).distinct().order_by("brand")
    chipsets = (
        GPU.objects.values_list("chipset", flat=True).distinct().order_by("chipset")
    )

    return render(
        request,
        "hardware/gpus.html",
        {
            "graphics_cards": page_obj,
            "page_obj": page_obj,
            "brands": brands,
            "chipsets": chipsets,
            "selected_brand": selected_brand,
            "selected_chipset": selected_chipset,
        },
    )


def rams(request):
    """Lista pamięci RAM z paginacją"""
    rams = RAM.objects.all().order_by("name")

    # Filtry
    selected_producer = request.GET.get("producer")
    selected_ram_type = request.GET.get("ram_type")

    if selected_producer:
        rams = rams.filter(producer__name=selected_producer)
    if selected_ram_type:
        rams = rams.filter(ram_type=selected_ram_type)

    # ✅ PAGINACJA
    paginator = Paginator(rams, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Filtry
    producers = Producer.objects.all().order_by("name")
    ram_types = (
        RAM.objects.values_list("ram_type", flat=True).distinct().order_by("ram_type")
    )

    return render(
        request,
        "hardware/rams.html",
        {
            "rams": page_obj,  # ✅ ZMIEŃ
            "page_obj": page_obj,  # ✅ DODAJ
            "producers": producers,
            "ram_types": ram_types,
            "selected_producer": selected_producer,
            "selected_ram_type": selected_ram_type,
        },
    )


def motherboards(request):
    """Lista płyt głównych z paginacją"""
    boards = Motherboard.objects.all().order_by("name")

    # Filtry
    selected_producer = request.GET.get("producer")
    selected_socket = request.GET.get("socket")
    selected_form_factor = request.GET.get("form_factor")

    if selected_producer:
        boards = boards.filter(producer__name=selected_producer)
    if selected_socket:
        boards = boards.filter(socket=selected_socket)
    if selected_form_factor:
        boards = boards.filter(form_factor=selected_form_factor)

    # ✅ PAGINACJA
    paginator = Paginator(boards, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Filtry
    producers = Producer.objects.all().order_by("name")
    sockets = (
        Motherboard.objects.values_list("socket", flat=True)
        .distinct()
        .order_by("socket")
    )
    form_factors = (
        Motherboard.objects.values_list("form_factor", flat=True)
        .distinct()
        .order_by("form_factor")
    )

    return render(
        request,
        "hardware/motherboards.html",
        {
            "boards": page_obj,
            "page_obj": page_obj,
            "producers": producers,
            "sockets": sockets,
            "form_factors": form_factors,
            "selected_producer": selected_producer,
            "selected_socket": selected_socket,
            "selected_form_factor": selected_form_factor,
        },
    )


def ssds(request):
    ssds = SSD.objects.all().order_by("size")

    producer = request.GET.get("producer")
    if producer:
        ssds = ssds.filter(producer__name=producer)

    protocol = request.GET.get("protocol")
    if protocol:
        ssds = ssds.filter(protocol=protocol)

    paginator = Paginator(ssds, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    producers = Producer.objects.filter(ssd__isnull=False).distinct()
    protocols = SSD.objects.values_list("protocol", flat=True).distinct()

    return render(
        request,
        "hardware/ssds.html",
        {
            "ssds": page_obj,
            "page_obj": page_obj,
            "producers": producers,
            "protocols": protocols,
            "selected_producer": producer,
            "selected_protocol": protocol,
        },
    )


def hdds(request):
    hdds = HDD.objects.all().order_by("size")

    producer = request.GET.get("producer")
    if producer:
        hdds = hdds.filter(producer__name=producer)

    form_factor = request.GET.get("form_factor")
    if form_factor:
        hdds = hdds.filter(form_factor=form_factor)

    paginator = Paginator(hdds, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    producers = Producer.objects.filter(hdd__isnull=False).distinct()
    form_factors = HDD.objects.values_list("form_factor", flat=True).distinct()

    return render(
        request,
        "hardware/hdds.html",
        {
            "hdds": page_obj,
            "page_obj": page_obj,
            "producers": producers,
            "form_factors": form_factors,
            "selected_producer": producer,
            "selected_form_factor": form_factor,
        },
    )


def psus(request):
    psus = PSU.objects.all().order_by("watt")

    producer = request.GET.get("producer")
    if producer:
        psus = psus.filter(producer__name=producer)

    efficiency = request.GET.get("efficiency_rating")
    if efficiency:
        psus = psus.filter(efficiency_rating=efficiency)

    paginator = Paginator(psus, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    producers = Producer.objects.filter(psu__isnull=False).distinct()
    efficiencies = PSU.objects.values_list("efficiency_rating", flat=True).distinct()

    return render(
        request,
        "hardware/psus.html",
        {
            "psus": page_obj,
            "page_obj": page_obj,
            "producers": producers,
            "efficiencies": efficiencies,
            "selected_producer": producer,
            "selected_efficiency": efficiency,
        },
    )


def coolers(request):
    coolers = CPUCooler.objects.all().order_by("name")

    producer = request.GET.get("producer")
    if producer:
        coolers = coolers.filter(producer__name=producer)

    socket = request.GET.get("socket")
    if socket:
        coolers = coolers.filter(supported_sockets__icontains=socket)

    paginator = Paginator(coolers, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    producers = Producer.objects.filter(cpucooler__isnull=False).distinct()
    sockets = CPUCooler.objects.values_list("supported_sockets", flat=True).distinct()

    return render(
        request,
        "hardware/coolers.html",
        {
            "coolers": page_obj,
            "page_obj": page_obj,
            "coolers": coolers,
            "producers": producers,
            "sockets": sockets,
            "selected_producer": producer,
            "selected_socket": socket,
        },
    )


from .forms import CustomUserCreationForm


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.status_code = 400
        return response


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data["password1"]

            user_auth = authenticate(
                request, username=user.username, password=raw_password
            )
            if user_auth is not None:
                login(request, user_auth)
                messages.success(
                    request, f"Konto dla {user.username} zostało utworzone!"
                )
                return redirect("hardware:login")
            messages.warning(request, "Konto utworzone. Zaloguj się ręcznie.")
            return render(
                request, "registration/register.html", {"form": form}, status=400
            )
        return render(request, "registration/register.html", {"form": form}, status=400)
    form = CustomUserCreationForm()

    return render(request, "registration/register.html", {"form": form})


def custom_logout(request):
    logout(request)
    return redirect("/")


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from .models import UserComputer, UserComputerLike, UserComputerComment


@login_required
def my_computers(request):
    """Lista komputerów użytkownika"""
    computers = UserComputer.objects.filter(user=request.user).order_by("-created_at")

    paginator = Paginator(computers, 6)  # 6 komputerów na stronę
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "hardware/my_computers.html",
        {"page_obj": page_obj, "computers": page_obj},
    )


@login_required
def add_computer(request):
    """Dodawanie nowego komputera"""
    if request.method == "POST":
        required_fields = ["name", "cpu_name", "gpu_name", "motherboard_name", "ram_name"]
        missing = [field for field in required_fields if not request.POST.get(field)]
        if missing:
            messages.error(request, "Brakuje wymaganych pól: " + ", ".join(missing))
            return render(
                request,
                "hardware/add_computer.html",
                status=400,
            )

        computer = UserComputer.objects.create(
            user=request.user,
            name=request.POST.get("name"),
            description=request.POST.get("description", ""),
            cpu_name=request.POST.get("cpu_name"),
            gpu_name=request.POST.get("gpu_name"),
            motherboard_name=request.POST.get("motherboard_name"),
            ram_name=request.POST.get("ram_name"),
            psu_watt=int(request.POST.get("psu_watt", 500)),
            ssd_size=int(request.POST.get("ssd_size", 512)),
            hdd_size=int(request.POST.get("hdd_size", 0)),
            is_public=request.POST.get("is_public") == "on",
            allow_comments=request.POST.get("allow_comments") == "on",
        )

        # Obsługa zdjęcia
        if request.FILES.get("image"):
            computer.image = request.FILES["image"]
            computer.save()

        messages.success(request, "Komputer został dodany pomyślnie!")
        return redirect("hardware:my_computers")

    return render(request, "hardware/add_computer.html")


@login_required
def edit_computer(request, computer_id):
    """Edycja komputera użytkownika"""
    computer = get_object_or_404(UserComputer, id=computer_id, user=request.user)

    if request.method == "POST":
        computer.name = request.POST.get("name")
        computer.description = request.POST.get("description", "")
        computer.cpu_name = request.POST.get("cpu_name")
        computer.gpu_name = request.POST.get("gpu_name")
        computer.motherboard_name = request.POST.get("motherboard_name")
        computer.ram_name = request.POST.get("ram_name")
        computer.psu_watt = int(request.POST.get("psu_watt", 500))
        computer.ssd_size = int(request.POST.get("ssd_size", 512))
        computer.hdd_size = int(request.POST.get("hdd_size", 0))
        computer.is_public = request.POST.get("is_public") == "on"
        computer.allow_comments = request.POST.get("allow_comments") == "on"

        if request.FILES.get("image"):
            computer.image = request.FILES["image"]

        computer.save()
        messages.success(request, "Komputer został zaktualizowany!")
        return redirect("hardware:my_computers")

    return render(request, "hardware/edit_computer.html", {"computer": computer})


@login_required
def delete_computer(request, computer_id):
    """Usuwanie komputera"""
    computer = get_object_or_404(UserComputer, id=computer_id, user=request.user)

    if request.method == "POST":
        computer.delete()
        messages.success(request, "Komputer został usunięty!")
        return redirect("hardware:my_computers")

    return render(request, "hardware/delete_computer.html", {"computer": computer})


def public_computers(request):
    """Galeria publicznych komputerów użytkowników"""
    computers = (
        UserComputer.objects.filter(is_public=True)
        .select_related("user")
        .order_by("-created_at")
    )

    # Filtrowanie
    search = request.GET.get("search")
    if search:
        computers = computers.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(user__username__icontains=search)
            | Q(cpu_name__icontains=search)
            | Q(gpu_name__icontains=search)
        )

    # Sortowanie
    sort_by = request.GET.get("sort", "newest")
    if sort_by == "popular":
        computers = computers.order_by("-views_count", "-likes_count")
    elif sort_by == "liked":
        computers = computers.order_by("-likes_count", "-views_count")
    else:  # newest
        computers = computers.order_by("-created_at")

    paginator = Paginator(computers, 12)  # 12 komputerów na stronę
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "hardware/public_computers.html",
        {
            "page_obj": page_obj,
            "computers": page_obj,
            "search": search,
            "sort_by": sort_by,
        },
    )


def computer_detail(request, computer_id):
    """Szczegóły komputera"""
    computer = get_object_or_404(UserComputer, id=computer_id)

    # Sprawdź uprawnienia
    if not computer.is_public and computer.user != request.user:
        messages.error(request, "Ten komputer jest prywatny.")
        return redirect("hardware:public_computers")

    # Zwiększ licznik wyświetleń
    if request.user != computer.user:
        computer.views_count += 1
        computer.save(update_fields=["views_count"])

    # Sprawdź czy użytkownik polubił
    user_liked = False
    if request.user.is_authenticated:
        user_liked = UserComputerLike.objects.filter(
            user=request.user, computer=computer
        ).exists()

    # Komentarze
    comments = computer.comments.select_related("user").order_by("-created_at")

    cpu = getattr(computer, "cpu", None)
    gpu = getattr(computer, "gpu", None)
    mobo = getattr(computer, "motherboard", None) or getattr(computer, "mobo", None)
    ram = getattr(computer, "ram", None)
    return render(
        request,
        "hardware/computer_detail.html",
        {
            "computer": computer,
            "user_liked": user_liked,
            "comments": comments,
            "found_cpu": cpu,
            "found_gpu": gpu,
            "found_mobo": mobo,
            "found_ram": ram,
        },
    )


@login_required
def use_my_computer(request, computer_id):
    """Użyj zapisanego komputera w upgraderze"""
    computer = get_object_or_404(UserComputer, id=computer_id, user=request.user)

    # Przekieruj do upgrade_results z danymi komputera
    return render(
        request,
        "hardware/upgrade_results.html",
        {
            "show_form_only": True,
            "comparisons": [],
            "current": {
                "cpu_name": computer.cpu_name,
                "gpu_name": computer.gpu_name,
                "mobo_name": computer.motherboard_name,
                "ram_name": computer.ram_name,
                "psu": computer.psu_watt,
                "ssd": computer.ssd_size,
                "hdd": computer.hdd_size,
            },
            "budget": 5000,
            "from_saved_computer": True,
            "saved_computer": computer,
            "user_computers": [],  # ✅ DODAJ żeby nie pokazywać sekcji "Użyj zapisanego zestawu"
        },
    )


@login_required
def toggle_like(request, computer_id):
    """Polub/odlub komputer"""
    computer = get_object_or_404(UserComputer, id=computer_id)

    like, created = UserComputerLike.objects.get_or_create(
        user=request.user, computer=computer
    )

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    # Aktualizuj licznik polubień
    computer.likes_count = computer.likes.count()
    computer.save(update_fields=["likes_count"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"liked": liked, "likes_count": computer.likes_count})

    return redirect("hardware:computer_detail", computer_id=computer.id)


@login_required
def add_comment(request, computer_id):
    """Dodaj komentarz"""
    computer = get_object_or_404(UserComputer, id=computer_id)

    if not computer.allow_comments:
        messages.error(request, "Komentarze są wyłączone dla tego komputera.")
        return redirect("hardware:computer_detail", computer_id=computer.id)

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            UserComputerComment.objects.create(
                user=request.user, computer=computer, content=content
            )
            messages.success(request, "Komentarz został dodany!")

    return redirect("hardware:computer_detail", computer_id=computer.id)


from django.db.models import Q


def autocomplete(request, category):
    query = request.GET.get("q", "").lower()
    results = []

    if category == "gpu":
        results = list(
            GPU.objects.filter(title__icontains=query).values_list("title", flat=True)
        )
    elif category == "cpu":
        results = list(
            CPU.objects.filter(title__icontains=query).values_list("title", flat=True)
        )
    elif category == "ram":
        results = list(
            RAM.objects.filter(name__icontains=query).values_list("name", flat=True)
        )
    elif category == "motherboard":
        results = list(
            Motherboard.objects.filter(name__icontains=query).values_list(
                "name", flat=True
            )
        )

    return JsonResponse({"results": results})


def upgrade_assistant(request):
    """Główna funkcja asystenta ulepszeń"""

    if request.method == "GET":
        # Sprawdź czy to kopiowanie z innego komputera
        from_copy = request.GET.get("from_copy") == "true"

        # Sprawdź czy użytkownik ma zapisane komputery
        user_computers = []
        if request.user.is_authenticated:
            user_computers = UserComputer.objects.filter(user=request.user).order_by(
                "-created_at"
            )[:5]

        # GET request - pokaż pusty formularz w upgrade_results.html
        return render(
            request,
            "hardware/upgrade_results.html",
            {
                "show_form_only": True,
                "comparisons": [],
                "current": {},
                "budget": 5000,
                "user_computers": user_computers,
                "from_copy": from_copy,  # ✅ DODAJ flagę
            },
        )

    if request.method == "POST":
        # Pobierz dane od użytkownika
        budget = Decimal(request.POST.get("budget", 0))
        cpu_name = request.POST.get("cpu_name")
        gpu_name = request.POST.get("gpu_name")
        mobo_name = request.POST.get("mobo_name")
        ram_name = request.POST.get("ram_name", "")

        psu_watt = int(request.POST.get("psu_watt", 0))
        ssd_size = int(request.POST.get("ssd_size", 0))
        hdd_size = int(request.POST.get("hdd_size", 0))

        print(f"[DEBUG] Wyszukiwanie komponentów:")
        print(f"  CPU: '{cpu_name}'")
        print(f"  GPU: '{gpu_name}'")
        print(f"  MOBO: '{mobo_name}'")
        print(f"  RAM: '{ram_name}'")

        # Znajdź obecne komponenty
        current_cpu, current_gpu, current_mobo, current_ram = find_current_components(
            cpu_name, gpu_name, mobo_name, ram_name
        )

        # SPRAWDZANIE KOMPATYBILNOŚCI SOCKETÓW
        if current_cpu and current_mobo:
            if not check_socket_compatibility(current_cpu.socket, current_mobo.socket):
                return render(
                    request,
                    "hardware/upgrade_results.html",
                    {
                        "error": f"Niekompatybilne sockety w Twoim zestawie: CPU {current_cpu.socket} ≠ Płyta {current_mobo.socket}. Sprawdź poprawność nazw komponentów.",
                        "show_form_only": True,
                        "comparisons": [],
                        "current": {
                            "cpu": current_cpu,
                            "gpu": current_gpu,
                            "ram": current_ram,
                            "psu": psu_watt,
                            "ssd": ssd_size,
                            "hdd": hdd_size,
                            "mobo": current_mobo,
                        },
                        "budget": budget,
                    },
                    status=400,
                )

        # SPRAWDZENIE KOMPONENTÓW
        missing_components = []

        if not current_cpu:
            missing_components.append(f"CPU: '{cpu_name}'")
            # Pokaż sugestie podobnych CPU
            similar_cpus = CPU.objects.filter(
                Q(title__icontains=cpu_name.split()[0])
                if cpu_name.split()
                else Q(title__icontains=cpu_name)
            )[:5]
            if similar_cpus:
                suggestions = [cpu.title for cpu in similar_cpus]
                missing_components.append(
                    f"Podobne CPU w bazie: {', '.join(suggestions[:3])}"
                )
        elif not current_cpu.benchmark:
            missing_components.append(f"CPU '{cpu_name}' nie ma benchmarku")

        if not current_gpu:
            missing_components.append(f"GPU: '{gpu_name}'")
        elif not current_gpu.benchmark:
            missing_components.append(f"GPU '{gpu_name}' nie ma benchmarku")

        if not current_mobo:
            missing_components.append(f"Płyta główna: '{mobo_name}'")

        # Sprawdź socket CPU
        if current_cpu:
            if not current_cpu.socket or current_cpu.socket.strip() == "":
                missing_components.append(
                    f"CPU '{cpu_name}' nie ma socketu i nie można go ustalić"
                )

        if missing_components:
            return render(
                request,
                "hardware/upgrade_results.html",
                {
                    "error": f"Nie znaleziono komponentów: {', '.join(missing_components)}. Sprawdź pisownię nazw.",
                    "show_form_only": True,
                    "comparisons": [],
                    "current": {},
                    "budget": budget,
                },
                status=400,
            )

        print(f"[INFO] ✅ Znalezione komponenty:")
        print(
            f"  CPU: {current_cpu.title} (socket: {current_cpu.socket}, benchmark: {current_cpu.benchmark})"
        )
        print(f"  GPU: {current_gpu.title} (benchmark: {current_gpu.benchmark})")
        print(f"  MOBO: {current_mobo.name} (socket: {current_mobo.socket})")

        # Znajdź lepsze komponenty
        (
            better_cpus,
            better_gpus,
            better_rams,
            better_mobos,
            better_ssds,
            better_hdds,
        ) = get_better_components(
            current_cpu,
            current_gpu,
            current_mobo,
            current_ram,
            ssd_size,
            hdd_size,
            budget,
        )

        # Generuj propozycje
        if current_ram:
            ram_size = parse_gb(current_ram.size) or 16
            ram_clock = current_ram.clock or 3200
        else:
            ram_size = 16
            ram_clock = 3200

        proposals = generate_proposals(
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
        )

        # Sortuj i wybierz najlepsze propozycje
        proposals = sort_proposals(
            proposals, current_cpu, current_gpu, ram_size, ssd_size, hdd_size
        )
        top_proposals = select_top_proposals(proposals)

        # Przygotuj dane do porównania
        comparison_data = prepare_comparison_data(
            top_proposals,
            current_cpu,
            current_gpu,
            current_mobo,
            current_ram,
            ssd_size,
            hdd_size,
        )

        return render(
            request,
            "hardware/upgrade_results.html",
            {
                "comparisons": comparison_data,
                "budget": budget,
                "show_form_only": False,
                "current": {
                    "cpu": current_cpu,
                    "gpu": current_gpu,
                    "ram": current_ram,
                    "psu": psu_watt,
                    "ssd": ssd_size,
                    "hdd": hdd_size,
                    "mobo": current_mobo,
                    # Dodaj nazwy dla możliwości zapisania
                    "cpu_name": cpu_name,
                    "gpu_name": gpu_name,
                    "mobo_name": mobo_name,
                    "ram_name": ram_name,
                },
            },
        )

    # Fallback dla innych metod HTTP
    return render(
        request,
        "hardware/upgrade_results.html",
        {"show_form_only": True, "comparisons": [], "current": {}, "budget": 5000},
    )


def check_compatibility(request):
    """API endpoint do sprawdzania kompatybilności socketów"""
    if request.method == "GET":
        cpu_id = request.GET.get("cpu_id")
        motherboard_id = request.GET.get("motherboard_id")

        if not cpu_id or not motherboard_id:
            return JsonResponse(
                {
                    "compatible": False,
                    "message": "Brak parametrów cpu_id lub motherboard_id",
                },
                status=400,
            )

        try:
            cpu = CPU.objects.get(id=cpu_id)
            motherboard = Motherboard.objects.get(id=motherboard_id)

            compatible = check_socket_compatibility(cpu.socket, motherboard.socket)

            if not compatible:
                message = f"Niekompatybilne sockety: CPU {cpu.socket} ≠ Płyta {motherboard.socket}"
            else:
                message = f"Kompatybilne: {cpu.socket} = {motherboard.socket}"

            return JsonResponse(
                {
                    "compatible": compatible,
                    "message": message,
                    "cpu_socket": cpu.socket,
                    "motherboard_socket": motherboard.socket,
                }
            )

        except (CPU.DoesNotExist, Motherboard.DoesNotExist):
            return JsonResponse(
                {"compatible": False, "message": "Komponenty nie znalezione"},
                status=404,
            )

    return JsonResponse({"compatible": False, "message": "Nieobsługiwana metoda"}, status=405)


def get_compatible_components(request):
    """API endpoint do pobierania kompatybilnych komponentów"""
    if request.method == "GET":
        component_type = request.GET.get("type")  # 'cpu' lub 'motherboard'
        component_id = request.GET.get("id")

        if not component_type or not component_id:
            return JsonResponse({"components": []})

        try:
            if component_type == "cpu":
                cpu = CPU.objects.get(id=component_id)
                compatible_mobos = get_compatible_motherboards(cpu.socket)
                components = [
                    {"id": mobo.id, "name": mobo.name, "socket": mobo.socket}
                    for mobo in compatible_mobos[:50]
                ]
            elif component_type == "motherboard":
                motherboard = Motherboard.objects.get(id=component_id)
                compatible_cpus = get_compatible_cpus(motherboard.socket)
                components = [
                    {"id": cpu.id, "name": cpu.title, "socket": cpu.socket}
                    for cpu in compatible_cpus[:50]
                ]
            else:
                components = []

            return JsonResponse({"components": components})

        except (CPU.DoesNotExist, Motherboard.DoesNotExist):
            return JsonResponse({"components": []})

    return JsonResponse({"components": []})


def component_details_api(request, category):
    """Endpoint zwracający pełne dane komponentów dla autocomplete"""
    query = request.GET.get("q", "").lower()
    results = []

    if category == "cpu":
        cpus = CPU.objects.filter(
            Q(title__icontains=query)
            | Q(model__icontains=query)
            | Q(brand__icontains=query)
        ).select_related()[:20]

        results = [
            {
                "id": cpu.id,
                "name": cpu.title or cpu.model,
                "model": cpu.model,
                "socket": cpu.socket,
                "cores": cpu.cores,
                "frequency": cpu.frequency,
                "benchmark": cpu.benchmark,
                "price": float(cpu.price) if cpu.price else None,
                "brand": cpu.brand,
            }
            for cpu in cpus
        ]

    elif category == "gpu":
        gpus = GPU.objects.filter(
            Q(title__icontains=query)
            | Q(model__icontains=query)
            | Q(brand__icontains=query)
        ).select_related()[:20]

        results = [
            {
                "id": gpu.id,
                "title": gpu.title,
                "model": gpu.model,
                "brand": gpu.brand,
                "chipset": gpu.chipset,
                "ram": gpu.ram,
                "benchmark": gpu.benchmark,
                "price": float(gpu.price) if gpu.price else None,
                "recomended_ps": gpu.recomended_ps,
            }
            for gpu in gpus
        ]

    elif category == "motherboard":
        mobos = Motherboard.objects.filter(
            Q(name__icontains=query) | Q(producer__name__icontains=query)
        ).select_related("producer")[:20]

        results = [
            {
                "id": mobo.id,
                "name": mobo.name,
                "socket": mobo.socket,
                "chipset": mobo.chipset,
                "form_factor": mobo.form_factor,
                "memory_type": mobo.memory_type,
                "memory_capacity": mobo.memory_capacity,
                "price": float(mobo.price) if mobo.price else None,
                "producer": mobo.producer.name if mobo.producer else None,
            }
            for mobo in mobos
        ]
    elif category == "ram":
        components = RAM.objects.filter(
            Q(name__icontains=query)
            | Q(size__icontains=query)
            | Q(ram_type__icontains=query),
            price__isnull=False,
            price__gt=0,
        ).order_by("price")[:20]

        results = []
        for ram in components:
            results.append(
                {
                    "id": ram.id,
                    "name": ram.name,
                    "title": ram.name,
                    "size": ram.size,
                    "clock": ram.clock,
                    "ram_type": ram.ram_type,
                    "price": float(ram.price) if ram.price else None,
                }
            )
    else:
        return JsonResponse({"error": "Invalid category"}, status=400)

    return JsonResponse({"results": results})


from django.http import JsonResponse
from django.template.loader import render_to_string


def component_modal_details(request):
    """Zwraca szczegóły komponentu w formacie JSON dla modala"""
    component_type = request.GET.get("type")
    component_id = request.GET.get("id")

    try:
        if component_type == "CPU":
            component = CPU.objects.get(id=component_id)
            template = "hardware/component_details/cpu_details.html"
        elif component_type == "GPU":
            component = GPU.objects.get(id=component_id)
            template = "hardware/component_details/gpu_details.html"
        elif component_type == "Motherboard":
            component = Motherboard.objects.get(id=component_id)
            template = "hardware/component_details/motherboard_details.html"
        elif component_type == "RAM":
            component = RAM.objects.get(id=component_id)
            template = "hardware/component_details/ram_details.html"
        elif component_type == "SSD":
            component = SSD.objects.get(id=component_id)
            template = "hardware/component_details/ssd_details.html"
        else:
            return JsonResponse(
                {"error": f"Unknown component type: {component_type}"}, status=400
            )

        html = render_to_string(template, {"component": component})

        # ZNAJDOWANIE LINKU DO SKLEPU
        shop_link = None

        # Sprawdź różne pola z linkami
        if hasattr(component, "product_page") and component.product_page:
            shop_link = component.product_page
        elif hasattr(component, "link_produkt_href") and component.link_produkt_href:
            shop_link = component.link_produkt_href

        # Sprawdź czy link jest poprawny (zaczyna się od http)
        if shop_link and not shop_link.startswith(("http://", "https://")):
            shop_link = "https://" + shop_link

        return JsonResponse(
            {
                "html": html,
                "shop_link": shop_link,
                "component_name": getattr(component, "title", None)
                or getattr(component, "name", None)
                or str(component),
            }
        )

    except Exception as e:
        return JsonResponse({"error": f"Component not found: {str(e)}"}, status=404)


def component_autocomplete(request):
    """API endpoint do autocomplete komponentów"""
    if request.method == "GET":
        component_type = request.GET.get("type")
        query = request.GET.get("q", "").strip()

        if not component_type or not query or len(query) < 2:
            return JsonResponse({"suggestions": []})

        suggestions = []

        if component_type == "cpu":
            cpus = CPU.objects.filter(
                Q(title__icontains=query) | Q(model__icontains=query)
            ).order_by("title")[:10]

            suggestions = [
                {
                    "value": cpu.title,
                    "label": f"{cpu.title} ({cpu.socket if cpu.socket else 'Socket?'})",
                    "socket": cpu.socket,
                    "benchmark": cpu.benchmark,
                }
                for cpu in cpus
            ]

        elif component_type == "gpu":
            gpus = GPU.objects.filter(title__icontains=query).order_by("title")[:10]

            suggestions = [
                {
                    "value": gpu.title,
                    "label": f"{gpu.title} ({gpu.benchmark if gpu.benchmark else '?'} pkt)",
                    "benchmark": gpu.benchmark,
                }
                for gpu in gpus
            ]

        elif component_type == "motherboard":
            mobos = Motherboard.objects.filter(name__icontains=query).order_by("name")[
                :10
            ]

            suggestions = [
                {
                    "value": mobo.name,
                    "label": f"{mobo.name} ({mobo.socket if mobo.socket else 'Socket?'})",
                    "socket": mobo.socket,
                    "chipset": mobo.chipset,
                }
                for mobo in mobos
            ]

        elif component_type == "ram":
            rams = RAM.objects.filter(name__icontains=query).order_by("name")[:10]

            suggestions = [
                {
                    "value": ram.name,
                    "label": (
                        f"{ram.name} ({ram.size} {ram.clock}MHz)"
                        if ram.size and ram.clock
                        else ram.name
                    ),
                    "size": ram.size,
                    "clock": ram.clock,
                    "type": ram.ram_type,
                }
                for ram in rams
            ]

        return JsonResponse({"suggestions": suggestions})

    return JsonResponse({"suggestions": []})


from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def toggle_computer_visibility(request, computer_id):
    """Admin może zmienić widoczność komputera"""
    computer = get_object_or_404(UserComputer, id=computer_id)

    if request.method == "POST":
        # Przełącz widoczność
        computer.is_public = not computer.is_public
        computer.save()

        try:
            AdminAction.objects.create(
                admin=request.user,
                action="hide_computer" if not computer.is_public else "show_computer",
                target_user=computer.user,
                target_computer=f"{computer.name} (ID: {computer_id})",
                reason="Zmiana widoczności przez panel admina",
            )
        except Exception as e:
            print(f"[WARNING] Nie można zapisać akcji admina: {e}")

        status = "publiczny" if computer.is_public else "prywatny"
        messages.success(request, f'Komputer "{computer.name}" jest teraz {status}')

    return redirect("hardware:computer_detail", computer_id=computer_id)


@staff_member_required
def admin_delete_computer(request, computer_id):
    """Admin może usunąć dowolny komputer"""
    computer = get_object_or_404(UserComputer, id=computer_id)

    if request.method == "POST":
        computer_name = computer.name
        computer_owner = computer.user

        try:
            AdminAction.objects.create(
                admin=request.user,
                action="delete_computer",
                target_user=computer_owner,
                target_computer=f"{computer_name} (ID: {computer_id})",
                reason=request.POST.get("reason", "Brak podanego powodu"),
            )
        except Exception as e:
            print(f"[WARNING] Nie można zapisać akcji admina: {e}")

        computer.delete()
        messages.success(
            request,
            f'Usunięto komputer "{computer_name}" użytkownika {computer_owner.username}',
        )
        return redirect("hardware:public_computers")

    return redirect("hardware:computer_detail", computer_id=computer_id)
