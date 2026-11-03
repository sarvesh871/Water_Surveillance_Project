from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from predictor import validate_readings

tests = [
    ("Normal screening example", 7.0, 80, 0.5, 25),
    ("High pH", 12.37, 81, 2.58, 20),
    ("Impossible pH", 32.33, 70, 2.58, 20),
    ("High TDS", 7.0, 2500, 0.5, 25),
    ("High turbidity", 7.0, 80, 8.0, 25),
    ("Invalid temperature", 7.0, 80, 0.5, 100),
]

for name, ph, tds, turbidity, temp in tests:
    status, reasons = validate_readings(ph, tds, turbidity, temp)

    print(f"\n{name}: {status}")

    for reason in reasons:
        print(f"  - {reason}")
