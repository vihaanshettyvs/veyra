import pandas as pd

df = pd.read_csv("csi_features.csv")

# Compare the median feature values per recording file
meta_cols = ["filename", "round", "label_4class", "label_3class"]
feature_cols = [c for c in df.columns if c not in meta_cols]

summary = df.groupby(["label_4class", "round", "filename"])[feature_cols].median().round(4)
print("--- MEDIAN FEATURE VALUES PER RECORDING SESSION ---")
print(summary.to_string())
