import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker


@pytest.mark.db
@pytest.mark.django_db
def test_register_creates_user(client):
    resp = client.post(
        reverse("hardware:register"),
        data={
            "username": "janek",
            "email": "janek@example.com",
            "password1": "Abcdef123!",
            "password2": "Abcdef123!",
        },
        follow=True,
    )

    assert resp.status_code == 200
    user = get_user_model().objects.filter(username="janek").first()
    assert user is not None


@pytest.mark.db
@pytest.mark.django_db
def test_register_rejects_weak_password(client):
    resp = client.post(
        reverse("hardware:register"),
        data={
            "username": "basia",
            "email": "basia@example.com",
            "password1": "123",
            "password2": "123",
        },
    )

    assert resp.status_code == 400
    assert not get_user_model().objects.filter(username="basia").exists()


@pytest.mark.db
@pytest.mark.django_db
def test_login_and_logout_flow(client, django_user_model):
    django_user_model.objects.create_user(
        username="anna", email="anna@example.com", password="Abcdef123!"
    )

    resp = client.post(
        reverse("hardware:login"),
        data={"username": "anna", "password": "Abcdef123!"},
        follow=True,
    )
    assert resp.status_code == 200
    assert resp.wsgi_request.user.is_authenticated

    resp = client.get(reverse("hardware:logout"), follow=True)
    assert resp.status_code == 200
    assert not resp.wsgi_request.user.is_authenticated


@pytest.mark.db
@pytest.mark.django_db
def test_login_rejects_invalid_credentials(client, django_user_model):
    django_user_model.objects.create_user(
        username="adam", email="adam@example.com", password="Abcdef123!"
    )

    resp = client.post(
        reverse("hardware:login"),
        data={"username": "adam", "password": "WrongPass123"},
    )

    assert resp.status_code == 400
    assert not resp.wsgi_request.user.is_authenticated


@pytest.mark.db
@pytest.mark.django_db
def test_add_computer_creates_public_entry(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="arek", email="arek@example.com", password="Abcdef123!"
    )
    client.login(username="arek", password="Abcdef123!")

    resp = client.post(
        reverse("hardware:add_computer"),
        data={
            "name": "test_pc",
            "description": "opis",
            "cpu_name": "CPU",
            "gpu_name": "GPU",
            "motherboard_name": "MOBO",
            "ram_name": "RAM",
            "is_public": "on",
        },
        follow=True,
    )
    assert resp.status_code == 200

    from hardware.models import UserComputer

    comp = UserComputer.objects.filter(name="test_pc", user=user).first()
    assert comp is not None
    assert comp.is_public is True


@pytest.mark.db
@pytest.mark.django_db
def test_like_toggle_changes_count(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="arek", email="arek@example.com", password="Abcdef123!"
    )
    client.login(username="arek", password="Abcdef123!")

    computer = baker.make("hardware.UserComputer", is_public=True)

    like_url = reverse("hardware:toggle_like", args=[computer.id])
    resp = client.post(like_url, follow=True)
    assert resp.status_code == 200

    computer.refresh_from_db()
    assert computer.likes.count() == 1

    client.post(like_url, follow=True)
    computer.refresh_from_db()
    assert computer.likes.count() == 0


@pytest.mark.db
@pytest.mark.django_db
def test_add_comment_appears(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="ola", email="ola@example.com", password="Abcdef123!"
    )
    client.login(username="ola", password="Abcdef123!")
    computer = baker.make("hardware.UserComputer", is_public=True)

    resp = client.post(
        reverse("hardware:add_comment", args=[computer.id]),
        data={"content": "super maszyna"},
        follow=True,
    )

    assert resp.status_code == 200
    computer.refresh_from_db()
    assert computer.comments.filter(content__icontains="super").exists()


