import ast
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 1. Load manifest and filter ONLY confirmed training recordings
manifest = pd.read_csv("manifest.csv")
train_files = manifest[(manifest["use_for_training"] == True) & (manifest["file_exists"] == True)]

print(f"Loaded {len(train_files)} confirmed labelled recordings for EDA.\n")

def parse_csi_amplitude(csi_str, drop_first_word=True):
    """Parse string '[a, b, ...]' into subcarrier amplitudes sqrt(x^2 + y^2)."""
    vals = np.array(ast.literal_eval(csi_str), dtype=np.float32)
    if drop_first_word:
        vals = vals[4:]  # Remove first invalid 32-bit word (4 bytes = 2 subcarriers)
    # Reshape into pairs (N_subcarriers, 2) and compute magnitude
    pairs = vals.reshape(-1, 2)
    amplitudes = np.sqrt(pairs[:, 0]**2 + pairs[:, 1]**2)
    return amplitudes

summary_rows = []
fig, axes = plt.subplots(4, 2, figsize=(14, 12), sharex=False)
axes = axes.flatten()

for idx, (_, row) in enumerate(train_files.iterrows()):
    df = pd.read_csv(row["filepath"])
    
    # Check if any packet lacks first_word_invalid == 1 or length != 384
    bad_len = (df["csi_length"] != 384).sum()
    
    # Convert all packets into a 2D matrix: (num_packets, 190_subcarriers)
    amp_matrix = np.vstack(df["csi_values"].apply(parse_csi_amplitude).values)
    
    # Compute mean amplitude per packet across subcarriers
    packet_mean_amp = amp_matrix.mean(axis=1)
    
    # Compute temporal fluctuation (how much amplitude changes from packet to packet)
    packet_diff_std = np.diff(packet_mean_amp).std()
    overall_std = amp_matrix.std()
    
    summary_rows.append({
        "filename": row["filename"],
        "label": row["activity_label"],
        "round": int(row["round"]),
        "packets": len(df),
        "bad_len": bad_len,
        "mean_amp": round(float(amp_matrix.mean()), 2),
        "overall_std": round(float(overall_std), 2),
        "temporal_diff_std": round(float(packet_diff_std), 3),
    })
    
    # Plot packet-by-packet mean amplitude for visual inspection
    ax = axes[idx]
    ax.plot(packet_mean_amp, linewidth=0.9)
    ax.set_title(f"R{int(row['round'])} | {row['activity_label']} ({row['detailed_label']})", fontsize=9)
    ax.set_ylabel("Mean Amp")
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("csi_eda_plot.png", dpi=150)

summary_df = pd.DataFrame(summary_rows)
print("--- CSI AMPLITUDE SUMMARY ACROSS ALL 8 LABELLED RECORDINGS ---")
print(summary_df.to_string(index=False))
print("\nSaved visual comparison plot to: csi_eda_plot.png")
