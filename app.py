"""VEYRA dashboard backend (real data, no mock data).

Run:   pip install flask
       python app.py
Open:  http://127.0.0.1:5000

HOW DATA GETS IN
Your teammates' scripts SEND their results to this server with a small HTTP POST:
  POST /api/csi  {"state": "empty" | "stationary" | "movement"}    from the CSI model
  POST /api/ble  {"detected": true or false, "name": "Watch-01"}   from the BLE scanner
The web page reads everything from GET /api/dashboard.

Until the first data arrives, the dashboard honestly shows "System disconnected".
"""
import os
import threading
import time
from collections import Counter, deque

from flask import Flask, jsonify, request, send_from_directory

# ------------------------------------------------------------------ SETTINGS
HOST, PORT = "127.0.0.1", 5000   # use "0.0.0.0" if the ESP32 / another computer must reach this
CSI_TIMEOUT = 10      # seconds without a CSI result before the ESP32 counts as disconnected
BLE_TIMEOUT = 15      # seconds without a scanner message before the BLE scanner counts as disconnected
TRUSTED_GRACE = 20    # trusted device still counts as "detected" this long after it was last seen
LABEL_MAP = {0: "empty", 1: "stationary", 2: "movement"}   # if your model outputs numbers, edit this
DEFAULT_LEVEL = {"empty": 3, "stationary": 20, "movement": 75}  # graph height if no "level" is sent
# --------------------------------------------------------------------------

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE, "static"))
lock = threading.Lock()

S = {"csi_state": None, "csi_since": 0.0, "csi_last": 0.0, "level": 0,
     "ble_last": 0.0, "ble_seen": 0.0, "ble_name": "Watch-01",
     "alert_since": None, "last_sample": 0.0}
_prev = {"room": "no_data", "trusted": False, "esp": False, "ble": False}
_events = []
_activity = deque(maxlen=1000)    # one sample every ~2s (about 33 minutes)
_csi_times = deque(maxlen=200)
ROOM_TEXT = {"empty": "Room is empty", "stationary": "Room occupied (stationary)",
             "movement": "Movement detected"}


def _log(kind, msg):
    _events.insert(0, {"t": time.time(), "type": kind, "msg": msg})
    del _events[500:]


def _evaluate():
    """Work out the current picture and log anything that changed. Call with the lock held."""
    now = time.time()
    esp = now - S["csi_last"] < CSI_TIMEOUT
    ble = now - S["ble_last"] < BLE_TIMEOUT
    room = S["csi_state"] if esp and S["csi_state"] else "no_data"
    trusted = ble and now - S["ble_seen"] < TRUSTED_GRACE
    name = S["ble_name"]

    if esp != _prev["esp"]:
        _log("system", "ESP32 CSI receiver online" if esp else "ESP32 data interrupted: no results received")
    if ble != _prev["ble"]:
        _log("system", "BLE scanner online" if ble else "BLE scanner stopped responding")
    if room != _prev["room"] and room != "no_data":
        _log("room", ROOM_TEXT[room])
    if trusted != _prev["trusted"]:
        _log("trusted", f"Trusted device detected: {name}" if trusted else f"Trusted device lost: {name}")

    # Unrecognised presence = someone is there, the BLE scanner works, but no trusted device matched.
    flag = room in ("stationary", "movement") and ble and not trusted
    if flag and not S["alert_since"]:
        S["alert_since"] = now
        _log("unrecognised", "Unrecognised presence: no trusted device matched")
    if not flag:
        S["alert_since"] = None

    _prev.update(room=room, trusted=trusted, esp=esp, ble=ble)

    if now - S["last_sample"] >= 2:
        S["last_sample"] = now
        _activity.append({"t": now, "v": S["level"] if room != "no_data" else 0, "s": room})
    return now, esp, ble, room, trusted


def _buckets(n=60, span=1800):
    """Squash the last 30 minutes into 60 points (30 seconds each) for the chart."""
    now = time.time()
    step = span / n
    out = []
    for k in range(n):
        lo = now - span + k * step
        pts = [p for p in _activity if lo <= p["t"] < lo + step]
        if pts:
            s = Counter(p["s"] for p in pts).most_common(1)[0][0]
            out.append({"t": lo, "v": round(sum(p["v"] for p in pts) / len(pts)), "s": s})
        else:
            out.append({"t": lo, "v": 0, "s": "no_data"})
    return out


def get_dashboard():
    with lock:
        now, esp, ble, room, trusted = _evaluate()
        recent = len([t for t in _csi_times if now - t < 10])
        return {
            "now": now,
            "room": {"state": room, "last_change": S["csi_since"]},
            "trusted": {"detected": trusted, "name": S["ble_name"], "last_seen": S["ble_seen"] or None},
            "alert": {"active": bool(S["alert_since"]), "since": S["alert_since"]},
            "system": {
                "esp32": {"online": esp, "last_packet": S["csi_last"], "rate": round(recent / 10, 1)},
                "ble": {"online": ble, "last_scan": S["ble_last"], "rate": 0},
            },
            "activity": _buckets(),
            "events": _events[:100],
        }


def _norm_state(v):
    """Accepts 'movement', 'Movement', or a number from LABEL_MAP. Returns None if unusable."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)) or (isinstance(v, str) and v.strip().isdigit()):
        return LABEL_MAP.get(int(float(v)))
    if isinstance(v, str):
        v = v.strip().lower()
        return v if v in DEFAULT_LEVEL else None
    return None


def _clock():
    while True:   # keeps timeouts, history and the event log going even if nobody has the page open
        with lock:
            _evaluate()
        time.sleep(1)


threading.Thread(target=_clock, daemon=True).start()


# ---------------------------------------------------------------- ROUTES
@app.route("/api/csi", methods=["POST"])
def post_csi():
    d = request.get_json(silent=True) or {}
    st = _norm_state(d.get("state"))
    if st is None:
        return jsonify(error='send {"state": "empty" | "stationary" | "movement"}'), 400
    now = time.time()
    try:
        level = float(d.get("level", DEFAULT_LEVEL[st]))
    except (TypeError, ValueError):
        level = DEFAULT_LEVEL[st]
    with lock:
        if st != S["csi_state"]:
            S["csi_since"] = now
        S["csi_state"], S["csi_last"] = st, now
        S["level"] = max(0, min(100, level))
        _csi_times.append(now)
        _evaluate()
    return jsonify(ok=True)


@app.route("/api/ble", methods=["POST"])
def post_ble():
    d = request.get_json(silent=True) or {}
    now = time.time()
    with lock:
        S["ble_last"] = now                      # any message counts as "scanner is alive"
        if d.get("name"):
            S["ble_name"] = str(d["name"])[:40]
        if d.get("detected") is True:
            S["ble_seen"] = now
        _evaluate()
    return jsonify(ok=True)


@app.route("/api/dashboard")
def dashboard():
    return jsonify(get_dashboard())


@app.route("/")
def index():
    for folder in (os.path.join(BASE, "static"), BASE):
        if os.path.exists(os.path.join(folder, "index.html")):
            return send_from_directory(folder, "index.html")
    return "index.html not found. Put it in a folder called 'static' next to app.py.", 404


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=(HOST == "127.0.0.1"))
