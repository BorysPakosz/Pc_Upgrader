import pandas as pd
import os
import re

# === KONFIGURACJA ===
folder_path = "ostateczne csv/"  # <- <- ZMIEŃ na ścieżkę do folderu z plikami CSV
usd_to_pln = 3.77  # <- <- AKTUALNY KURS DOLARA

# Funkcja do konwersji wartości w dolarach na złotówki
def convert_price_usd_to_pln(price_str):
    if pd.isna(price_str):
        return price_str
    match = re.search(r"\$([\d.,]+)", str(price_str))
    if match:
        usd_value = float(match.group(1).replace(",", ""))
        pln_value = usd_value * usd_to_pln
        return f"{pln_value:.2f} zł"
    return price_str

# Iteracja po wszystkich plikach CSV w folderze
for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(folder_path, filename)
        print(f"Przetwarzanie: {filename}")
        
        try:
            df = pd.read_csv(file_path)

            if "Price" in df.columns:
                df["Price"] = df["Price"].apply(convert_price_usd_to_pln)
                df.to_csv(file_path, index=False)
                print(f"Zmieniono ceny w pliku: {filename}")
            else:
                print(f"⚠️ Kolumna 'Price' nie istnieje w pliku: {filename}")
        
        except Exception as e:
            print(f"❌ Błąd przy przetwarzaniu {filename}: {e}")
