import os
from pathlib import Path
import pandas as pd
import re
import spacy

# Load spaCy model once
nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+|www\.\S+", "", text)       # remove URLs
    text = re.sub(r"[^A-Za-z0-9\s]", " ", text)        # remove symbols
    text = re.sub(r"\s+", " ", text).strip()           # remove extra spaces
    return text.lower()

def lemmatize_text(text):
    doc = nlp(text)
    lemmas = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return " ".join(lemmas)

def main(topic="AI"):
    """
    Preprocess cleaned news data for NLP.
    Each topic saves to: data/processed/news_nlp_ready_<topic>.csv
    """
    topic_tag = topic.lower().replace(" ", "_")

    PROCESSED_DIR = Path("data/processed")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    INPUT_CSV = PROCESSED_DIR / f"cleaned_news_{topic_tag}.csv"
    OUTPUT_CSV = PROCESSED_DIR / f"news_nlp_ready_{topic_tag}.csv"

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    df["raw_text"] = (df.get("title", "").fillna("") + " " + df.get("description", "").fillna("")).str.strip()

    # Clean and lemmatize
    df["clean_text"] = df["raw_text"].apply(clean_text)
    df["lemmatized"] = df["clean_text"].apply(lemmatize_text)

    # Simple text features
    df["num_words"] = df["clean_text"].apply(lambda x: len(x.split()))
    df["num_chars"] = df["clean_text"].apply(len)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Saved NLP-ready data for '{topic}' to {OUTPUT_CSV}")

    return OUTPUT_CSV

if __name__ == "__main__":
    main()
