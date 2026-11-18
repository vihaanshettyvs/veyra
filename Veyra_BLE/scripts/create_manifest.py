import os
import pandas as pd

records = [
    {"filename": "serial_20261104_181012_parsed.csv", "activity_label": "stationary", "detailed_label": "Stationary presence", "round": 1, "use_for_training": True},
    {"filename": "serial_20261104_181654_parsed.csv", "activity_label": "mixed_movement", "detailed_label": "1 person walking, 3 stationary", "round": 1, "use_for_training": True},
    {"filename": "serial_20261104_182053_parsed.csv", "activity_label": "movement", "detailed_label": "4 people walking", "round": 1, "use_for_training": True},
    {"filename": "serial_20261104_182639_parsed.csv", "activity_label": "empty", "detailed_label": "Empty room", "round": 1, "use_for_training": True},
    {"filename": "serial_20261104_183134_parsed.csv", "activity_label": "stationary", "detailed_label": "Stationary presence", "round": 2, "use_for_training": True},
    {"filename": "serial_20261104_184126_parsed.csv", "activity_label": "empty", "detailed_label": "Empty room", "round": 2, "use_for_training": True},
    {"filename": "serial_20261104_184512_parsed.csv", "activity_label": "mixed_movement", "detailed_label": "1 person walking, 3 stationary", "round": 2, "use_for_training": True},
    {"filename": "serial_20261104_184638_parsed.csv", "activity_label": "movement", "detailed_label": "4 people walking", "round": 2, "use_for_training": True},
    {"filename": "serial_20261104_194024_parsed.csv", "activity_label": "unlabelled", "detailed_label": "Unlabelled test recording", "round": None, "use_for_training": False},
    {"filename": "serial_20261103_002801_parsed.csv", "activity_label": "unlabelled", "detailed_label": "Unconfirmed recording", "round": None, "use_for_training": False},
]

manifest_df = pd.DataFrame(records)

# Point to your 'data' folder
manifest_df["filepath"] = manifest_df["filename"].apply(lambda f: os.path.join("data", f))
manifest_df["file_exists"] = manifest_df["filepath"].apply(os.path.exists)

manifest_df.to_csv("manifest.csv", index=False)
print("manifest.csv created successfully!\n")
print(manifest_df[["filename", "activity_label", "round", "file_exists", "filepath"]])
