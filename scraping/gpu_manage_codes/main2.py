import pandas as pd

# Wczytaj pliki
benchmarks_df = pd.read_csv('rating/GPU_UserBenchmarks.csv')
nowe_df = pd.read_csv('nowe_gpu.csv')

# Wyodrębnij nazwy modeli z nazw kart w obu dataframe'ach
def extract_gpu_model(name):
    # Szukamy charakterystycznych oznaczeń kart
    models = ['RTX', 'GTX', 'RX', 'Arc']
    for model in models:
        if model in name:
            # Znajdujemy numer modelu (np. 4090, 3080, etc.)
            import re
            match = re.search(f'{model}\s*(\d{3,4}(?:\s*[-]?[A-Za-z]*)?(?:\s*Super|\s*Ti|\s*XT)?)', name)
            if match:
                return match.group(0).strip()
    return None

# Zastosuj funkcję do obu dataframe'ów
benchmarks_df['clean_model'] = benchmarks_df['Model'].apply(extract_gpu_model)
nowe_df['clean_model'] = nowe_df['gpu'].apply(extract_gpu_model)

# Przygotuj ceny w nowe_df (usuń 'zł' i zamień przecinki na kropki)
nowe_df['price'] = nowe_df['price'].str.replace(' zł', '').str.replace(' ', '')\
                                  .str.replace(',', '.').astype(float)

# Połącz dataframe'y
merged_df = pd.merge(nowe_df,
                    benchmarks_df[['clean_model', 'Benchmark', 'Rank', 'Samples']], 
                    on='clean_model',
                    how='left')

# Posortuj według benchmarku malejąco
merged_df = merged_df.sort_values('Benchmark', ascending=False)

# Wybierz i zmień nazwy kolumn
result_df = merged_df[['brand', 'gpu', 'price', 'Benchmark', 'Rank', 'Samples', 'img-src']]\
    .rename(columns={
        'brand': 'Manufacturer',
        'gpu': 'Model',
        'price': 'Price',
        'img-src': 'Image_URL'
    })

# Zapisz wyniki do nowego pliku CSV
result_df.to_csv('gpu_ratings.csv', index=False)