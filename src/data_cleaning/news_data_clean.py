import pandas as pd
import json
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def clean_news_data(topic="AI"):
    """Clean the latest raw news file for the given topic."""
    files = sorted(RAW_DIR.glob(f"news_{topic}_*.json"))
    if not files:
        raise FileNotFoundError(f"No raw data found for topic '{topic}'")

    latest_file = files[-1]
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data.get("articles", [])
    df = pd.DataFrame(articles)

    # Basic cleanup
    df = df[["source", "author", "title", "description", "url", "publishedAt"]]
    df["source"] = df["source"].apply(lambda x: x["name"] if isinstance(x, dict) else x)
    df.drop_duplicates(subset=["title"], inplace=True)
    df.dropna(subset=["title", "url"], inplace=True)
    df["title"] = df["title"].str.strip()
    df["description"] = df["description"].str.strip()
    df["publishedAt"] = pd.to_datetime(df["publishedAt"]).dt.date

    # Save cleaned version
    output_file = PROCESSED_DIR / f"cleaned_news_{topic.lower().replace(' ', '_')}.csv"
    df.to_csv(output_file, index=False)
    print(f"✅ Cleaned data saved to {output_file}")
    return output_file
