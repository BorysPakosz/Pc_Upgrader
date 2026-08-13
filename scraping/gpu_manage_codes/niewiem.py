import pandas as pd
import re

# Read the CSV files
price_df = pd.read_csv('nowy_gpu.csv')
ranking_df = pd.read_csv('rating/GPU_UserBenchmarks.csv')

# Clean the data
for df in [price_df, ranking_df]:
    for col in df.columns:
        # Convert numerical NaN values to empty strings to avoid type errors with string operations
        df[col] = df[col].fillna("")
        if df[col].dtype == object:
            df[col] = df[col].str.strip() if hasattr(df[col], 'str') else df[col]

# Function to normalize model names for better matching
def normalize_model_name(name):
    if not isinstance(name, str):
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove prefixes like "geforce" or suffixes like "gpu"
    name = re.sub(r'geforce\s+', '', name)
    name = re.sub(r'radeon\s+', '', name)
    
    # Extract RTX/GTX/RX model numbers with possible suffixes
    gpu_match = re.search(r'(rtx|gtx|rx)\s*(\d{4,})\s*(ti|super|xt|xtx)?', name)
    if gpu_match:
        base = f"{gpu_match.group(1)} {gpu_match.group(2)}"
        suffix = gpu_match.group(3) if gpu_match.group(3) else ""
        return f"{base} {suffix}".strip()
    
    # For other models, just return cleaned name
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

# Add normalized model columns
price_df['normalized_model'] = price_df['title'].apply(normalize_model_name)
ranking_df['normalized_model'] = ranking_df['Model'].apply(normalize_model_name)

# Add extracted base model for matching
try:
    price_df['extracted_model'] = price_df['title'].apply(lambda x: 
        re.search(r'(rtx|gtx|rx)\s*(\d{4,})\s*(ti|super|xt|xtx)?', str(x).lower()).group(0) 
        if re.search(r'(rtx|gtx|rx)\s*(\d{4,})\s*(ti|super|xt|xtx)?', str(x).lower()) else "")
    
    ranking_df['extracted_model'] = ranking_df['Model'].apply(lambda x: 
        re.search(r'(rtx|gtx|rx)\s*(\d{4,})\s*(ti|super|xt|xtx)?', str(x).lower()).group(0) 
        if re.search(r'(rtx|gtx|rx)\s*(\d{4,})\s*(ti|super|xt|xtx)?', str(x).lower()) else "")
except Exception as e:
    print(f"Warning: Error in model extraction: {e}")
    price_df['extracted_model'] = ""
    ranking_df['extracted_model'] = ""

# Match by part number first
merged_df = pd.DataFrame(columns=price_df.columns.tolist() + ranking_df.columns.tolist())
matched_price_indices = set()
matched_ranking_indices = set()

# Step 1: Match by part number (exact match)
for p_idx, p_row in price_df.iterrows():
    for r_idx, r_row in ranking_df.iterrows():
        # Safe string comparison with type checking
        if (isinstance(p_row['part_number'], str) and 
            isinstance(r_row['Part Number'], str) and 
            p_row['part_number'] and 
            r_row['Part Number'] and 
            p_row['part_number'].lower() == r_row['Part Number'].lower()):
            combined_row = pd.concat([p_row, r_row])
            merged_df = pd.concat([merged_df, combined_row.to_frame().T], ignore_index=True)
            matched_price_indices.add(p_idx)
            matched_ranking_indices.add(r_idx)

# Step 2: Match by normalized model names and extracted model
for p_idx, p_row in price_df.iterrows():
    if p_idx in matched_price_indices:
        continue
    
    for r_idx, r_row in ranking_df.iterrows():
        if r_idx in matched_ranking_indices:
            continue
        
        # Try matching on normalized model names
        if (isinstance(p_row['normalized_model'], str) and 
            isinstance(r_row['normalized_model'], str) and 
            p_row['normalized_model'] and 
            r_row['normalized_model'] and 
            p_row['normalized_model'] == r_row['normalized_model']):
            combined_row = pd.concat([p_row, r_row])
            merged_df = pd.concat([merged_df, combined_row.to_frame().T], ignore_index=True)
            matched_price_indices.add(p_idx)
            matched_ranking_indices.add(r_idx)
            break
            
        # Try matching on extracted model (handles Ti, Super, etc. variants)
        if (p_row.get('extracted_model', "") and 
            r_row.get('extracted_model', "") and 
            p_row['extracted_model'] == r_row['extracted_model']):
            combined_row = pd.concat([p_row, r_row])
            merged_df = pd.concat([merged_df, combined_row.to_frame().T], ignore_index=True)
            matched_price_indices.add(p_idx)
            matched_ranking_indices.add(r_idx)
            break
            
        # Try matching on base model number (ignoring suffixes)
        p_base_match = re.search(r'(rtx|gtx|rx)\s*(\d{4,})', str(p_row.get('extracted_model', "")))
        r_base_match = re.search(r'(rtx|gtx|rx)\s*(\d{4,})', str(r_row.get('extracted_model', "")))
        
        if (p_base_match and r_base_match and 
            p_base_match.group(1) == r_base_match.group(1) and 
            p_base_match.group(2) == r_base_match.group(2)):
            combined_row = pd.concat([p_row, r_row])
            merged_df = pd.concat([merged_df, combined_row.to_frame().T], ignore_index=True)
            matched_price_indices.add(p_idx)
            matched_ranking_indices.add(r_idx)
            break

