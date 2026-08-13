from django.urls import path
from . import views

app_name = "hardware"

urlpatterns = [
    # Autocomplete API (stary, działający)
    path(
        "api/components/<str:category>/",
        views.component_details_api,
        name="component_details_api",
    ),
    # Modal szczegółów (nowy)
    path(
        "component-details/",
        views.component_modal_details,
        name="component_modal_details",
    ),
    path("api/autocomplete/<str:category>/", views.autocomplete, name="autocomplete"),
    path("", views.index, name="index"),
    path("cases/", views.computer_cases, name="cases"),
    path("cpus/", views.cpus, name="cpus"),
    path("gpus/", views.gpus, name="gpus"),
    path("motherboards/", views.motherboards, name="motherboards"),
    path("rams/", views.rams, name="rams"),
    path("ssds/", views.ssds, name="ssds"),
    path("hdds/", views.hdds, name="hdds"),
    path("psus/", views.psus, name="psus"),
    path("coolers/", views.coolers, name="coolers"),
    path("upgrade/", views.upgrade_assistant, name="upgrade"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        views.CustomLoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", views.custom_logout, name="logout"),
    path("check-compatibility/", views.check_compatibility, name="check_compatibility"),
    path(
        "get-compatible-components/",
        views.get_compatible_components,
        name="get_compatible_components",
    ),
    # Komputery użytkowników
    path("my-computers/", views.my_computers, name="my_computers"),
    path("add-computer/", views.add_computer, name="add_computer"),
    path("edit-computer/<int:computer_id>/", views.edit_computer, name="edit_computer"),
    path(
        "delete-computer/<int:computer_id>/",
        views.delete_computer,
        name="delete_computer",
    ),
    path("use-computer/<int:computer_id>/", views.use_my_computer, name="use_computer"),
    # Galeria publicznych komputerów
    path("computers/", views.public_computers, name="public_computers"),
    path("computer/<int:computer_id>/", views.computer_detail, name="computer_detail"),
    path("computer/<int:computer_id>/like/", views.toggle_like, name="toggle_like"),
    path("computer/<int:computer_id>/comment/", views.add_comment, name="add_comment"),
    path(
        "component-autocomplete/",
        views.component_autocomplete,
        name="component_autocomplete",
    ),
    # Akcje admina na komputerach
    path(
        "admin/computer/<int:computer_id>/toggle-visibility/",
        views.toggle_computer_visibility,
        name="toggle_computer_visibility",
    ),
    path(
        "admin/computer/<int:computer_id>/delete/",
        views.admin_delete_computer,
        name="admin_delete_computer",
    ),
]
