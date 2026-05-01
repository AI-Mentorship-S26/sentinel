from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import all model scoring functions
from predict_congestion import get_congestion_score
from predict_crime_score import predict_crime_score
from predict_risk import run_sentinel_assessment
from ship_detection import detect_latest
from portcongestion import score_port

# Precompute satellite scores for all ports at startup
_satellite_cache = {}

def _preload_satellite_scores():
    print("[CACHE] Starting preload...")
    from ports_config import get_all_port_names
    for port_name in get_all_port_names():
        try:
            result = detect_latest(port_name)
            _satellite_cache[port_name] = result.get("congestion_score", 0.0)
            print(f"[CACHE] {port_name} → {_satellite_cache[port_name]}")
        except Exception as e:
            _satellite_cache[port_name] = 0.0
    print(f"[CACHE] All {len(_satellite_cache)} ports preloaded.")

_preload_satellite_scores()


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

    satellite_score = _satellite_cache.get(port_name, 0.0)
    scores.append(satellite_score)
    print("Satellite Score:", satellite_score, type(satellite_score))


       # News Statistical Model 
    _, _, _, summary = score_port(port_name)

    if summary:
        news_score = summary.get("port_score", 0) / 100  # Convert to 0.0-1.0 scale
    else:
        news_score = 0
    print(f"News Score: {news_score} {type(news_score)}")
    scores.append(news_score)


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

    # Satellite Ship Detection Score (preloaded)
    

    final_score = (
        0.65 * throughput_congestion_score +
        0.30 * ml_score +
        0.10 * crime_score +
        0.50 * satellite_score +
        0.30 * news_score
        
)

    # Rounding
    return round(final_score, 2)