# Step 3: Match by chipset and partial model name
for p_idx, p_row in price_df.iterrows():
    if p_idx in matched_price_indices:
        continue
    
    for r_idx, r_row in ranking_df.iterrows():
        if r_idx in matched_ranking_indices:
            continue
        
        # Safe string conversion with null checking
        p_chipset = str(p_row['chipset']).lower() if pd.notna(p_row['chipset']) else ""
        r_model = str(r_row['Model']).lower() if pd.notna(r_row['Model']) else ""
        p_title = str(p_row['title']).lower() if pd.notna(p_row['title']) else ""
        
        # Check if chipset is in model name or vice versa
        if (p_chipset and p_chipset in r_model) or (r_model and r_model in p_title):
            combined_row = pd.concat([p_row, r_row])
            merged_df = pd.concat([merged_df, combined_row.to_frame().T], ignore_index=True)
            matched_price_indices.add(p_idx)
            matched_ranking_indices.add(r_idx)
            break

# Add remaining unmatched rows from price data
for p_idx, p_row in price_df.iterrows():
    if p_idx not in matched_price_indices:
        blank_ranking = pd.Series([None] * len(ranking_df.columns), index=ranking_df.columns)
        combined_row = pd.concat([p_row, blank_ranking])
        merged_df = pd.concat([merged_df, combined_row.to_frame().T], ignore_index=True)

# Add remaining unmatched rows from ranking data
for r_idx, r_row in ranking_df.iterrows():
    if r_idx not in matched_ranking_indices:
        blank_price = pd.Series([None] * len(price_df.columns), index=price_df.columns)
        combined_row = pd.concat([blank_price, r_row])
        merged_df = pd.concat([merged_df, combined_row.to_frame().T], ignore_index=True)

# Reorder columns for better readability
cols_order = [
    'title', 'Brand', 'Model', 'normalized_model', 'Rank', 'Benchmark', 
    'price', 'chipset', 'ram', 'dlugosc', 'taktowanie', 'part_number', 'Part Number',
    'Samples', 'URL', 'img-src', 'link_produkt-href'
]
merged_df = merged_df[cols_order]

# Fill missing Model values with title for better readability
merged_df['Model'] = merged_df.apply(lambda row: row['Model'] if row['Model'] else row['title'], axis=1)

# Clean up the display - drop columns used just for matching
cols_to_drop = ['normalized_model', 'extracted_model']
final_df = merged_df.drop([col for col in cols_to_drop if col in merged_df.columns], axis=1)

# Print the final merged dataframe
print("Final merged dataset:")
print(final_df.head())

# Function to apply the same ranking to similar models
def propagate_rankings(df):
    model_to_rank = {}
    model_to_benchmark = {}
    
    # First collect all rankings by model name patterns
    for _, row in df.iterrows():
        if row['Rank'] and row['Model']:
            # Extract the core model number (e.g., RTX 4090 from different variants)
            model_pattern = normalize_model_name(str(row['Model']))
            if model_pattern and model_pattern not in model_to_rank:
                model_to_rank[model_pattern] = row['Rank']
                model_to_benchmark[model_pattern] = row['Benchmark']
    
    # Then apply those rankings to similar models
    for idx, row in df.iterrows():
        if not row['Rank'] and row['Model']:
            model_norm = normalize_model_name(str(row['Model']))
            
            # Try exact match first
            if model_norm in model_to_rank:
                df.at[idx, 'Rank'] = model_to_rank[model_norm]
                df.at[idx, 'Benchmark'] = model_to_benchmark[model_norm]
                continue
                
            # Extract the base model without suffixes for fuzzy matching
            base_model_match = re.search(r'(rtx|gtx|rx)\s*(\d{4,})', model_norm)
            if base_model_match:
                base_model = f"{base_model_match.group(1)} {base_model_match.group(2)}"
                
                # Try to match with same base model
                for pattern, rank in model_to_rank.items():
                    pattern_base = re.search(r'(rtx|gtx|rx)\s*(\d{4,})', pattern)
                    if pattern_base and pattern_base.group(1) == base_model_match.group(1) and pattern_base.group(2) == base_model_match.group(2):
                        df.at[idx, 'Rank'] = rank
                        df.at[idx, 'Benchmark'] = model_to_benchmark[pattern]
                        break
            else:
                # Fall back to substring matching for non-standard model names
                for pattern, rank in model_to_rank.items():
                    if pattern and model_norm and (pattern in model_norm or model_norm in pattern):
                        df.at[idx, 'Rank'] = rank
                        df.at[idx, 'Benchmark'] = model_to_benchmark[pattern]
                        break
    
    return df

# Apply ranking propagation
final_df = propagate_rankings(final_df)

# Save to CSV
final_df.to_csv('merged_gpu_data.csv', index=False, encoding='utf-8')

print("\nData saved to 'merged_gpu_data.csv'")
print(f"Total cards: {len(final_df)}")
print(f"Cards with rankings: {sum(1 for x in final_df['Rank'] if x)}")
print(f"Cards without rankings: {sum(1 for x in final_df['Rank'] if not x)}")