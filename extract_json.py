#!/usr/bin/env python3
#extract_json.py
# Script to extract data from JSON files in a directory and save to CSV
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Define the base directory
base_dir = "/Users/cmilbourn/Documents/Sweet_Data/Development_Data/nifti/"

# Find all JSON files
json_files = list(Path(base_dir).rglob("*.json"))
print(f"Found {len(json_files)} JSON files\n")

# Store data for the table
data = []

# Process each JSON file
for json_file in sorted(json_files):
    try:
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        
        # Get relative path
        rel_path = str(json_file.relative_to(base_dir))
        
        # Flatten JSON data for the table (first level keys and values)
        row = {"File": rel_path}
        
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                # Truncate long values
                if isinstance(value, (list, dict)):
                    val_str = str(value)
                    value_str = val_str[:100] + "..." if len(val_str) > 100 else val_str
                else:
                    value_str = str(value)
                row[key] = value_str
        
        data.append(row)
    except Exception as e:
        print(f"Error reading {json_file}: {e}")

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = Path("/Users/cmilbourn/Library/CloudStorage/OneDrive-TheUniversityofNottingham/Project2_SweetPhase2/Methods_Project2_SweetPhase2/DataAnalysis/tSNR/tSNR_V2/extract_json")
output_dir.mkdir(parents=True, exist_ok=True)
output_csv = output_dir / f"nifti_json_data_{timestamp}.csv"
df.to_csv(output_csv, index=False)
print(f"CSV saved to: {output_csv}")

# Display summary
print(f"\nTotal JSON files: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print(f"\nFirst few rows:")
print(df.head(15).to_string())
print("\n" + "="*80)
print("Columns in dataset:")
print(sorted(df.columns.tolist()))
