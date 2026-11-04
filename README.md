# IoT-Enabled Smart Health Surveillance and Early Warning System for Water-Borne Disease Prediction in Vulnerable Communities

**Project Stage:** Major Project Stage-II  
**Department:** Computer Engineering  
**Institute:** R. C. Patel Institute of Technology, Shirpur, Maharashtra, India  
**Academic Year:** 2026–27

## Repository contents

```text
Water_Surveillance_Project/
├── README.md
├── requirements.txt
├── .gitignore
├── backend/
│   ├── app.py
│   ├── collector.py
│   ├── config.py
│   ├── dashboard.py
│   ├── predictor.py
│   ├── risk_predictor.py
│   ├── storage.py
│   ├── mode_state.py
│   ├── simulator.py
│   ├── train_classifier.py
│   ├── compare_classifiers.py
│   ├── train_regressor.py
│   ├── generate_risk_dataset.py
│   ├── inspect_risk_dataset.py
│   ├── water_classifier.pkl
│   ├── risk_regressor.pkl
│   ├── water_data.csv
│   ├── water_quality_dataset1.csv
│   ├── water_potability.csv
│   ├── disease_risk_dataset.csv
│   └── tests/
├── hardware/
│   └── esp32/
│       └── water_esp.ino
└── docs/
    ├── DATA_AND_MODEL_NOTES.md
    └── PACKAGE_INVENTORY.md
```

Backend scripts, datasets, and model files are kept together in `backend/` because the current code expects these files relative to the backend scripts. This layout avoids unnecessary path changes that could disrupt the existing prototype.

## Project overview

The current prototype includes:

1. ESP32 sensor acquisition using the firmware in `hardware/esp32/water_esp.ino`.
2. Sensor readings for pH, water level, light, temperature, turbidity, and TDS-related values, subject to the current hardware configuration.
3. An ESP32 Wi-Fi access point and HTTP endpoint.
4. A Python/Flask backend running on a laptop or PC.
5. Local CSV-based storage.
6. Water-quality classification and a separate experimental synthetic risk-index workflow.
7. A browser-based monitoring dashboard.

**An Android application is not included in this project version.**

## Hardware and firmware

### ESP32 access point

The firmware configures the ESP32 as a Wi-Fi access point:

| Setting | Value |
|---|---|
| SSID | `ESP_WiFi` |
| Demo password | `12341234` |
| ESP32 IP address | `192.168.100.1` |
| Sensor endpoint | `http://192.168.100.1/data` |
| Status endpoint | `http://192.168.100.1/status` |

The password is embedded in the demo firmware. Change it before use outside a controlled demonstration and do not reuse it for other networks or accounts.

### Sensor pins configured in firmware

| Sensor/interface | ESP32 configuration |
|---|---|
| 4-in-1 sensor UART | UART2, RX GPIO16, TX GPIO17 |
| Turbidity analog input | GPIO34 |
| TDS analog input | GPIO35 |

Check module wiring and voltage requirements before powering the circuit. ESP32 GPIO pins are not 5 V tolerant.

## Software requirements

- Python 3.10 or a compatible Python version supported by the dependencies
- Arduino IDE with ESP32 board support
- ESP32 board and USB cable
- Laptop/PC with Wi-Fi
- Web browser

## Backend setup

Run the commands from the repository root.

### 1. Create and activate a virtual environment

**macOS/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the Flask backend

```bash
cd backend
python app.py
```

Open the dashboard on the same computer:

```text
http://127.0.0.1:5000/
```

The backend collects readings at the configured interval while running (currently 10 seconds by default). In sensor mode, the ESP32 must be powered on and the laptop must be connected to its `ESP_WiFi` access point.

### 4. Sensor and simulation modes

The default reading mode is `SENSOR`, configured in `backend/config.py`.

The dashboard supports `SENSOR` and `SIMULATED` modes. Simulation is for software demonstration/testing; simulated readings must not be presented as actual sensor measurements.

## Arduino firmware setup

