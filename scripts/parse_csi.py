import csv
import json
import sys
from pathlib import Path


def parse_csi_file(input_path):
    input_path = Path(input_path)

    if not input_path.exists():
        print(f"File not found: {input_path}")
        return

    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{input_path.stem}_parsed.csv"

    columns = [
        "timestamp",
        "packet_id",
        "mac",
        "rssi",
        "rate",
        "sig_mode",
        "mcs",
        "bandwidth",
        "smoothing",
        "not_sounding",
        "aggregation",
        "stbc",
        "fec_coding",
        "sgi",
        "noise_floor",
        "ampdu_cnt",
        "channel",
        "secondary_channel",
        "local_timestamp",
        "ant",
        "sig_len",
        "rx_format",
        "csi_length",
        "first_word_invalid",
        "csi_values",
    ]

    total_csi = 0
    valid_records = 0
    rejected_records = 0
    invalid_arrays = 0
    array_lengths = set()

    with input_path.open("rb") as raw_file, \
         output_path.open("w", newline="", encoding="utf-8") as output_file:

        writer = csv.DictWriter(output_file, fieldnames=columns)
        writer.writeheader()

        for raw_line in raw_file:
            if b"CSI_DATA," not in raw_line:
                continue

            total_csi += 1

            try:
                line = raw_line.decode("utf-8").strip()
                row = next(csv.reader([line]))

                if len(row) != 26:
                    rejected_records += 1
                    continue

                if row[1] != "CSI_DATA":
                    rejected_records += 1
                    continue

                declared_length = int(row[23])
                csi_text = row[25].strip()

                if not (csi_text.startswith("[") and csi_text.endswith("]")):
                    invalid_arrays += 1
                    rejected_records += 1
                    continue

                values = [
                    int(value.strip())
                    for value in csi_text[1:-1].split(",")
                ]

                if len(values) != declared_length:
                    invalid_arrays += 1
                    rejected_records += 1
                    continue

                output_row = {
                    "timestamp": row[0],
                    "packet_id": int(row[2]),
                    "mac": row[3],
                    "rssi": int(row[4]),
                    "rate": int(row[5]),
                    "sig_mode": int(row[6]),
                    "mcs": int(row[7]),
                    "bandwidth": int(row[8]),
                    "smoothing": int(row[9]),
                    "not_sounding": int(row[10]),
                    "aggregation": int(row[11]),
                    "stbc": int(row[12]),
                    "fec_coding": int(row[13]),
                    "sgi": int(row[14]),
                    "noise_floor": int(row[15]),
                    "ampdu_cnt": int(row[16]),
                    "channel": int(row[17]),
                    "secondary_channel": int(row[18]),
                    "local_timestamp": int(row[19]),
                    "ant": int(row[20]),
                    "sig_len": int(row[21]),
                    "rx_format": int(row[22]),
                    "csi_length": declared_length,
                    "first_word_invalid": int(row[24]),
                    "csi_values": json.dumps(values),
                }

                writer.writerow(output_row)
                valid_records += 1
                array_lengths.add(len(values))

            except (ValueError, csv.Error, IndexError):
                rejected_records += 1

    print("\n========== VEYRA CSI PARSER ==========")
    print(f"Input:                  {input_path}")
    print(f"CSI records found:      {total_csi}")
    print(f"Valid records exported: {valid_records}")
    print(f"Rejected records:       {rejected_records}")
    print(f"Invalid CSI arrays:     {invalid_arrays}")
    print(f"Array lengths found:    {sorted(array_lengths)}")
    print(f"\nOutput: {output_path}")
    print("======================================")

    if valid_records == 0:
        print("WARNING: No valid records were exported.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/parse_csi.py <input_log_file>")
        sys.exit(1)

    parse_csi_file(sys.argv[1])
