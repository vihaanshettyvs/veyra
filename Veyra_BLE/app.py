import joblib
import numpy as np
import pandas as pd
import streamlit as st
from scripts.extract_features import WINDOW_SIZE, STEP_SIZE, extract_window_features, parse_csi_amplitude

st.set_page_config(page_title="VEYRA — Privacy-Conscious Indoor Monitoring", layout="wide")
st.title("VEYRA — Wi-Fi CSI Activity & BLE Presence Dashboard")
st.caption("Offline CSI Replay & Classification Prototype (Hardware-Free Mode)")

bundle = joblib.load("veyra_csi_model.joblib")
model = bundle["model"]
feature_cols = bundle["features"]
manifest = pd.read_csv("manifest.csv")
available_files = manifest[manifest["file_exists"] == True]

st.sidebar.header("1. Select CSI Recording")
selected_file = st.sidebar.selectbox("Choose a parsed CSV recording:", available_files["filename"].tolist())
file_info = available_files[available_files["filename"] == selected_file].squeeze()

st.sidebar.markdown(f"**Ground Truth Label:** `{file_info['detailed_label']}`")
st.sidebar.markdown(f"**Training Set:** `{file_info['use_for_training']}`")

st.sidebar.divider()
st.sidebar.header("2. BLE Trusted Wearable Status")
ble_present = st.sidebar.toggle("Simulate Trusted Smartwatch Detected (BLE)", value=True)
if ble_present:
    st.sidebar.success("Trusted Device Present (Authorized)")
else:
    st.sidebar.warning("No Trusted Wearable Detected")

df = pd.read_csv(file_info["filepath"])
amp_matrix = np.vstack(df["csi_values"].apply(parse_csi_amplitude).values)

window_preds = []
for start in range(0, len(amp_matrix) - WINDOW_SIZE + 1, STEP_SIZE):
    feats = extract_window_features(amp_matrix[start : start + WINDOW_SIZE])
    X_win = pd.DataFrame([feats])[feature_cols]
    pred = model.predict(X_win).item()
    window_preds.append({"window_idx": len(window_preds), "start_packet": start, "prediction": pred})

pred_df = pd.DataFrame(window_preds)
dominant_activity = next(iter(pred_df["prediction"].mode()))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Dominant Room Activity", dominant_activity.upper())
col2.metric("Total Packets Analyzed", len(df))
col3.metric("Time Windows Evaluated", len(pred_df))
col4.metric("BLE Trusted Presence", "Authorized" if ble_present else "Unverified")

st.subheader("Normalized CSI Subcarrier Amplitude Over Time")
st.line_chart(amp_matrix.mean(axis=1))

st.subheader("Window-by-Window Activity Predictions")
st.bar_chart(pred_df["prediction"].value_counts())
st.dataframe(pred_df, use_container_width=True)
