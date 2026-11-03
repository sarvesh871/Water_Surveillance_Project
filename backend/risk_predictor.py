"""Disease-risk model inference helpers.

The current regressor is trained on a synthetic dataset. Its output is an
experimental case-count estimate, not a validated disease forecast or probability.
"""
from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent / "risk_regressor.pkl"
DATASET_MAX_CASES = 81.0
_FEATURES = ["ph", "temperature", "turbidity"]
_model = None


def _load_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}. Run train_regressor.py first."
            )
        _model = joblib.load(MODEL_PATH)
    return _model


def risk_score_from_cases(cases):
    """Normalize the synthetic predicted case count to 0..1, not a probability."""
    return round(min(max(float(cases), 0.0) / DATASET_MAX_CASES, 1.0), 2)


def get_risk_level(cases):
    """Derive category from the same normalized score shown on the dashboard."""
    score = risk_score_from_cases(cases)
    if score <= 0.10:
        return "Very Low"
    if score <= 0.20:
        return "Low"
    if score <= 0.40:
        return "Moderate"
    if score <= 0.70:
        return "High"
    return "Critical"


def predict_future_cases(ph, temperature, turbidity):
    """Return (estimated_cases, risk_level) for compatibility with app.py."""
    values = [ph, temperature, turbidity]
    if any(value is None for value in values):
        raise ValueError("pH, temperature, and turbidity are required for risk estimation.")
    X = pd.DataFrame([{
        "ph": float(ph),
        "temperature": float(temperature),
        "turbidity": float(turbidity),
    }], columns=_FEATURES)
    predicted = float(_load_model().predict(X)[0])
    predicted = round(min(max(predicted, 0.0), DATASET_MAX_CASES))
    return int(predicted), get_risk_level(predicted)
