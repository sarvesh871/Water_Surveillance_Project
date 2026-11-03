from datetime import datetime
from threading import Lock
from flask import Flask, request, redirect, url_for, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from collector import get_sensor_data
from predictor import predict_water_details
from storage import save
from dashboard import render
from config import COLLECTION_INTERVAL, STALE_AFTER_SECONDS
from mode_state import get_mode, set_mode
from risk_predictor import risk_score_from_cases, get_risk_level, predict_future_cases

app = Flask(__name__)
LATEST = {}
LAST_ERROR = None
LAST_SUCCESS_AT = None
_COLLECTION_LOCK = Lock()


def _safe_float(data, key, fallback=None):
    value = data.get(key, fallback)
    if value is None:
        raise ValueError(f"Required reading '{key}' is missing.")
    return float(value)


def collect():
    """Collect and save one reading; keep app alive when a sensor/model fails."""
    global LATEST, LAST_ERROR, LAST_SUCCESS_AT
    if not _COLLECTION_LOCK.acquire(blocking=False):
        return {"status": "skipped", "reason": "collection already in progress"}
    try:
        data = get_sensor_data()
        required = ("ph", "temp", "turbidity", "tds", "water", "light")
        missing = [key for key in required if key not in data or data[key] is None]
        if missing:
            raise ValueError("Missing required sensor fields: " + ", ".join(missing))

        # Normalize numeric sensor values before calling either model.
        for key in ("ph", "temp", "turbidity", "tds"):
            data[key] = _safe_float(data, key)
        for key in ("water", "light"):
            try:
                data[key] = float(data[key])
            except (TypeError, ValueError):
                raise ValueError(f"Sensor field '{key}' is not numeric.")

        prediction_details = predict_water_details(
            data["ph"], data["turbidity"], data["tds"], data["temp"]
        )
        prediction = prediction_details["prediction"]
        expected_cases, risk_score, risk_level = None, None, "Unavailable"
        risk_error = None
        if prediction_details["validation_status"] != "SENSOR_ERROR":
            try:
                expected_cases, _ = predict_future_cases(data["ph"], data["temp"], data["turbidity"])
                risk_score = risk_score_from_cases(expected_cases)
                # Use the same helper as the risk model so score/category cannot drift.
                risk_level = get_risk_level(expected_cases)
            except Exception as exc:
                risk_error = str(exc)

        now = datetime.now()
        row = {
            "timestamp": now.strftime("%d %b %Y %H:%M:%S"),
            **data,
            "reading_mode": get_mode(),
            "expected_cases": expected_cases,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "prediction": prediction,
            "validation_status": prediction_details["validation_status"],
            "prediction_reasons": prediction_details["reasons"],
            "risk_error": risk_error,
        }
        save(row)
        LATEST = row.copy()
        LAST_SUCCESS_AT = now.isoformat(timespec="seconds")
        LAST_ERROR = None

        print("=" * 60)
        print(f"NEW READING ({row.get('data_source', get_mode())})")
        print("=" * 60)
        print(f"Time           : {row['timestamp']}")
        print(f"pH             : {row['ph']}")
        print(f"Temperature    : {row['temp']} °C")
        if row.get("data_source") == "SENSOR":
            note = " (demo-adjusted; not calibrated NTU)" if row.get("turbidity_adjusted") else " (raw value passed through)"
            print(f"Turbidity      : {row['turbidity']}{note}")
            print(f"Turbidity raw  : {row.get('turbidity_raw', 'unavailable')}")
        else:
            print(f"Turbidity      : {row['turbidity']} NTU (simulated)")
        print(f"TDS            : {row['tds']} ppm")
        print(f"Prediction     : {row['prediction']}")
        print(f"Expected Cases : {row['expected_cases']}")
        print(f"Risk Score     : {row['risk_score']}")
        print(f"Risk Level     : {row['risk_level']}")
        print("=" * 60)
        return {"status": "ok", "reading": row}
    except Exception as exc:
        LAST_ERROR = f"{type(exc).__name__}: {exc}"
        print(f"Collection failed ({get_mode()}): {LAST_ERROR}")
        return {"status": "error", "error": LAST_ERROR}
    finally:
        _COLLECTION_LOCK.release()


@app.route("/")
def home():
    return render(LATEST, last_error=LAST_ERROR, last_success_at=LAST_SUCCESS_AT)


@app.route("/collect", methods=["GET", "POST"])
def manual():
    result = collect()
    code = 200 if result.get("status") in ("ok", "skipped") else 503
    return jsonify(result), code


@app.route("/mode", methods=["POST"])
def change_mode():
    requested_mode = request.form.get("mode", "")
    try:
        set_mode(requested_mode)
    except ValueError:
        return "Invalid mode. Choose SENSOR or SIMULATED.", 400
    return redirect(url_for("home"))


@app.route("/health")
def health():
    age_seconds = None
    if LAST_SUCCESS_AT:
        age_seconds = max(0, int((datetime.now() - datetime.fromisoformat(LAST_SUCCESS_AT)).total_seconds()))
    healthy = LAST_ERROR is None and age_seconds is not None and age_seconds <= STALE_AFTER_SECONDS
    return jsonify({
        "status": "ok" if healthy else "degraded",
        "mode": get_mode(),
        "last_success_at": LAST_SUCCESS_AT,
        "seconds_since_last_success": age_seconds,
        "stale_after_seconds": STALE_AFTER_SECONDS,
        "last_error": LAST_ERROR,
    }), (200 if healthy else 503)


if __name__ == "__main__":
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(collect, "interval", seconds=COLLECTION_INTERVAL, max_instances=1, coalesce=True)
    scheduler.start()
    try:
        app.run(debug=True, use_reloader=False)
    finally:
        scheduler.shutdown(wait=False)
