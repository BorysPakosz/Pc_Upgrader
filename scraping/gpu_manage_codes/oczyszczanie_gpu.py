import pandas as pd

# Wczytaj plik CSV
df = pd.read_csv('gpu1.csv')
# Usuń dwie pierwsze kolumny i 'link_produkt'
df = df.drop(columns=[df.columns[0], df.columns[1], 'link_produkt'])

# Usuń 'Karta graficzna ' z początku 'title'
df['title'] = df['title'].str.replace(r'^Karta graficzna ', '', regex=True)

# Wyciągnij part_number z nawiasów i usuń nawiasy z title
df['part_number'] = df['title'].str.extract(r'\(([^)]*)\)')[0]  # zawartość nawiasów
df['title'] = df['title'].str.replace(r'\s*\([^)]*\)', '', regex=True)  # usuwa " (coś)"

df.to_csv('nowy_gpu.csv', index=False)
