"""Synthetic readings for testing the existing shared software pipeline."""
import random

_reading_number = 0
_sample_type = "Soapy/cloudy water"
READINGS_PER_SCENARIO = 12

def get_simulated_data():
    global _reading_number, _sample_type
    if _reading_number and _reading_number % READINGS_PER_SCENARIO == 0:
        _sample_type = "Clean water" if _sample_type == "Soapy/cloudy water" else "Soapy/cloudy water"
    _reading_number += 1
    def noise(center, spread, digits=2):
        return round(random.gauss(center, spread), digits)
    if _sample_type == "Clean water":
        ph, tds, turbidity = noise(7.35, .05), max(0, noise(81, 2)), max(.1, noise(.65, .18))
    else:
        ph, tds, turbidity = noise(7.45, .08), max(0, noise(90, 4)), max(3, noise(8.5, 1.2))
    return {"ph": min(14, max(0, ph)), "temp": noise(25, .35),
            "water": random.choice([12, 13, 14]), "light": random.randint(0, 15),
            "turbidity": turbidity, "turbidity_raw": turbidity,
            "turbidity_adjusted": False, "tds": tds,
            "sample_type": _sample_type, "data_source": "SIMULATED"}
