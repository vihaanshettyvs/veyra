"""Pretends to be the CSI model + BLE scanner, so you can test the real pipeline
before the hardware is connected.

1. Start the dashboard:   python app.py
2. In a SECOND terminal:  pip install requests
                          python send_test.py
Stop it with Ctrl+C and, after ~10 seconds, the dashboard shows "System disconnected".
"""
import itertools
import time

import requests

URL = "http://127.0.0.1:5000"

# (room state, is the trusted watch detected?)
STEPS = [("empty", False), ("stationary", True), ("movement", True),
         ("movement", False),    # someone moving, no watch -> Unrecognised presence flag
         ("stationary", False), ("empty", False)]

for state, watch in itertools.cycle(STEPS):
    for _ in range(5):           # about 10 seconds per step
        requests.post(URL + "/api/csi", json={"state": state}, timeout=2)
        requests.post(URL + "/api/ble", json={"detected": watch, "name": "Watch-01"}, timeout=2)
        time.sleep(2)
