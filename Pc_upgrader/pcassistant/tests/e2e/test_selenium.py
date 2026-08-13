import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.auth import get_user_model
import time


@pytest.mark.e2e
@pytest.mark.django_db
class TestUserAuthE2E:

    def test_user_registration_and_login_redirect(self, driver):
        """Rejestracja nowego użytkownika i przekierowanie do logowania"""
        driver.get(driver.base_url + "/register")

        driver.find_element(By.NAME, "username").send_keys("newuser")
        driver.find_element(By.NAME, "email").send_keys("newuser@localhost.com")
        driver.find_element(By.NAME, "password1").send_keys("SuperSecurePassword123!")
        driver.find_element(By.NAME, "password2").send_keys("SuperSecurePassword123!")

        time.sleep(0.5)
        button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
        button.click()
        time.sleep(0.5)

        assert (
            "/login" in driver.current_url
        ), "Nie przekierowano na stronę logowania po rejestracji"

    def test_user_login_and_logout(self, driver):
        """Logowanie istniejącego użytkownika"""
        User = get_user_model()
        User.objects.create_user(
            username="loginuser",
            email="login@localhost.com",
            password="SuperSecurePassword123!",
        )

        driver.get(driver.base_url)
        driver.find_element(By.CSS_SELECTOR, 'a[href="/login/"]').click()
        assert "/login" in driver.current_url

        driver.find_element(By.NAME, "username").send_keys("loginuser")
        driver.find_element(By.NAME, "password").send_keys("SuperSecurePassword123!")
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(0.5)

        # Po zalogowaniu powinno wrócić na stronę główną i pokazać link "Wyloguj"
        assert driver.base_url in driver.current_url
        logout_link = driver.find_element(By.CSS_SELECTOR, 'a[href="/logout/"]').text
        assert "Wyloguj" in logout_link
        driver.find_element(By.CSS_SELECTOR, 'a[href="/logout/"]').click()
        time.sleep(0.5)
        assert (
            driver.find_element(By.CSS_SELECTOR, 'a[href="/login/"]').text
            == "Zaloguj się"
        )

    def test_password_reset_request(self, driver):
        """Wysłanie maila z linkiem resetu hasła (bez ustawiania nowego hasła)"""
        User = get_user_model()
        User.objects.create_user(
            username="resetuser",
            email="resetuser@localhost.com",
            password="SuperSecurePassword123!",
        )

        driver.get(driver.base_url + "/login/")
        driver.find_element(By.CSS_SELECTOR, 'a[href="/password_reset/"]').click()

        assert "/password_reset/" in driver.current_url

        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys("resetuser@localhost.com")

        button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        button.click()

        wait = WebDriverWait(driver, 5)
        wait.until(EC.url_contains("/password_reset/done"))

        assert "Sprawdź skrzynkę" in driver.page_source


