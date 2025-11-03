import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Import project modules
from src.data_ingest.fetch_news import fetch_and_save_news
from src.data_cleaning.news_data_clean import clean_news_data
from src.nlp.preprocess_text import main as preprocess_text
from src.nlp.topic_modeling import main as topic_modeling

# -----------------------------
# File paths
# -----------------------------
LAST_TOPIC_FILE = Path("data/last_topic.txt")
LAST_TOPIC_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_last_topic():
    return LAST_TOPIC_FILE.read_text().strip() if LAST_TOPIC_FILE.exists() else "AI"

def save_last_topic(topic):
    LAST_TOPIC_FILE.write_text(topic)

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(page_title="🧠 Aether - News Insights", layout="wide")
st.title("🧠 Aether - AI News Trend Analyzer")
st.markdown("Explore trending topics, sources, and insights from the latest news articles.")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("⚙️ News Settings")
user_topic = st.sidebar.text_input("Enter a topic to analyze", value=load_last_topic())

# Dynamic processed file name
topic_filename = f"news_topics_{user_topic.lower().replace(' ', '_')}.csv"
processed_path = Path(f"data/processed/{topic_filename}")

# Run pipeline button
run_pipeline = st.sidebar.button("🚀 Run Analysis")

# If user topic changed and we already have data for it, sync automatically
if user_topic != load_last_topic() and processed_path.exists():
    save_last_topic(user_topic)
    st.rerun()

# -----------------------------
# Run NLP Pipeline
# -----------------------------
if run_pipeline:
    st.info(f"📰 Fetching and analyzing fresh news for topic: **{user_topic}** ...")

    # Step 1: Fetch latest news
    fetch_and_save_news(user_topic)

    # Step 2: Clean the fetched data
    clean_news_data(user_topic)

    # Step 3: NLP preprocessing
    preprocess_text(user_topic)

    # Step 4: Topic modeling
    topic_modeling( topic=user_topic)


    save_last_topic(user_topic)
    st.success("✅ NLP pipeline completed! Displaying results...")
    st.rerun()  # Reload dashboard with new data

# -----------------------------
# Load & Display Dashboard
# -----------------------------
if not processed_path.exists():
    st.warning(f"⚠️ No data found for '{user_topic}'. Please click '🚀 Run Analysis' to fetch new data.")
    st.stop()

df = pd.read_csv(processed_path)
st.markdown(f"### 📊 Showing results for: **{user_topic}**")

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
