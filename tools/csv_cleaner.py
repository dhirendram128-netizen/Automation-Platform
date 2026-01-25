import pandas as pd
import os

def clean_csv(input_csv, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(input_csv)

    # remove completely empty rows
    df = df.dropna(how="all")

    # trim spaces from string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    # remove duplicate rows
    df = df.drop_duplicates()

    # normalize headers
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    output_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(output_path, index=False)

    return output_path