@pytest.mark.e2e
@pytest.mark.django_db
class TestSeleniumE2E:
    LIKE_BUTTON = (By.XPATH, '//button[contains(@class,"btn-outline-danger")]')

    def login(self, driver, username, password):
        driver.get(driver.base_url + "/login/")
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="/logout/"]'))
        )

    def create_public_computer(self, test_user):
        from hardware.models import UserComputer

        return UserComputer.objects.create(
            user=test_user,
            name="loginuser_pc",
            description="masnoni asddawqws asdadas",
            cpu_name="Procesor Intel Core i5-11400F",
            gpu_name="Asus RTX 3060 12GB TUF OC",
            motherboard_name="Gigabyte B560 HD3",
            ram_name="ADATA XPG 32GB 2400",
            is_public=True,
        )

    def wait_clickable(self, driver, locator, timeout=10):
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable(locator))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        return element

    def get_like_button(self, driver):
        return self.wait_clickable(driver, self.LIKE_BUTTON)

    def test_add_computer_visible_on_list(self, driver, test_user):
        self.login(driver, test_user.username, "TestPassword123!")

        driver.get(driver.base_url + "/add-computer/")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.NAME, "name")))
        driver.find_element(By.NAME, "name").send_keys("loginuser_pc")
        driver.find_element(By.NAME, "description").send_keys("opis")
        driver.find_element(By.NAME, "cpu_name").send_keys("Intel i5")
        driver.find_element(By.NAME, "gpu_name").send_keys("RTX 3060")
        driver.find_element(By.NAME, "motherboard_name").send_keys("B560")
        driver.find_element(By.NAME, "ram_name").send_keys("32GB")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        public_toggle = self.wait_clickable(driver, (By.NAME, "is_public"))
        driver.execute_script("arguments[0].click();", public_toggle)
        submit = self.wait_clickable(driver, (By.CSS_SELECTOR, 'button[type="submit"]'))
        driver.execute_script("arguments[0].click();", submit)

        # Wyloguj i sprawdź stronę listy
        driver.find_element(By.CSS_SELECTOR, 'a[href="/logout/"]').click()
        driver.get(driver.base_url + "/computers/")

        el = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    '//*[contains(@class,"card-title") and normalize-space()="loginuser_pc"]',
                )
            )
        )
        assert el.is_displayed(), "Karta z nazwą 'loginuser_pc' nie jest widoczna"

    def test_like_count_changes(self, driver, test_user):
        comp = self.create_public_computer(test_user)
        self.login(driver, test_user.username, "TestPassword123!")
        driver.get(driver.base_url + f"/computer/{comp.id}/")

        wait = WebDriverWait(driver, 5)
        wait.until(EC.visibility_of_element_located((By.ID, "like-count")))

        def count():
            return int(driver.find_element(By.ID, "like-count").text)

        start = count()

        self.get_like_button(driver).click()
        wait.until(lambda d: count() == start + 1)
        assert count() == start + 1

        self.get_like_button(driver).click()
        wait.until(lambda d: count() == start)
        assert count() == start

    def test_like_visual_toggle(self, driver, test_user):
        comp = self.create_public_computer(test_user)
        self.login(driver, test_user.username, "TestPassword123!")
        driver.get(driver.base_url + f"/computer/{comp.id}/")

        wait = WebDriverWait(driver, 5)
        wait.until(EC.visibility_of_element_located((By.ID, "like-count")))
        heart_icon = driver.find_element(By.ID, "like-icon")

        self.get_like_button(driver).click()
        wait.until(lambda d: "text-danger" in heart_icon.get_attribute("class"))
        assert "text-danger" in heart_icon.get_attribute("class")

        self.get_like_button(driver).click()
        wait.until(lambda d: "text-danger" not in heart_icon.get_attribute("class"))
        assert "text-danger" not in heart_icon.get_attribute("class")

    def test_like_persists_after_reload(self, driver, test_user):
        comp = self.create_public_computer(test_user)
        self.login(driver, test_user.username, "TestPassword123!")
        driver.get(driver.base_url + f"/computer/{comp.id}/")

        wait = WebDriverWait(driver, 5)
        wait.until(EC.visibility_of_element_located((By.ID, "like-count")))

        start = int(driver.find_element(By.ID, "like-count").text)
        self.get_like_button(driver).click()
        wait.until(lambda d: int(d.find_element(By.ID, "like-count").text) == start + 1)

        driver.refresh()
        wait.until(EC.visibility_of_element_located((By.ID, "like-count")))
        assert int(driver.find_element(By.ID, "like-count").text) == start + 1

    def test_add_comment_to_computer(self, driver, test_user):
        comp = self.create_public_computer(test_user)
        wait = WebDriverWait(driver, 10)

        self.login(driver, test_user.username, "TestPassword123!")
        driver.get(driver.base_url + f"/computer/{comp.id}/")

        textarea = wait.until(EC.visibility_of_element_located((By.NAME, "content")))
        textarea.send_keys("Świetny komputer!")

        form = textarea.find_element(By.XPATH, "./ancestor::form")
        button = form.find_element(By.CSS_SELECTOR, 'button[type="submit"]')

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        driver.execute_script("window.scrollBy(0, -150);")
        driver.execute_script("arguments[0].click();", button)

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//p[contains(text(), "Świetny komputer!")]')
            )
        )

        comments = driver.find_elements(
            By.XPATH, '//p[contains(text(), "Świetny komputer!")]'
        )
        assert any(c.is_displayed() for c in comments)

    def test_delete_computer_removes_from_my_list(self, driver, test_user):
        comp = self.create_public_computer(test_user)
        self.login(driver, test_user.username, "TestPassword123!")

        driver.get(driver.base_url + f"/delete-computer/{comp.id}/")
        confirm_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'form button[type="submit"]'))
        )
        driver.execute_script("arguments[0].click();", confirm_btn)
        WebDriverWait(driver, 5).until(EC.url_contains("/my-computers"))

        driver.get(driver.base_url + "/my-computers/")
        cards = driver.find_elements(
            By.XPATH,
            f'//*[contains(@class,"card-title") and normalize-space()="{comp.name}"]',
        )
        assert not any(card.is_displayed() for card in cards)
