from news_api import get_news_data

def main():
    df = get_news_data("Port of Houston")

    print("Rows:", len(df))
    print(df.head())

    df.to_csv("houston_news.csv", index=False)
    print("Saved houston_news.csv")

if __name__ == "__main__":
    main()