@pytest.mark.db
@pytest.mark.django_db
def test_check_compatibility_flags_mismatch(client):
    cpu = baker.make("hardware.CPU", socket="AM4")
    mobo = baker.make("hardware.Motherboard", socket="LGA1700")

    resp = client.get(
        reverse("hardware:check_compatibility"),
        data={"cpu_id": cpu.id, "motherboard_id": mobo.id},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["compatible"] is False


@pytest.mark.db
@pytest.mark.django_db
def test_check_compatibility_requires_parameters(client):
    resp = client.get(reverse("hardware:check_compatibility"))

    assert resp.status_code == 400
    assert resp.json()["compatible"] is False


@pytest.mark.db
@pytest.mark.django_db
def test_check_compatibility_returns_404_for_missing_parts(client):
    resp = client.get(
        reverse("hardware:check_compatibility"),
        data={"cpu_id": 9999, "motherboard_id": 8888},
    )

    assert resp.status_code == 404
    assert resp.json()["compatible"] is False


@pytest.mark.db
@pytest.mark.django_db
def test_check_compatibility_rejects_non_get(client):
    resp = client.post(
        reverse("hardware:check_compatibility"),
        data={"cpu_id": 1, "motherboard_id": 1},
    )

    assert resp.status_code == 405
    assert resp.json()["compatible"] is False


@pytest.mark.db
@pytest.mark.django_db
def test_delete_computer_removes_owned_record(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="kasia", email="kasia@example.com", password="Abcdef123!"
    )
    client.login(username="kasia", password="Abcdef123!")
    computer = baker.make("hardware.UserComputer", user=user, is_public=True)

    resp = client.post(reverse("hardware:delete_computer", args=[computer.id]), follow=True)
    assert resp.status_code == 200

    from hardware.models import UserComputer

    assert not UserComputer.objects.filter(id=computer.id).exists()


@pytest.mark.db
@pytest.mark.django_db
def test_component_autocomplete_cpu_returns_suggestion(client):
    cpu = baker.make("hardware.CPU", title="Ryzen 5 5600X", socket="AM4", benchmark=100)

    resp = client.get(reverse("hardware:component_autocomplete"), data={"type": "cpu", "q": "Ry"})

    assert resp.status_code == 200
    data = resp.json()
    assert any(s["value"] == cpu.title for s in data.get("suggestions", []))


@pytest.mark.db
@pytest.mark.django_db
def test_component_autocomplete_gpu_returns_suggestion(client):
    gpu = baker.make("hardware.GPU", title="RTX 4060", benchmark=150)

    resp = client.get(reverse("hardware:component_autocomplete"), data={"type": "gpu", "q": "406"})
    assert resp.status_code == 200
    data = resp.json()
    assert any("RTX 4060" in s["label"] for s in data.get("suggestions", []))


@pytest.mark.db
@pytest.mark.django_db
def test_component_autocomplete_ram_returns_suggestion(client):
    ram = baker.make("hardware.RAM", name="Corsair Vengeance", ram_type="DDR4")
    resp = client.get(reverse("hardware:component_autocomplete"), data={"type": "ram", "q": "Corsair"})
    assert resp.status_code == 200
    assert any("Corsair" in s["label"] for s in resp.json().get("suggestions", []))


@pytest.mark.db
@pytest.mark.django_db
def test_component_autocomplete_requires_min_length(client):
    resp = client.get(reverse("hardware:component_autocomplete"), data={"type": "gpu", "q": "x"})
    assert resp.status_code == 200
    assert resp.json() == {"suggestions": []}


@pytest.mark.db
@pytest.mark.django_db
def test_upgrade_assistant_get_shows_form(client):
    resp = client.get(reverse("hardware:upgrade"))
    assert resp.status_code == 200
    assert resp.context[0].get("show_form_only") is True


@pytest.mark.db
@pytest.mark.django_db
def test_upgrade_assistant_post_success_flow(client):
    cpu = baker.make("hardware.CPU", title="Test CPU", socket="AM4", benchmark=100)
    gpu = baker.make("hardware.GPU", title="Test GPU", benchmark=150)
    mobo = baker.make("hardware.Motherboard", name="Test MOBO", socket="AM4")
    ram = baker.make("hardware.RAM", name="Test RAM", size="16 GB", clock=3200)

    resp = client.post(
        reverse("hardware:upgrade"),
        data={
            "budget": "5000",
            "cpu_name": cpu.title,
            "gpu_name": gpu.title,
            "mobo_name": mobo.name,
            "ram_name": ram.name,
            "psu_watt": 650,
            "ssd_size": 512,
            "hdd_size": 0,
        },
    )

    assert resp.status_code == 200
    assert resp.context[0].get("show_form_only") is False


@pytest.mark.db
@pytest.mark.django_db
def test_upgrade_assistant_post_missing_components_shows_error(client):
    resp = client.post(
        reverse("hardware:upgrade"),
        data={
            "budget": "3000",
            "cpu_name": "",
            "gpu_name": "Missing GPU",
            "mobo_name": "",
            "ram_name": "",
            "psu_watt": 400,
            "ssd_size": 256,
            "hdd_size": 0,
        },
    )

    assert resp.status_code == 400
    assert resp.context[0].get("show_form_only") is True
    assert "error" in resp.context[0]


@pytest.mark.db
@pytest.mark.django_db
def test_add_computer_missing_required_fields_returns_400(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="aga", email="aga@example.com", password="Abcdef123!"
    )
    client.login(username="aga", password="Abcdef123!")

    resp = client.post(
        reverse("hardware:add_computer"),
        data={
            # brak nazwy oraz cpu_name
            "gpu_name": "RTX 3060",
            "motherboard_name": "B560",
            "ram_name": "16GB",
        },
    )

    assert resp.status_code == 400
