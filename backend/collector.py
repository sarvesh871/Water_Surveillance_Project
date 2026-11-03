import requests
from collections import deque
from statistics import median
from config import ESP_URL
from mode_state import get_mode

turbidity_history = deque(maxlen=5)

def smooth_turbidity(raw):
    raw = float(raw)
    turbidity_history.append(raw)
    return round(median(turbidity_history), 2)

def normalize_turbidity_for_demo(raw_value):
    """Apply the requested software workaround to a noisy hardware reading.

    Values below 3 are passed through unchanged. Values >= 3 are mapped
    monotonically into 1.0-2.9, so larger raw readings still mean more
    cloudiness within the adjusted range. The original reading is retained
    separately. This is NOT a physical calibration to NTU.
    """
    raw_value = float(raw_value)
    if raw_value < 3.0:
        return round(raw_value, 2), False
    # A logarithmic compression handles typical 3-20 readings without
    # abrupt jumps and safely clamps unusually large input values.
    import math
    bounded = max(3.0, min(raw_value, 1000.0))
    adjusted = 1.0 + 1.9 * (math.log(bounded / 3.0) / math.log(1000.0 / 3.0))
    return round(min(2.9, max(1.0, adjusted)), 2), True

def get_sensor_data():
    if get_mode() == "SIMULATED":
        from simulator import get_simulated_data
        return get_simulated_data()

    response = requests.get(ESP_URL, timeout=5)
    response.raise_for_status()
    data = response.json()
    raw_turbidity = float(data.get("turbidity_raw", data.get("turbidity")))
    smoothed_raw = smooth_turbidity(raw_turbidity)
    adjusted_turbidity, was_adjusted = normalize_turbidity_for_demo(smoothed_raw)
    return {
        "ph": round(float(data["ph"]), 2),
        "temp": round(float(data["temp"] if "temp" in data else data["temperature"]), 2),
        "water": data["water"],
        "light": data["light"],
        "turbidity": adjusted_turbidity,
        "turbidity_raw": round(smoothed_raw, 2),
        "turbidity_adjusted": was_adjusted,
        "tds": round(float(data["tds"]), 2),
        "sample_type": "Hardware sample",
        "data_source": "SENSOR",
    }
