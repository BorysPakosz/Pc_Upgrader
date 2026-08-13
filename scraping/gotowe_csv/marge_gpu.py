import pandas as pd
import re

# Wczytaj główny plik GPU
gpu_data = pd.read_csv("gpu_data.csv")

# Wczytaj plik z rekomendowaną mocą zasilacza
ps_data = pd.read_csv("gpu_ps.csv")

# Funkcja czyszcząca tytuł
def clean_title(title):
    if pd.isna(title):
        return ""
    # Usuń "Karta graficzna"
    title = re.sub(r'Karta graficzna\s*', '', title, flags=re.IGNORECASE)
    # Usuń wszystko w nawiasach
    title = re.sub(r'\s*\([^)]*\)', '', title)
    return title.strip().lower()
# Oczyść kolumnę rekomendowanej mocy zasilacza – wyciągnij tylko wartość np. "700 W"
def extract_power(value):
    if pd.isna(value):
        return ""
    match = re.search(r"(\d{2,4})\s*W", value)
    return f"{match.group(1)} W" if match else ""

# Oczyść tytuły w obu DataFrame’ach
gpu_data["clean_title"] = gpu_data["title"].apply(clean_title)
ps_data["clean_title"] = ps_data["title"].apply(clean_title)
ps_data["recomended_ps"] = ps_data["recomended_ps"].apply(extract_power)


# Połącz dane po oczyszczonych tytułach
merged = pd.merge(gpu_data, ps_data[["clean_title", "recomended_ps"]], on="clean_title", how="left")

# Usuń pomocniczą kolumnę
merged.drop(columns=["clean_title"], inplace=True)

# Posortuj po Rank (jeśli istnieje taka kolumna)
if "Rank" in merged.columns:
    merged = merged.sort_values(by="Rank", ascending=True)





# Zapisz wynik
merged.to_csv("gpu_data_with_recomended_ps.csv", index=False)
