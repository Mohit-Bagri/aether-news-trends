import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="🧠 Aether - News Insights", layout="wide")

# -----------------------------
# Load Data
# -----------------------------
processed_path = Path("data/processed/news_topics.csv")

if not processed_path.exists():
    st.error("❌ No processed data found! Please run NLP pipeline first.")
    st.stop()

df = pd.read_csv(processed_path)

st.title("🧠 Aether - AI News Trend Analyzer")
st.markdown("Explore trending topics, sources and insights from news articles.")

# -----------------------------
# Sidebar Filters
# -----------------------------
sources = df["source"].dropna().unique().tolist()
selected_sources = st.sidebar.multiselect("Filter by Source", sources, default=sources)

filtered_df = df[df["source"].isin(selected_sources)]

# -----------------------------
# Topic Overview
# -----------------------------
st.header("🧩 Topic Clusters")

topic_counts = filtered_df["topic"].value_counts().sort_index()
fig = px.bar(
    x=topic_counts.index,
    y=topic_counts.values,
    labels={"x": "Topic", "y": "Article Count"},
    title="Articles per Topic"
)
st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Top Sources
# -----------------------------
st.header("🏁 Top Sources")
top_sources = filtered_df["source"].value_counts().head(10)
fig2 = px.pie(values=top_sources.values, names=top_sources.index, title="Top 10 Sources")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Article Explorer
# -----------------------------
st.header("📰 Explore Articles by Topic")

topic_choice = st.selectbox("Choose a Topic", sorted(filtered_df["topic"].unique()))
topic_articles = filtered_df[filtered_df["topic"] == topic_choice][["title", "url", "description"]]

for _, row in topic_articles.iterrows():
    st.markdown(f"### [{row['title']}]({row['url']})")
    st.write(row["description"])
    st.markdown("---")
