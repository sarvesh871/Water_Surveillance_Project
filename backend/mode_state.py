from config import DEFAULT_READING_MODE

VALID_MODES = {"SENSOR", "SIMULATED"}
_current_mode = DEFAULT_READING_MODE if DEFAULT_READING_MODE in VALID_MODES else "SENSOR"

def get_mode():
    return _current_mode

def set_mode(mode):
    global _current_mode
    normalized = str(mode).strip().upper()
    if normalized not in VALID_MODES:
        raise ValueError(f"Unsupported reading mode: {mode}")
    _current_mode = normalized
    return _current_mode
