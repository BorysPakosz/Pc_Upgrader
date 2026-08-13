# 🖥️ Pc Upgrader – Django App

Aplikacja webowa wspierająca ulepszanie komputera, stworzona we frameworku Django. Projekt zrealizowany w ramach pracy inżynierskiej.

## ✅ Wymagania wstępne

- Python 3.10+
- [Pipenv](https://pipenv.pypa.io/en/latest/)

---

## 🚀 Szybki start

### 1. Sklonuj repozytorium
```bash
git clone [https://github.com/BorysPakosz/Praca-inz.git](https://github.com/BorysPakosz/Praca-inz.git)
cd Praca-inz/Pc_upgrader/pcassistant
```
*(Upewnij się, że jesteś w folderze zawierającym plik `manage.py`)*

### 2. Utwórz i aktywuj środowisko wirtualne
Zainstaluj wszystkie potrzebne zależności przy pomocy Pipenv:
```bash
pipenv install
pipenv shell
```

### 3. Skonfiguruj zmienne środowiskowe (.env)
Aplikacja wymaga pliku konfiguracyjnego z poświadczeniami. W głównym katalogu projektu (obok pliku `manage.py`) utwórz plik o nazwie `.env` i uzupełnij go swoimi danymi:

```text
SECRET_KEY=twoj_tajny_klucz_django
DEBUG=True
EMAIL_USER=twoj_email@gmail.com
EMAIL_PASS=twoje_haslo_aplikacji
```

### 4. Wykonaj migracje bazy danych
Repozytorium nie zawiera lokalnej bazy danych. Przed pierwszym uruchomieniem musisz wygenerować czystą bazę:
```bash
python manage.py migrate
```

### 5. Zaimportuj podzespoły komputerowe (Baza Wiedzy)
Aby aplikacja miała na czym pracować, załaduj początkową bazę części (procesory, karty graficzne itp.) z plików CSV do bazy danych:
```bash
python import_data.py
```

### 6. Uruchom serwer
```bash
python manage.py runserver
```
Aplikacja będzie dostępna pod adresem: http://127.0.0.1:8000

---

## ⚙️ Przydatne komendy

- **Tworzenie konta administratora (dostęp do panelu /admin):**
```bash
python manage.py createsuperuser
```

- **Aktualizacja struktury bazy danych (po zmianach w modelach):**
```bash
python manage.py makemigrations
python manage.py migrate
```