from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import all model scoring functions
from predict_congestion import get_congestion_score
from predict_crime_score import predict_crime_score
from predict_risk import run_sentinel_assessment

def get_final_port_score(port_name):
    scores = []

    # Throughput Statistical Model
    throughput_congestion_score = get_congestion_score(port_name)
    # print("Throughput score:", throughput_congestion_score, type(throughput_congestion_score))
    scores.append(throughput_congestion_score)

    # Crime Statistical Model
    crime_score = predict_crime_score(port_name)
    print("Crime score:", crime_score, type(crime_score))
    scores.append(crime_score)

    # Vessel Tracking Model
    ml_result = run_sentinel_assessment(port_name) or {}
    ml_score = ml_result.get("risk_score_numeric", 0) / 100
    scores.append(ml_score)
    print("Vessel result:", ml_result)
    print("Vessel score normalized:", ml_score)

        # ml_score = run_sentinel_assessment(port_name)
        # print("Vessel tracking score:", ml_score, type(ml_score))
        # scores.append(ml_score)

        # if ml_result:
        #     # Convert 0-100 scale to 0.0-1.0 scale to match congestion
        #     ml_score_normalized = ml_result.get("risk_score_numeric", 0) / 100
        #     scores.append(ml_score_normalized)
    
    final_score = (
        0.65 * throughput_congestion_score +
        0.30 * ml_score +
        0.10 * crime_score
)

    # Rounding
    return round(final_score, 2)