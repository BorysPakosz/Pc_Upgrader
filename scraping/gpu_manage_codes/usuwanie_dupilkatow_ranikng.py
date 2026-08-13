import pandas as pd

# 1) Wczytaj połączenie
df = pd.read_csv('filtered_output_gpu.csv')
df = df.drop(columns=['URL'])

# 4) Zapisz efekt
df.to_csv('filtered_output_gpu.csv', index=False)
