
import pandas as pd
from pathlib import Path

file_path = Path("disease_risk_dataset.csv")

if not file_path.exists():
    raise FileNotFoundError(
        "disease_risk_dataset.csv was not found in the current folder."
    )

df = pd.read_csv(file_path)

print("\n--- DATASET SHAPE ---")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")

print("\n--- COLUMN NAMES ---")
print(df.columns.tolist())

print("\n--- FIRST FIVE ROWS ---")
print(df.head().to_string(index=False))

print("\n--- DATA TYPES ---")
print(df.dtypes.to_string())

print("\n--- MISSING VALUES ---")
print(df.isnull().sum().to_string())

print("\n--- NUMERIC SUMMARY ---")
print(df.describe(include="number").round(3).to_string())

print("\n--- DUPLICATE ROWS ---")
print(df.duplicated().sum())

if "timestamp" in df.columns:
    timestamps = pd.to_datetime(df["timestamp"], errors="coerce")
    print("\n--- TIMESTAMP COVERAGE ---")
    print(f"Valid timestamps: {timestamps.notna().sum()}")
    print(f"First timestamp: {timestamps.min()}")
    print(f"Last timestamp: {timestamps.max()}")

if "future_case_count" in df.columns:
    print("\n--- TARGET DISTRIBUTION ---")
    print(df["future_case_count"].describe().to_string())
    print(
        "Unique target values:",
        df["future_case_count"].nunique()
    )
