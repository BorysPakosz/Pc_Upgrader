import os

import django
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Ensure Django is configured even if pytest.ini is ignored (e.g. when running with a wrong flag).
if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pcassistant.settings")
    django.setup()


@pytest.fixture
def test_user(db):
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username="selenium_user",
        email="selenium@localhost.com",
        defaults={"password": "TestPassword123!"},
    )
    user.set_password("TestPassword123!")
    user.save()
    return user


@pytest.fixture
def driver(live_server):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1280,900")
    drv = webdriver.Chrome(options=opts)
    drv.base_url = live_server.url  # wygodny alias
    yield drv
    drv.quit()


def pytest_configure(config):
    # Register markers to avoid UnknownMark warnings when pytest.ini is skipped.
    config.addinivalue_line("markers", "unit: szybkie testy jednostkowe bez bazy")
    config.addinivalue_line("markers", "db: testy Django z baza danych")
    config.addinivalue_line("markers", "e2e: testy end-to-end (Selenium)")
