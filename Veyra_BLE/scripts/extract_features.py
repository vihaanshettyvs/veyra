import ast
import numpy as np
import pandas as pd

WINDOW_SIZE = 25
STEP_SIZE = 12

def parse_csi_amplitude(csi_str):
    vals = np.array(ast.literal_eval(csi_str), dtype=np.float32)
    vals = vals[4:]  # Drop invalid first 32-bit word (4 bytes)
    pairs = vals.reshape(-1, 2)
    amp = np.sqrt(pairs[:, 0]**2 + pairs[:, 1]**2)
    mean_val = amp.mean()
    return amp / mean_val if mean_val > 0 else amp

def extract_window_features(win_amp):
    active_mask = win_amp.mean(axis=0) > 0.05
    w = win_amp[:, active_mask]
    pkt_diff = np.diff(w, axis=0)
    subcarrier_temp_std = w.std(axis=0)
    corr_matrix = np.corrcoef(w.T)
    upper_tri = np.nan_to_num(corr_matrix[np.triu_indices_from(corr_matrix, k=1)], nan=0.0)
    
    return {
        "norm_std_mean": float(subcarrier_temp_std.mean()),
        "norm_std_median": float(np.median(subcarrier_temp_std)),
        "norm_std_p90": float(np.percentile(subcarrier_temp_std, 90)),
        "norm_std_max": float(subcarrier_temp_std.max()),
        "norm_iqr_mean": float(np.mean(np.percentile(w, 75, axis=0) - np.percentile(w, 25, axis=0))),
        "diff_abs_mean": float(np.abs(pkt_diff).mean()),
        "diff_rms": float(np.sqrt(np.mean(pkt_diff**2))),
        "diff_p90": float(np.percentile(np.abs(pkt_diff), 90)),
        "subcarrier_corr_mean": float(upper_tri.mean()),
        "subcarrier_corr_std": float(upper_tri.std()),
        "spatial_std_fluctuation": float(w.std(axis=1).std()),
    }

manifest = pd.read_csv("manifest.csv")
train_files = manifest[(manifest["use_for_training"] == True) & (manifest["file_exists"] == True)]

all_windows = []
for _, row in train_files.iterrows():
    df = pd.read_csv(row["filepath"])
    amp_matrix = np.vstack(df["csi_values"].apply(parse_csi_amplitude).values)
    for start in range(0, len(amp_matrix) - WINDOW_SIZE + 1, STEP_SIZE):
        win_amp = amp_matrix[start : start + WINDOW_SIZE]
        feats = extract_window_features(win_amp)
        feats["filename"] = row["filename"]
        feats["round"] = int(row["round"])
        feats["label_4class"] = row["activity_label"]
        feats["label_3class"] = "movement" if "movement" in row["activity_label"] else row["activity_label"]
        feats["label_2class"] = "movement" if "movement" in row["activity_label"] else "no_movement"
        all_windows.append(feats)

features_df = pd.DataFrame(all_windows)
features_df.to_csv("csi_features.csv", index=False)
print("Restored best 11-feature dataset!")



