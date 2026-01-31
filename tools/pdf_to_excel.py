import pdfplumber
import pandas as pd
import os
import pytesseract
from PIL import Image
import io
from pypdf import PdfReader, PdfWriter

def pdf_to_excel(pdf_path, output_dir):
    """
    Converts a PDF (text-based or scanned) to an Excel file.
    Uses OCR if text extraction fails or yields too little text.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "output.xlsx")
    
    all_tables = []
    text_rows = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # 1. Try extracting text first
                raw_text = page.extract_text() or ""
                clean_text = raw_text.strip()

                tables = []
                
                # If page appears to be scanned (little to no text), try OCR
                # Threshold: less than 50 characters might suggest a scanned page (mostly empty or image)
                # or just garbage.
                if len(clean_text) < 50:
                    try:
                        # Convert page to image
                        # resolution=300 is standard for OCR
                        img_obj = page.to_image(resolution=300)
                        pil_image = img_obj.original
                        
                        # Use pytesseract to get a searchable PDF overlay or just data
                        # To extract TABLES, it's best to let pdfplumber handle a searchable PDF.
                        # So we convert the image to a searchable PDF using Tesseract.
                        pdf_bytes = pytesseract.image_to_pdf_or_hocr(pil_image, extension='pdf')
                        
                        # Open the OCR'd PDF page with pdfplumber
                        with pdfplumber.open(io.BytesIO(pdf_bytes)) as ocr_pdf:
                            ocr_page = ocr_pdf.pages[0]
                            tables = ocr_page.extract_tables()
                            # verification: did we get better text?
                            ocr_text = ocr_page.extract_text() or ""
                            if not clean_text and ocr_text:
                                raw_text = ocr_text # Use OCR text for fallback
                                
                    except Exception as e:
                        # If OCR fails, we just proceed with what we have (fail safe)
                        print(f"OCR warning on page {i+1}: {e}")
                        pass
                else:
                    # Standard text PDF
                    tables = page.extract_tables()

                # 2. Process Tables
                if tables:
                    for table in tables:
                        # table is usually a list of lists
                        if table and len(table) > 1:
                            # Basic cleanup: remove none values
                            cleaned_table = [[cell if cell is not None else "" for cell in row] for row in table]
                            
                            # Heuristic: headers are usually the first row
                            # Check if we have enough columns
                            if len(cleaned_table[0]) > 0:
                                df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
                                # Attempt numeric conversion
                                for col in df.columns:
                                    df[col] = pd.to_numeric(df[col], errors='ignore')
                                all_tables.append(df)
                else:
                    # If no tables found, use the raw text as fallback rows
                    # Split by newline
                    lines = raw_text.split('\n')
                    for line in lines:
                        if line.strip():
                            text_rows.append([line.strip()])

        # 3. Compile Output
        if not all_tables and not text_rows:
            # Absolute worst case: empty file or total failure
            # Create a dummy dataframe so we return a valid Excel
            df = pd.DataFrame(["No extractable text or tables found."], columns=["Status"])
            df.to_excel(output_path, index=False)
            return output_path

        mode = "w"
        if all_tables:
            # Write tables to sheets
            # For simplicity in this version, we concatenate into one big sheet or 
            # if user wants separate sheets, we could use pd.ExcelWriter.
            # User request: "If tables are detected -> convert each table to a sheet"
            # But "If no clear table -> place extracted text row-wise in Sheet1"
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for idx, df in enumerate(all_tables):
                    sheet_name = f"Table_{idx+1}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # Fallback to text rows
            df = pd.DataFrame(text_rows, columns=["Extracted Text"])
            df.to_excel(output_path, index=False, header=False)

    except Exception as e:
        # GLOBAL FAILSAFE
        # Create a minimal Excel with the error (or just generic text) to ensure return
        print(f"Critical PDF processing error: {e}")
        df = pd.DataFrame(["Error processing file. Content may be corrupted or unreadable."], columns=["Error"])
        df.to_excel(output_path, index=False)
    
    return output_path
