from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""Smoke tests for recent-history storage and dashboard trend rendering."""
from pathlib import Path
import tempfile
import storage
from dashboard import render

def main():
    original_path = storage.CSV_FILE
    with tempfile.TemporaryDirectory() as tmp:
        storage.CSV_FILE = str(Path(tmp) / "test_water_data.csv")
        try:
            for i in range(3):
                storage.save({
                    "timestamp": f"21 Oct 2026 15:00:{i:02d}",
                    "ph": 7.2 + i * 0.01,
                    "temp": 24 + i,
                    "turbidity": 0.4 + i * 0.1,
                    "tds": 80 + i,
                    "risk_score": 0.1 + i * 0.05,
                    "risk_level": "Low",
                    "prediction": "Potable",
                    "data_source": "SIMULATED",
                    "sample_type": "Clean water",
                })
            history = storage.get_history(60)
            assert len(history) == 3
            assert history[0]["timestamp"].endswith("00")
            assert history[-1]["tds"] == 82
            html = render({
                "timestamp": "21 Oct 2026 15:00:02",
                "ph": 7.22, "temp": 26, "water": 1, "light": 10,
                "turbidity": 0.6, "tds": 82, "prediction": "Potable",
                "risk_score": 0.2, "risk_level": "Low", "expected_cases": 16,
                "validation_status": "VALID", "prediction_reasons": [],
                "data_source": "SIMULATED", "sample_type": "Clean water",
            })
            assert "Recent Trends" in html
            assert "TDS trend" in html
            assert "Recent Readings" in html
            assert "TDS (ppm)" in html
            print("PASS: storage order, TDS history, and dashboard charts render.")
        finally:
            storage.CSV_FILE = original_path

if __name__ == "__main__":
    main()
