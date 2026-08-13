import pandas as pd

# Wczytanie plików CSV
df_processed = pd.read_csv('output_wide.csv')
df_benchmark = pd.read_csv('rating/CPU_UserBenchmarks.csv')

# Sprawdzenie dostępnych kolumn w przetworzonym pliku
print("Dostępne kolumny w pliku output_wide.csv:")
print(df_processed.columns.tolist())

# Przygotowanie kolumn do połączenia: usunięcie spacji i standaryzacja
df_processed['title_clean'] = df_processed['model_core'].str.replace(' ', '').str.lower()
df_benchmark['Model_clean'] = df_benchmark['Model'].str.replace(' ', '').str.lower()

# Połączenie danych
merged_df = pd.merge(
    df_benchmark,
    df_processed,
    how='left',
    left_on='Model_clean',
    right_on='title_clean'
)

# Lista kolumn, które chcemy uwzględnić w wynikowym pliku
# Podstawowe kolumny z benchmark
basic_columns = ['Part Number', 'brand', 'Model', 'Rank', 'Benchmark', 'Samples']

# Kolumny z przetworzonego pliku CPU
cpu_columns = [
    'title',
    'price', 
    'img-src', 
]

# Dodaj kolumny z parametrów procesora, jeśli istnieją
param_columns = [
    'frequency',       # Częstotliwość taktowania procesora
    'cores',           # Liczba rdzeni
    'threads',         # Liczba wątków
    'socket',          # Typ gniazda
    'unlocked_multiplier', # Odblokowany mnożnik
    'cache',           # Pamięć podręczna
    'architecture',    # Architektura
    'tdp',             # TDP
    'integrated_graphics', # Zintegrowany układ graficzny
    'technology_process'   # Proces technologiczny
]

# Sprawdź, które kolumny są dostępne w danych
available_param_columns = [col for col in param_columns if col in merged_df.columns]
cpu_columns.extend(available_param_columns)

# Wszystkie wybrane kolumny
all_columns = basic_columns + cpu_columns

# Wybierz tylko te kolumny, które faktycznie istnieją w merged_df
existing_columns = [col for col in all_columns if col in merged_df.columns]

# Wybór i reorganizacja kolumn
final_df = merged_df[existing_columns].rename(columns={
    'title': 'Title',
    'price': 'Price',
    'img-src': 'Image URL',
    'frequency': 'Frequency',
    'cores': 'Cores',
    'socket': 'Socket',
    'unlocked_multiplier': 'Unlocked Multiplier',
})

# Zamiana brakujących wartości na 'N/A'
final_df = final_df.fillna('N/A')

# Zapisanie wynikowego pliku CSV
final_df.to_csv('merged_cpu_data.csv', index=False)

print(f"\nPliki zostały połączone i zapisane jako 'merged_cpu_data.csv'.")
print(f"Liczba kolumn w wynikowym pliku: {len(final_df.columns)}")
print("Nazwy kolumn w wynikowym pliku:")
print(final_df.columns.tolist())