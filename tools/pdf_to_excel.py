import pdfplumber
import pandas as pd
import os

def pdf_to_excel(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    all_tables.append(df)

    if not all_tables:
        raise ValueError("No tables found in PDF")

    final_df = pd.concat(all_tables, ignore_index=True)

    output_path = os.path.join(output_dir, "output.xlsx")
    final_df.to_excel(output_path, index=False)

    return output_path
