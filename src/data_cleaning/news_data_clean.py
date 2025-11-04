import pandas as pd
from pathlib import Path

def clean_news_data(input_path, custom_output=None):
    """
    Cleans the raw news data:
      - Loads JSON or CSV
      - Removes duplicates, NaN, and empty text
      - Saves a cleaned CSV file (default or custom_output)
    """

    df = pd.read_json(input_path) if str(input_path).endswith(".json") else pd.read_csv(input_path)

    # Normalize column names
    df.columns = df.columns.str.lower()

    # Standardize text fields
    if "title" not in df.columns:
        df["title"] = ""

    # Try to get text content
    if "description" in df.columns:
        df["text"] = df["description"]
    elif "content" in df.columns:
        df["text"] = df["content"]
    elif "summary" in df.columns:
        df["text"] = df["summary"]
    else:
        df["text"] = ""

    # Drop duplicates and NaNs
    df.drop_duplicates(subset=["title", "text"], inplace=True)
    df.dropna(subset=["title", "text"], inplace=True)

    # Trim whitespace and clean strings
    df["title"] = df["title"].astype(str).str.strip()
    df["text"] = df["text"].astype(str).str.strip()

    # Filter out junk rows (like "nan" or too short)
    df = df[df["title"].str.len() > 5]
    df = df[df["text"].str.len() > 10]

    # Decide output path
    if custom_output:
        output_path = Path(custom_output)
    else:
        output_path = Path(input_path).with_name("cleaned_" + Path(input_path).stem + ".csv")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save cleaned file
    df.to_csv(output_path, index=False)

    print(f"🧹 Cleaned news data saved to: {output_path} ({len(df)} rows)")
    return output_path
