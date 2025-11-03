import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from pathlib import Path

DATA_PATH = Path("data/processed/news_nlp_ready.csv")
OUTPUT_PATH = Path("data/processed/news_topics.csv")
df = pd.read_csv(DATA_PATH)

print(f"🔍 Loaded {len(df)} articles")

if len(df) < 3:
    print("⚠️ Not enough data for topic modeling — need at least 3 articles.")
    exit()

# 🧩 Dynamic parameter adjustment
n_docs = len(df)
min_df = 1 if n_docs < 20 else 5
max_df = 0.95 if n_docs < 50 else 0.8
k = 2 if n_docs < 20 else min(10, n_docs // 10)

print(f"⚙️ Using parameters -> min_df={min_df}, max_df={max_df}, clusters={k}")

# 🧮 TF-IDF Vectorization
vectorizer = TfidfVectorizer(
    max_df=max_df,
    min_df=min_df,
    stop_words='english',
    max_features=1000
)

X = vectorizer.fit_transform(df["clean_text"])


kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
df["topic"] = kmeans.fit_predict(X)

terms = vectorizer.get_feature_names_out()
topic_keywords = {}

for i in range(k):
    indices = kmeans.cluster_centers_[i].argsort()[-10:][::-1]
    topic_keywords[i] = [terms[idx] for idx in indices]

# 5️⃣ Save results
df.to_csv(OUTPUT_PATH, index=False)
print(f"✅ Topic modeling complete. Results saved to {OUTPUT_PATH}\n")

for topic, keywords in topic_keywords.items():
    print(f"🧩 Topic {topic}: {', '.join(keywords)}")

