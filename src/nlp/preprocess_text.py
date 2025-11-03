import os
from pathlib import Path
import pandas as pd
import re
from dotenv import load_dotenv
import spacy


load_dotenv()
NLTK_AVAILABLE = False

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = PROCESSED_DIR / "cleaned_news.csv"
OUTPUT_CSV = PROCESSED_DIR / "news_nlp_ready.csv"

nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+|www\.\S+", "", text)      
    text = re.sub(r"[^A-Za-z0-9\s]", " ", text)       
    text = re.sub(r"\s+", " ", text).strip()         
    return text.lower()

def lemmatize_text(text):
    doc = nlp(text)
    lemmas = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return " ".join(lemmas)

def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)

    # combine title+description for NLP
    df["raw_text"] = (df.get("title", "") .fillna("") + " " + df.get("description", "").fillna("")).str.strip()

    # clean
    df["clean_text"] = df["raw_text"].apply(clean_text)

    # lemmatize (spaCy)
    df["lemmatized"] = df["clean_text"].apply(lemmatize_text)

    # simple features
    df["num_words"] = df["clean_text"].apply(lambda x: len(x.split()))
    df["num_chars"] = df["clean_text"].apply(len)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved NLP-ready data to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()