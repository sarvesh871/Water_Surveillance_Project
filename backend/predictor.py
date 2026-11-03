
"""
Water-quality prediction with input validation.

Returns one of:
- "Sensor Error"
- "Non-Potable"
- "Potable"
- "Needs Attention"

The rules are screening safeguards, not a laboratory safety certification.
"""

from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent / "water_classifier.pkl"

FEATURES = [
    "pH",
    "TDS_ppm",
    "Turbidity_NTU",
    "Temperature_C",
]

# Broad plausibility bounds to catch broken or malformed sensor readings.
PH_PLAUSIBLE = (0.0, 14.0)
TDS_PLAUSIBLE = (0.0, 100000.0)       # ppm
TURBIDITY_PLAUSIBLE = (0.0, 1000.0)   # NTU
TEMP_PLAUSIBLE = (-10.0, 80.0)        # degrees Celsius

# Screening limits based on BIS IS 10500.
PH_SCREEN = (6.5, 8.5)
TDS_PERMISSIBLE = 2000.0
TURBIDITY_PERMISSIBLE = 5.0

_artifact = None


def _load_model():
    global _artifact

    if _artifact is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}. "
                "Run train_classifier.py first."
            )

        _artifact = joblib.load(MODEL_PATH)

    return _artifact


def validate_readings(ph, tds, turbidity, temperature):
    """
    Return (status, reasons).

    status is:
      SENSOR_ERROR, NON_POTABLE, NEEDS_ATTENTION, or VALID
    """

    raw_values = {
        "pH": ph,
        "TDS": tds,
        "Turbidity": turbidity,
        "Temperature": temperature,
    }

    values = {}

    for name, value in raw_values.items():
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "SENSOR_ERROR", [f"{name} reading is missing or not numeric."]

        if not pd.notna(number) or number in (float("inf"), float("-inf")):
            return "SENSOR_ERROR", [f"{name} reading is missing or invalid."]

        values[name] = number

    # Impossible or implausible sensor values are rejected first.
    bounds = {
        "pH": PH_PLAUSIBLE,
        "TDS": TDS_PLAUSIBLE,
        "Turbidity": TURBIDITY_PLAUSIBLE,
        "Temperature": TEMP_PLAUSIBLE,
    }

    for name, (minimum, maximum) in bounds.items():
        value = values[name]
        if not minimum <= value <= maximum:
            return "SENSOR_ERROR", [
                f"{name} reading {value:g} is outside the configured "
                f"sensor-plausibility range ({minimum:g} to {maximum:g})."
            ]

    warnings = []

    if not PH_SCREEN[0] <= values["pH"] <= PH_SCREEN[1]:
        warnings.append(
            f"pH {values['pH']:.2f} is outside the screening range "
            f"{PH_SCREEN[0]}–{PH_SCREEN[1]}."
        )

    if values["TDS"] > TDS_PERMISSIBLE:
        warnings.append(
            f"TDS {values['TDS']:.1f} ppm exceeds the configured "
            f"{TDS_PERMISSIBLE:.0f} ppm permissible limit."
        )
    elif values["TDS"] > 500:
        warnings.append(
            "TDS exceeds 500 ppm, the BIS acceptable limit."
        )

    if values["Turbidity"] > TURBIDITY_PERMISSIBLE:
        warnings.append(
            f"Turbidity {values['Turbidity']:.2f} NTU exceeds "
            f"{TURBIDITY_PERMISSIBLE:.1f} NTU."
        )
    elif values["Turbidity"] > 1:
        warnings.append(
            "Turbidity exceeds 1 NTU, the BIS acceptable limit."
        )

    if warnings:
        # Beyond a permissible limit: fail the screening check.
        hard_fail = (
            not PH_SCREEN[0] <= values["pH"] <= PH_SCREEN[1]
            or values["TDS"] > TDS_PERMISSIBLE
            or values["Turbidity"] > TURBIDITY_PERMISSIBLE
        )

        if hard_fail:
            return "NON_POTABLE", warnings

        return "NEEDS_ATTENTION", warnings

    return "VALID", []


def predict_water(ph, turbidity, tds, temperature):
    """
    Compatible with the existing app.py call:
        predict_water(ph, turbidity, tds, temperature)

    Existing dashboard wording is preserved where possible.
    """

    status, reasons = validate_readings(
        ph=ph,
        tds=tds,
        turbidity=turbidity,
        temperature=temperature,
    )

    if status == "SENSOR_ERROR":
        return "Sensor Error"

    if status == "NON_POTABLE":
        return "Non-Potable"

    artifact = _load_model()
    model = artifact["model"] if isinstance(artifact, dict) else artifact

    row = pd.DataFrame([{
        "pH": float(ph),
        "TDS_ppm": float(tds),
        "Turbidity_NTU": float(turbidity),
        "Temperature_C": float(temperature),
    }], columns=FEATURES)

    label = str(model.predict(row)[0]).strip().title()

    # If a parameter exceeds an acceptable limit but remains within
    # the permissible screening limit, do not claim confidently safe.
    return "Potable" if label == "Safe" else "Non-Potable"


def predict_water_details(ph, turbidity, tds, temperature):
    """
    Return a prediction and explanations for the dashboard.
    """
    status, reasons = validate_readings(
        ph=ph,
        tds=tds,
        turbidity=turbidity,
        temperature=temperature,
    )

    prediction = predict_water(ph, turbidity, tds, temperature)

    # Keep the ML prediction and standards-based screening distinct. This avoids
    # implying that the classifier alone certifies drinking-water safety.
    if status == "NEEDS_ATTENTION" and prediction == "Potable":
        display_prediction = "Needs Attention"
    else:
        display_prediction = prediction

    return {
        "prediction": display_prediction,
        "model_prediction": prediction,
        "validation_status": status,
        "reasons": reasons,
    }