1. Open `hardware/esp32/water_esp.ino` in Arduino IDE.
2. Select the appropriate ESP32 board and serial port.
3. Verify sensor wiring and voltage requirements.
4. Upload the firmware.
5. Open Serial Monitor at **115200 baud**.
6. Connect the laptop to the ESP32 access point.
7. Open `http://192.168.100.1/` to view the ESP32's built-in sensor page, or start the Flask backend.

The 4-in-1 UART sensor is configured at **9600 baud** on UART2 (GPIO16/GPIO17).

## Data files and dataset attribution

The datasets used by the project are listed below. Dataset source attribution is provided in the references section.

| File | Purpose | Source / attribution |
|---|---|---|
| `backend/water_data.csv` | Prototype sensor/backend log | Collected/generated during project operation; not an external dataset |
| `backend/water_quality_dataset1.csv` | Water-quality classifier dataset | Ooko et al., *Water Quality Dataset from Water Sources in Kenya*, Mendeley Data, Version 2 [1] |
| `backend/water_potability.csv` | Additional potability dataset retained from project work | MainakRepositor/Datasets GitHub repository [2] |
| `backend/disease_risk_dataset.csv` | Experimental risk-regression dataset | Synthetic dataset generated by this project’s `generate_risk_dataset.py`; not real epidemiological records |

The saved model artifacts are:

- `backend/water_classifier.pkl`: trained classification pipeline/artifact.
- `backend/risk_regressor.pkl`: trained regression model.

Do not delete or rename datasets or model files without updating the scripts that load them. The current scripts expect these files in the `backend/` directory.

### Dataset references

**[1]** Ooko, Samson Otieno; Cheptegei, Laura; Karume, Simon. (2026). *Water Quality Dataset from Water Sources in Kenya*. Mendeley Data, Version 2. https://doi.org/10.17632/575ctg3nnr.2

**[2]** MainakRepositor. *Datasets: water_potability.csv*. GitHub repository. https://github.com/MainakRepositor/Datasets/blob/master/water_potability.csv

**Dataset usage note:** Please review each source’s license and terms before redistributing the dataset files publicly. Attribution in this README does not itself grant redistribution rights. If a dataset’s terms do not permit redistribution, remove the dataset file from the public GitHub repository and provide instructions for obtaining it from the original source instead.

## Training and retraining

Run training scripts from the backend directory:

```bash
cd backend
python train_classifier.py
python train_regressor.py
```

Regenerate the synthetic risk dataset with:

```bash
python generate_risk_dataset.py
```

**Warning:** These operations may overwrite existing dataset/model files. Back up files first if you need to preserve the supplied results.

## Tests and diagnostic scripts

Run the lightweight tests from the repository root:

```bash
python backend/tests/test_validation.py
python backend/tests/test_prediction_details.py
python backend/tests/test_dashboard_storage.py
```

`test_sensor.py` attempts to communicate with the ESP32 and should only be run while the device is powered on and reachable:

```bash
python backend/tests/test_sensor.py
```

These checks are not a complete test suite and do not establish water-safety validity.

## Scientific and prototype limitations

- This is an academic prototype, not a certified drinking-water testing device.
- Comprehensive calibration against laboratory/reference instruments has not been established.
- Turbidity values may be raw ADC or software-adjusted values. They must not be described as calibrated NTU measurements without appropriate calibration.
- Classification results depend on the source dataset, its labels, and its feature distribution. They do not certify water as safe to drink or establish performance on independent real-world samples.
- The risk dataset and target are synthetic. The output is a normalized demonstration index, **not a disease probability or epidemiological outbreak forecast**.
- Dashboard outputs are intended for educational/prototype evaluation and must not be used as the sole basis for drinking-water or public-health decisions.

See [`docs/DATA_AND_MODEL_NOTES.md`](docs/DATA_AND_MODEL_NOTES.md) for additional model and data interpretation notes.

## Student team

- Fegade Nikhil Vijay
- Dorik Rupesh Girish
- Dhande Sarvesh Gopal
- Patil Laghvi Ashok

Department of Computer Engineering, R. C. Patel Institute of Technology, Shirpur, Maharashtra, India.
