import pandas as pd
import json
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

latest_file = sorted(RAW_DIR.glob("news_*.json"))[-1]
with open(latest_file, "r", encoding="utf-8") as f:
    data = json.load(f)

articles = data.get("articles")

df = pd.DataFrame(articles)

df = df[["source", "author", "title", "description", "url", "publishedAt"]]

df["source"] = df["source"].apply(lambda x: x["name"] if isinstance(x, dict) else x)

df.drop_duplicates(subset=["title"], inplace=True)
df.dropna(subset=["title", "url"], inplace=True)

df["title"] = df["title"].str.strip()
df["description"] = df["description"].str.strip()
df["publishedAt"] = pd.to_datetime(df["publishedAt"]).dt.date

output_file = PROCESSED_DIR / "cleaned_news.csv"
df.to_csv(output_file, index=False)

print(f"Cleaned data saved to {output_file}")
