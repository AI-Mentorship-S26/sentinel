from data_sources.news_api import get_processed_news_data

df = get_processed_news_data(limit=5)
from data_sources.news_api import get_processed_news_data

df = get_processed_news_data(limit=50)

# save to CSV
df.to_csv("processed_news.csv", index=False)

print(df.head())

print(df.head())