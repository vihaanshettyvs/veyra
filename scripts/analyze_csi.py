
import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# Check command-line argument
if len(sys.argv) != 2:
    print("Usage: python scripts/analyze_csi.py <csv_file>")
    sys.exit(1)

path = Path(sys.argv[1])

if not path.exists():
    print(f"File not found: {path}")
    sys.exit(1)


# Load dataset
df = pd.read_csv(path)

print("\n========== VEYRA SIGNAL ANALYSIS ==========")
print("\nDataset:", path)
print("Dataset shape:", df.shape)


# Output directory
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

# Unique filename for each recording
prefix = path.stem


# RSSI analysis
print("\nRSSI statistics:")
print(df["rssi"].describe())


# Packet timing analysis
timestamps = pd.to_datetime(df["timestamp"])
intervals = timestamps.diff().dt.total_seconds().dropna()

print("\nPacket interval statistics (seconds):")
print(intervals.describe())


# Decode CSI arrays
csi_arrays = []

for value in df["csi_values"]:
    try:
        array = json.loads(value)

        if len(array) == 384:
            csi_arrays.append(array)

    except (json.JSONDecodeError, TypeError):
        continue


if not csi_arrays:
    print("\nNo valid CSI arrays found.")
    sys.exit(1)


csi_arrays = np.array(csi_arrays)

print("\nCSI matrix shape:", csi_arrays.shape)

print("\nCSI value statistics:")
print("Minimum:", csi_arrays.min())
print("Maximum:", csi_arrays.max())
print("Mean:", csi_arrays.mean())
print("Standard deviation:", csi_arrays.std())


# 1. RSSI over time
plt.figure(figsize=(12, 5))
plt.plot(timestamps, df["rssi"])

plt.title(f"VEYRA - RSSI over time ({prefix})")
plt.xlabel("Time")
plt.ylabel("RSSI (dBm)")

plt.xticks(rotation=30)
plt.tight_layout()

rssi_file = output_dir / f"{prefix}_rssi.png"
plt.savefig(rssi_file, dpi=150)
plt.close()


# 2. CSI values from one packet
plt.figure(figsize=(12, 5))
plt.plot(csi_arrays[0])

plt.title(f"VEYRA - CSI values in one packet ({prefix})")
plt.xlabel("CSI array index")
plt.ylabel("Recorded value")

plt.tight_layout()

single_file = output_dir / f"{prefix}_single_packet.png"
plt.savefig(single_file, dpi=150)
plt.close()


# 3. CSI variation across packets
plt.figure(figsize=(12, 5))
plt.plot(np.std(csi_arrays, axis=0))

plt.title(f"VEYRA - CSI variation across packets ({prefix})")
plt.xlabel("CSI array index")
plt.ylabel("Standard deviation")

plt.tight_layout()

variation_file = output_dir / f"{prefix}_variation.png"
plt.savefig(variation_file, dpi=150)
plt.close()


# Results
print("\nAll three plots saved successfully:")
print(rssi_file)
print(single_file)
print(variation_file)

print("\n==========================================")
