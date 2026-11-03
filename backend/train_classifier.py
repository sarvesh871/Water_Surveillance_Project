"""
Train and compare water-safety classifiers from water_quality_dataset1.csv.

Run:
    python train_classifier.py

The model is saved as water_classifier.pkl. The dataset labels are Safe/Unsafe.
Very high random-split scores should not be interpreted as real-world validation,
especially when observations are repeated measurements from the same sources.
"""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.pipeline import Pipeline

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "water_quality_dataset1.csv"
MODEL_PATH = BASE_DIR / "water_classifier.pkl"

FEATURES = ["pH", "TDS_ppm", "Turbidity_NTU", "Temperature_C"]
TARGET = "Label"

def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DATASET_PATH.name}. Place it in the same folder as this script."
        )

    df = pd.read_csv(DATASET_PATH)
    required = FEATURES + [TARGET]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    # Keep optional metadata for a less leakage-prone split, if available.
    metadata = [column for column in ["timestamp", "source", "source_id", "site", "location"] if column in df.columns]
    df = df[required + metadata].copy()
    df[TARGET] = df[TARGET].astype(str).str.strip().str.title()
    df = df[df[TARGET].isin(["Safe", "Unsafe"])]
    for column in FEATURES:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=[TARGET]).reset_index(drop=True)
    X = df[FEATURES]
    y = df[TARGET]
    if y.nunique() != 2:
        raise ValueError(f"Expected Safe and Unsafe labels; found {sorted(y.unique())}")

    print(f"Rows used: {len(df):,}")
    print("Label counts:")
    print(y.value_counts().to_string())
    print(f"\nMissing feature values before imputation: {int(X.isna().sum().sum())}")
    duplicate_features = df.duplicated(subset=FEATURES, keep=False)
    if duplicate_features.any():
        duplicate_rows = int(duplicate_features.sum())
        conflicting = int((df.loc[duplicate_features].groupby(FEATURES)[TARGET].nunique() > 1).sum())
        print(f"Repeated feature rows: {duplicate_rows:,}; feature groups with conflicting labels: {conflicting:,}")
        print("Repeated rows can inflate random-split scores; interpret scores cautiously.")

    # Prefer testing on later dates or unseen source groups to reduce leakage.
    if "timestamp" in df.columns and df["timestamp"].notna().sum() > 1:
        dates = pd.to_datetime(df["timestamp"], errors="coerce")
        valid = dates.notna()
        df, X, y, dates = df.loc[valid].copy(), X.loc[valid].copy(), y.loc[valid].copy(), dates.loc[valid]
        unique_dates = sorted(dates.dt.normalize().unique())
        if len(unique_dates) >= 2:
            cutoff = pd.Timestamp(unique_dates[max(1, min(len(unique_dates)-1, int(len(unique_dates)*0.8)))])
            train_mask = dates < cutoff
            X_train, X_test = X.loc[train_mask], X.loc[~train_mask]
            y_train, y_test = y.loc[train_mask], y.loc[~train_mask]
            split_description = f"chronological holdout (test starts {cutoff.date()})"
        else:
            split_description = None
    else:
        split_description = None

    group_column = next((column for column in ["source_id", "source", "site", "location"] if column in df.columns and df[column].nunique() >= 2), None)
    if split_description is None and group_column:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_idx, test_idx = next(splitter.split(X, y, groups=df[group_column]))
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        split_description = f"unseen-source holdout using {group_column}"

    if split_description is None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )
        split_description = "stratified random row split (no date/source metadata available)"

    if X_train.empty or X_test.empty or y_train.nunique() < 2:
        raise ValueError("The selected split is too small or lacks both training labels. Check dataset metadata and label distribution.")
    print(f"Evaluation split: {split_description}")

    models = {
        "Random Forest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=2, class_weight="balanced",
            random_state=42, n_jobs=-1
        ),
        "Extra Trees": ExtraTreesClassifier(
            n_estimators=300, min_samples_leaf=2, class_weight="balanced",
            random_state=42, n_jobs=-1
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=150, learning_rate=0.1, max_leaf_nodes=31, random_state=42
        ),
    }

    results = []
    fitted = {}
    for name, estimator in models.items():
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", estimator),
        ])
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        metrics = {
            "name": name,
            "accuracy": accuracy_score(y_test, predictions),
            "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
            "macro_f1": f1_score(y_test, predictions, average="macro"),
        }
        results.append(metrics)
        fitted[name] = (pipeline, predictions)
        print(
            f"\n{name}\n"
            f"  Accuracy:          {metrics['accuracy']:.4f}\n"
            f"  Balanced accuracy: {metrics['balanced_accuracy']:.4f}\n"
            f"  Macro F1:           {metrics['macro_f1']:.4f}\n"
            f"  Confusion matrix (rows=true [Safe, Unsafe], columns=predicted [Safe, Unsafe]):\n"
            f"{confusion_matrix(y_test, predictions, labels=['Safe', 'Unsafe'])}\n"
        )

    best = max(results, key=lambda item: (item["macro_f1"], item["balanced_accuracy"]))
    best_pipeline, best_predictions = fitted[best["name"]]
    artifact = {
        "model": best_pipeline,
        "features": FEATURES,
        "labels": ["Safe", "Unsafe"],
        "model_name": best["name"],
        "test_metrics": {
            "accuracy": best["accuracy"],
            "balanced_accuracy": best["balanced_accuracy"],
            "macro_f1": best["macro_f1"],
        },
    }
    joblib.dump(artifact, MODEL_PATH)

    print("=" * 60)
    print(f"Selected model: {best['name']}")
    print(f"Saved model to: {MODEL_PATH}")
    print("\nClassification report for selected model:")
    print(classification_report(y_test, best_predictions, labels=["Safe", "Unsafe"], zero_division=0))
    print(
        "\nCAUTION: a random row split can leak source-specific patterns when readings are "
        "repeated over time. These metrics are a preliminary dataset test, not proof of "
        "drinking-water safety or generalization to unseen water sources."
    )

if __name__ == "__main__":
    main()
