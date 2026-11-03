"""Generate a reproducible synthetic dataset for demonstrating risk-model flow.

This is not epidemiological evidence. The target is a synthetic case-count proxy
constructed from water-quality features so the regression task is learnable and
its limitations are explicit.
"""
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

NUM_VILLAGES = 10
DAYS_PER_VILLAGE = 365
START_DATE = datetime(2025, 1, 1)
SEED = 42
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "disease_risk_dataset.csv"

VILLAGES = [
    ("Village_A", 21.1458, 79.0882), ("Village_B", 21.1735, 79.1041),
    ("Village_C", 21.1586, 79.0652), ("Village_D", 21.1941, 79.1210),
    ("Village_E", 21.1124, 79.0748), ("Village_F", 21.1308, 79.1321),
    ("Village_G", 21.2017, 79.0923), ("Village_H", 21.1702, 79.0587),
    ("Village_I", 21.1864, 79.1475), ("Village_J", 21.1206, 79.1016),
]


def main():
    rng = np.random.default_rng(SEED)
    rows = []
    for village_index, (village, lat, lon) in enumerate(VILLAGES):
        village_ph_offset = rng.normal(0, 0.12)
        village_tds_offset = rng.normal(0, 0.08)
        turbidity = rng.uniform(0.6, 2.0)
        for day in range(DAYS_PER_VILLAGE):
            date = START_DATE + timedelta(days=day)
            seasonal = np.sin(2 * np.pi * (day / 365.0))
            temperature = float(np.clip(27 + 5 * seasonal + rng.normal(0, 1.2), 18, 40))
            ph = float(np.clip(7.1 + village_ph_offset + rng.normal(0, 0.12), 5.0, 9.8))

            # Slow drift plus occasional synthetic contamination spikes.
            turbidity = float(np.clip(0.97 * turbidity + rng.normal(0, 0.22), 0.4, 35))
            if rng.random() < 0.025:
                turbidity = min(35.0, turbidity + rng.uniform(2.0, 9.0))
            # Occasional recovery to baseline prevents the series sticking high forever.
            if turbidity > 4 and rng.random() < 0.22:
                turbidity = max(0.7, turbidity * rng.uniform(0.45, 0.75))

            # Synthetic hazard proxy, bounded to 0..1.
            ph_component = min(abs(ph - 7.0) / 2.5, 1.0)
            turbidity_component = min(turbidity / 10.0, 1.0)
            temperature_component = min(max((temperature - 22.0) / 10.0, 0.0), 1.0)
            hazard = float(np.clip(
                0.40 * turbidity_component + 0.25 * ph_component + 0.35 * temperature_component,
                0, 1,
            ))
            # Synthetic expected-case proxy. Noise is intentionally limited so the
            # model learns a relationship, but it is not a real disease-case forecast.
            future_cases = int(np.clip(round(hazard * 81 + rng.normal(0, 2.0)), 0, 81))
            rows.append({
                "timestamp": date.strftime("%Y-%m-%d"),
                "village": village,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "ph": round(ph, 2),
                "temperature": round(temperature, 2),
                "turbidity": round(turbidity, 2),
                "future_case_count": future_cases,
                "target_type": "SYNTHETIC_PROXY",
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Generated {len(df):,} synthetic rows: {OUTPUT_PATH}")
    print("Target range:", int(df.future_case_count.min()), "to", int(df.future_case_count.max()))
    print("Target mean:", round(float(df.future_case_count.mean()), 2))
    print("WARNING: synthetic target only; do not report model metrics as real outbreak accuracy.")


if __name__ == "__main__":
    main()
