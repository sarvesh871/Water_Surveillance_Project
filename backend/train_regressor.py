"""Train the experimental synthetic disease-risk regressor.

Run: python train_regressor.py

The generated target is synthetic and based on water-quality indicators. Metrics
measure fit to that synthetic rule only; they do not validate real outbreak
forecasting. A chronological holdout is used when timestamps are available.
"""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "disease_risk_dataset.csv"
MODEL_PATH = BASE_DIR / "risk_regressor.pkl"
FEATURES = ["ph", "temperature", "turbidity"]
TARGET = "future_case_count"


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing {DATA_PATH.name}; run generate_risk_dataset.py first.")
    df = pd.read_csv(DATA_PATH)
    required = FEATURES + [TARGET]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing columns: {missing}")
    df = df[required + (["timestamp"] if "timestamp" in df.columns else [])].copy()
    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=required)
    if len(df) < 30:
        raise ValueError("At least 30 valid rows are required to train the risk model.")

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
        unique_dates = sorted(df["timestamp"].dt.normalize().unique())
        split_index = max(1, min(len(unique_dates) - 1, int(len(unique_dates) * 0.8)))
        cutoff = pd.Timestamp(unique_dates[split_index])
        train_df = df[df["timestamp"] < cutoff]
        test_df = df[df["timestamp"] >= cutoff]
        split_description = f"chronological holdout; test starts {cutoff.date()}"
    else:
        # Deterministic fallback only when the dataset truly has no timestamp.
        split_index = int(len(df) * 0.8)
        train_df, test_df = df.iloc[:split_index], df.iloc[split_index:]
        split_description = "ordered 80/20 holdout (no timestamp column)"

    if train_df.empty or test_df.empty:
        raise ValueError("Could not form non-empty chronological train/test sets.")
    X_train, y_train = train_df[FEATURES], train_df[TARGET]
    X_test, y_test = test_df[FEATURES], test_df[TARGET]

    model = RandomForestRegressor(
        n_estimators=300, max_depth=12, min_samples_leaf=3,
        random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    print(f"Rows: {len(df)} | train: {len(train_df)} | test: {len(test_df)}")
    print(f"Evaluation split: {split_description}")
    print(f"MAE: {mean_absolute_error(y_test, predictions):.3f} cases")
    print(f"RMSE: {mean_squared_error(y_test, predictions) ** 0.5:.3f} cases")
    print(f"R²: {r2_score(y_test, predictions):.3f}")
    print("WARNING: this score evaluates synthetic data only, not real-world outbreaks.")
    print(pd.DataFrame({"Feature": FEATURES, "Importance": model.feature_importances_}).to_string(index=False))
    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
