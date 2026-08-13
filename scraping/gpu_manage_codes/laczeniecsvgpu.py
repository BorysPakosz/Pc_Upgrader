import pandas as pd
import difflib

# 1) Wczytaj oba pliki
details = pd.read_csv('nowy_gpu.csv')
rank    = pd.read_csv('rating/GPU_UserBenchmarks.csv')

# 2) Dokładne łączenie po part_number
merged = details.merge(
    rank,
    how='left',
    left_on='part_number',
    right_on='Part Number',
    suffixes=('', '_rank')
)

# 3) Przygotuj listę modeli do fuzzy-matchingu
model_list = rank['Model'].dropna().unique().tolist()

def match_model(text, choices, cutoff=0.8):
    """
    Zwraca najlepsze dopasowanie z 'choices' dla stringa 'text'
    jeśli współczynnik podobieństwa >= cutoff (0.0–1.0).
    """
    matches = difflib.get_close_matches(text, choices, n=1, cutoff=cutoff)
    return matches[0] if matches else None

# 4) Dla każdego wiersza bez rankingu spróbuj dopasować fuzzy,
#    ale tylko jeśli jest niepusty chipset
unmatched_idx = merged[merged['Rank'].isna()].index
for idx in unmatched_idx:
    chipset = merged.at[idx, 'chipset']
    # pomiń, jeśli chipset jest NaN lub pusty string
    if pd.isna(chipset) or str(chipset).strip() == '':
        continue

    combined = f"{chipset} {merged.at[idx, 'title']}"
    best_model = match_model(combined, model_list)
    if best_model:
        matched = rank[rank['Model'] == best_model].iloc[0]
        for col in ['Rank', 'Benchmark', 'Samples', 'URL', 'Brand', 'Type']:
            merged.at[idx, col] = matched[col]

# 5) Zapisz efekt
merged.to_csv('merged_output.csv', index=False)
print("Zapisano merged_output.csv")
