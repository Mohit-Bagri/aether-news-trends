import os
import re
from pathlib import Path
import pandas as pd
import spacy

nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"[^A-Za-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()

def lemmatize_text(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc if not token.is_stop and token.is_alpha])

def main(topic="AI"):
    input_path = PROCESSED_DIR / f"cleaned_news_{topic.lower().replace(' ', '_')}.csv"
    output_path = PROCESSED_DIR / f"news_nlp_ready_{topic.lower().replace(' ', '_')}.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found for topic '{topic}'")

    df = pd.read_csv(input_path)
    df["raw_text"] = (df["title"].fillna("") + " " + df["description"].fillna("")).str.strip()
    df["clean_text"] = df["raw_text"].apply(clean_text)
    df["lemmatized"] = df["clean_text"].apply(lemmatize_text)
    df["num_words"] = df["clean_text"].apply(lambda x: len(x.split()))
    df["num_chars"] = df["clean_text"].apply(len)

    df.to_csv(output_path, index=False)
    print(f"✅ NLP-ready data saved to {output_path}")
    return output_path

if __name__ == "__main__":
    main()
