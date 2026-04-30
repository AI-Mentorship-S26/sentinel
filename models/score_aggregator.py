from predict_congestion import get_congestion_score
from predict_crime_score import predict_crime_score
from predict_risk import run_sentinel_assessment

def get_final_port_score(port_name):
    scores = []

    # Throughput Statistical Model
    throughput_congestion_score = get_congestion_score(port_name)
    scores.append(throughput_congestion_score)

    # Your models go here
    scores.append(predict_crime_score(port_name))
    # scores.append(predict_news_score(port_name))
    ml_result = run_sentinel_assessment(port_name)
    if ml_result:
        # Convert 0-100 scale to 0.0-1.0 scale to match congestion
        ml_score_normalized = ml_result.get("risk_score_numeric", 0) / 100
        scores.append(ml_score_normalized)
    final_score = sum(scores) / len(scores)

    # Rounding
    return round(final_score, 2)