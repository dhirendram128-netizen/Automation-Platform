import os
from pypdf import PdfReader, PdfWriter

def merge_pdfs(input_paths, output_path):
    writer = PdfWriter()
    for path in input_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path

def split_pdf(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(input_path)
    split_files = []
    
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        
        output_filename = f"page_{i+1}.pdf"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, "wb") as f:
            writer.write(f)
        split_files.append(output_path)
        
    return split_files
