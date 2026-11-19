"""VEYRA dashboard backend (mock data).

Run:   pip install flask
       python app.py
Open:  http://127.0.0.1:5000

The browser only talks to ONE endpoint: /api/dashboard.
Later, replace the code inside get_dashboard() with real CSI + BLE data.
Keep the returned JSON shape the same and the HTML never needs to change.
"""
import random
import time
from collections import Counter, deque

from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

# ---------------------------------------------------------------- MOCK DATA
# Everything in this block is fake. Swap it for real hardware output later.
LEVEL = {"empty": (0, 6), "stationary": (14, 30), "movement": (55, 95)}
now0 = time.time()
_c = {"state": "empty", "since": now0, "trusted": False, "alert_since": None,
      "outage": 0.0, "last_sample": 0.0}
_events = []
_activity = deque(maxlen=1000)  # one sample every ~2s (about 33 minutes)


def _log(kind, msg, t=None):
    _events.insert(0, {"t": t or time.time(), "type": kind, "msg": msg})





def _tick():
    now = time.time()
    off = _c["outage"] > now
    if _c["outage"] and not off:
        _c["outage"] = 0.0
        _log("system", "ESP32 CSI receiver back online")

    if not off and now - _c["since"] > random.randint(8, 18):
        if random.random() < 0.08:  # simulate a sensor dropout
            _c["outage"] = now + 10
            _log("system", "ESP32 data interrupted: no packets received")
        else:
            was_trusted, old = _c["trusted"], _c["state"]
            _c["state"] = random.choice(["empty", "stationary", "movement"])
            _c["since"] = now
            _c["trusted"] = _c["state"] != "empty" and random.random() < 0.55
            labels = {"empty": "Room is empty", "stationary": "Room occupied (stationary)",
                      "movement": "Movement detected"}
            _log("room", labels[_c["state"]])
            if _c["trusted"] and not was_trusted:
                _log("trusted", "Trusted device detected: Watch-01")
            if was_trusted and not _c["trusted"]:
                _log("trusted", "Trusted device lost: Watch-01")
            present = _c["state"] != "empty"
            if present and not _c["trusted"]:
                if not _c["alert_since"]:
                    _c["alert_since"] = now
                    _log("unrecognised", "Unrecognised presence: no trusted device matched")
            else:
                _c["alert_since"] = None

    if now - _c["last_sample"] >= 2:
        _c["last_sample"] = now
        st = "no_data" if off else _c["state"]
        lo, hi = LEVEL.get(st, (0, 0))
        _activity.append({"t": now, "v": random.randint(lo, hi), "s": st})


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
    _tick()
    now = time.time()
    off = _c["outage"] > now
    return {
        "now": now,
        "room": {"state": "no_data" if off else _c["state"], "last_change": _c["since"]},
        "trusted": {"detected": _c["trusted"], "name": "Watch-01",
                    "last_seen": now if _c["trusted"] else now - 600},
        "alert": {"active": bool(_c["alert_since"]) and not off, "since": _c["alert_since"]},
        "system": {
            "esp32": {"online": not off, "last_packet": now - (30 if off else random.random()),
                      "rate": 0 if off else random.randint(92, 104)},
            "ble": {"online": True, "last_scan": now - random.random() * 2, "rate": 1},
        },
        "activity": _buckets(),
        "events": _events[:100],
    }
# ------------------------------------------------------------- END MOCK DATA


@app.route("/api/dashboard")
def dashboard():
    return jsonify(get_dashboard())


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    app.run(debug=True)
