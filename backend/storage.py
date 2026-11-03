import os
import threading
from pathlib import Path
import pandas as pd
from config import CSV_FILE

COLUMNS = [
    "timestamp", "ph", "temp", "water", "light", "turbidity", "tds",
    "expected_cases", "risk_score", "risk_level", "prediction",
    "sample_type", "data_source", "validation_status", "turbidity_raw",
    "turbidity_adjusted", "reading_mode", "prediction_reasons",
]
_WRITE_LOCK = threading.Lock()


def _read_existing():
    path = Path(CSV_FILE)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=COLUMNS)
    try:
        existing = pd.read_csv(path, on_bad_lines="skip")
    except (pd.errors.EmptyDataError, OSError):
        return pd.DataFrame(columns=COLUMNS)
    for column in COLUMNS:
        if column not in existing.columns:
            existing[column] = None
    return existing[COLUMNS]


def save(row):
    """Append one row while retaining compatibility with older CSV schemas."""
    normalized = {column: row.get(column, None) for column in COLUMNS}
    new_row = pd.DataFrame([normalized], columns=COLUMNS)
    path = Path(CSV_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _WRITE_LOCK:
        existing = _read_existing()
        combined = new_row if existing.empty else pd.concat([existing, new_row], ignore_index=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        combined.to_csv(temp_path, index=False)
        os.replace(temp_path, path)


def get_recent(limit=10):
    if limit <= 0:
        return []
    with _WRITE_LOCK:
        existing = _read_existing()
    return existing.tail(limit).iloc[::-1].where(pd.notna(existing.tail(limit).iloc[::-1]), None).to_dict("records")


def get_history(limit=60, data_source=None):
    """Return chronological records for charts; optionally filter by source."""
    if limit <= 0:
        return []
    with _WRITE_LOCK:
        df = _read_existing()
    if data_source:
        df = df[df["data_source"] == data_source]
    df = df.tail(limit).copy()
    if "timestamp" in df.columns:
        df["timestamp"] = df["timestamp"].astype(str)
    return df.where(pd.notna(df), None).to_dict("records")
