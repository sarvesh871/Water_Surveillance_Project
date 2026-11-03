from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ESP_URL = "http://192.168.100.1/data"
CSV_FILE = str(BASE_DIR / "water_data.csv")
MODEL_FILE = str(BASE_DIR / "water_classifier.pkl")
RISK_MODEL_FILE = str(BASE_DIR / "risk_regressor.pkl")
COLLECTION_INTERVAL = 10
DEFAULT_READING_MODE = "SENSOR"  # SENSOR or SIMULATED
STALE_AFTER_SECONDS = max(3 * COLLECTION_INTERVAL, 30)
