import pandas as pd

# Wczytanie danych
cpu_data = pd.read_csv("cpu_data.csv")
cpudata = pd.read_csv("CPUData.csv")

# Przygotowanie kolumn pomocniczych do łączenia
cpu_data['clean_model'] = cpu_data['Model'].str.strip().str.lower()
cpudata['clean_name'] = cpudata['Name'].str.replace(r'(?i)\b(intel|amd)\b', '', regex=True).str.strip().str.lower()

# Wybierz tylko potrzebne kolumny z CPUData.csv
cpudata_filtered = cpudata[['clean_name', 'Base Clock', 'Turbo Clock', 'Unlocked Multiplier', 'Cores', 'Threads', 'TDP', 'Socket']]

# Usuń zbędne kolumny z cpu_data
cpu_data_filtered = cpu_data.drop(columns=['Frequency', 'Cores', 'Socket'])

# LEFT JOIN – główny zbiór to cpu_data
merged = pd.merge(
    cpu_data_filtered,
    cpudata_filtered,
    left_on='clean_model',
    right_on='clean_name',
    how='left'
)

# Usuń kolumny pomocnicze
merged = merged.drop(columns=['clean_model', 'clean_name'])

# Zapisz wynik
merged.to_csv("final_merged_cpu_data.csv", index=False)

# Podgląd kilku pierwszych wierszy
print(merged.head())
