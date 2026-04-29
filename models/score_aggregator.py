from predict_congestion import get_congestion_score

def get_final_port_score(port_name):
    scores = []

    # Throughput Statistical Model
    throughput_congestion_score = get_congestion_score(port_name)
    scores.append(throughput_congestion_score)

    # Your models go here
    # scores.append(predict_crime_score(port_name))
    # scores.append(predict_news_score(port_name))

    final_score = sum(scores) / len(scores)

    # Rounding
    return round(final_score, 2)