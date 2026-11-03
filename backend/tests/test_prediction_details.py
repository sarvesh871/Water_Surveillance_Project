from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from predictor import predict_water_details

result = predict_water_details(
    ph=12.37,
    turbidity=2.58,
    tds=81.03,
    temperature=10.56,
)

print(result)
