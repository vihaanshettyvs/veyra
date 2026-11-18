import os
import pandas as pd

print("--- ALL CSV FILES FOUND IN PROJECT ---")
all_csvs = []
for root, dirs, files in os.walk("."):
    if ".venv" in root:
        continue
    for f in sorted(files):
        if f.endswith(".csv") and f != "manifest.csv":
            full_path = os.path.join(root, f)
            all_csvs.append(full_path)
            print("Found:", full_path)

if not all_csvs:
    print("No CSV files found inside VEYRA_BLE!")
else:
    sample_path = all_csvs.pop(0)
    print(f"\n--- INSPECTING FIRST CSV: {sample_path} ---")
    df = pd.read_csv(sample_path)
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print("Columns:", list(df.columns))

    print("\n--- FIRST 2 ROWS (METADATA) ---")
    meta_cols = [c for c in df.columns if c != "csi_values"]
    print(df[meta_cols].head(2).to_string())

    if "csi_values" in df.columns:
        first_csi = df["csi_values"].head(1).item()
        print("\n--- RAW csi_values (PACKET 1) ---")
        print("Type:", type(first_csi))
        print("First 120 chars:", str(first_csi)[:120])
        print("Last 60 chars:", str(first_csi)[-60:])



