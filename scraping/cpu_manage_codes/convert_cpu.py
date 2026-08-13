import pandas as pd
import re

# 1) Wczytaj dane i oczyść nazwy kolumn
df = pd.read_csv('cpu (1).csv', encoding='utf-8')
df.columns = df.columns.str.strip()

# 2) Usuń niepotrzebne kolumny (ignorujemy błędy, jeśli którejś nie ma)
df = df.drop(columns=['web-scraper-order', 'web-scraper-start-url'], errors='ignore')

# 3) Wyciągnij informacje z tytułu
# Wyciągamy markę (AMD/Intel)
df['brand'] = df['title'].str.extract(r'^Procesor\s+(AMD|Intel)', expand=False)
# Wyciągamy rdzeń modelu
regex = r'^Procesor\s+(?:AMD|Intel)\s+([^,]+),'
df['model_core'] = df['title'].str.extract(regex, expand=False)
# Wyciągamy częstotliwość z tytułu
df['frequency_title'] = df['title'].str.extract(r',\s*(\d+(?:\.\d+)?\s*GHz)', expand=False)
# Wyciągamy numer modelu/part number z tytułu jeśli istnieje
df['part_number'] = df['title'].str.extract(r'\(([^)]+)\)'
, expand=False)

# 4) Funkcja do parsowania parametrów - poprawiona
def parse_params(params_raw):
    d = {}
    if not isinstance(params_raw, str):
        return d
    
    # Usuwamy nagłówek i końcówkę "Pokaż więcej"
    if 'CECHY PRODUKTU' in params_raw:
        params_raw = params_raw.replace('CECHY PRODUKTU', '')
    if 'Pokaż więcej' in params_raw:
        params_raw = params_raw.replace('Pokaż więcej', '')
    
    # Wykorzystujemy regex do wyodrębnienia par klucz-wartość
    pattern = r'([^:]+):\s*([^\n]+)'
    matches = re.findall(pattern, params_raw)
    
    for key, val in matches:
        key = key.strip()
        val = val.strip()
        # Standaryzujemy nazwy kluczy
        key = standardize_key(key)
        d[key] = val
    
    return d

# Funkcja do standaryzacji nazw kluczy
def standardize_key(key):
    key = key.lower().strip()
    
    # Mapowanie popularnych kluczy do standardowych nazw
    key_mapping = {
        'częstotliwość taktowania procesora': 'frequency',
        'liczba rdzeni': 'cores',
        'odblokowany mnożnik': 'unlocked_multiplier',
        'typ gniazda': 'socket',
        'liczba wątków': 'threads',
        'pamięć podręczna procesora': 'cache',
        'pamięć cache': 'cache',
        'pamięć podręczna': 'cache',
        'architektura': 'architecture',
        'tdp': 'tdp',
        'zintegrowany układ graficzny': 'integrated_graphics',
        'proces technologiczny': 'technology_process',
        'wynik benchmark': 'benchmark_score'
    }
    
    return key_mapping.get(key, key)

# 5) Przetwórz wszystkie wiersze
parsed_params = []
for params in df['parameters']:
    parsed = parse_params(params)
    parsed_params.append(parsed)

# 6) Utwórz DataFrame z parsowanych parametrów
params_df = pd.DataFrame(parsed_params)
print(f"Wyodrębnione kolumny parametrów: {params_df.columns.tolist()}")

# 7) Połącz z oryginałem i usuń kolumnę parameters
df_wide = pd.concat([
    df.drop(columns=['parameters']), 
    params_df
], axis=1)

# 8) Formatowanie ceny - usunięcie " zł" i konwersja do liczby
if 'price' in df_wide.columns:
    df_wide['price_numeric'] = df_wide['price'].str.extract(r'([\d\s]+,\d+)').iloc[:, 0]
    df_wide['price_numeric'] = df_wide['price_numeric'].str.replace(' ', '').str.replace(',', '.').astype(float)

# 9) Sprawdź wynik
print(f"\nRozmiar wynikowego DataFrame: {df_wide.shape}")
print(f"Liczba kolumn: {len(df_wide.columns)}")
print(f"Nazwy kolumn: {df_wide.columns.tolist()}")

# 10) Zapisz wynik
df_wide.to_csv('output_wide.csv', index=False, encoding='utf-8')
print("\nZapisano output_wide.csv")