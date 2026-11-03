from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

ESP_URL = "http://192.168.100.1/data"

try:
    response = requests.get(
        ESP_URL,
        timeout=5
    )
    print("ESP32 Connected")
    print(response.json())

except Exception as e:
    print("Connection Failed")
    print(e)