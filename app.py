from flask import Flask, render_template, request, send_file
import os
import zipfile
import pandas as pd

from tools.invoice_tool import generate_invoices
from tools.csv_cleaner import clean_csv
from tools.pdf_to_excel import pdf_to_excel

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html", title="Automation Platform")

# ---------------- INVOICE TOOL ----------------

@app.route("/invoice", methods=["POST"])
def invoice():
    uploaded_file = request.files.get("file")

    if not uploaded_file:
        return "No file uploaded", 400

    filename = uploaded_file.filename.lower()

    if not filename.endswith(".csv"):
        return "Wrong file type. Please upload a CSV file only.", 400

    csv_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(csv_path)

    # CSV content validation (CRITICAL FIX)
    try:
        pd.read_csv(csv_path)
    except Exception:
        return "Invalid CSV file. Please upload a valid CSV.", 400

    try:
        invoice_output = os.path.join(OUTPUT_FOLDER, "invoices")
        pdf_files = generate_invoices(csv_path, invoice_output)

        zip_path = os.path.join(OUTPUT_FOLDER, "invoices.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for pdf in pdf_files:
                zipf.write(pdf, os.path.basename(pdf))

        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        return f"Invoice generation failed: {str(e)}", 500

# ---------------- CSV CLEANER ----------------

@app.route("/csv-cleaner", methods=["POST"])
def csv_cleaner_route():
    uploaded_file = request.files.get("file")

    if not uploaded_file:
        return "No file uploaded", 400

    filename = uploaded_file.filename.lower()

    if not filename.endswith(".csv"):
        return "Wrong file type. Please upload a CSV file only.", 400

    upload_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(upload_path)

    try:
        cleaned_file = clean_csv(upload_path, os.path.join(OUTPUT_FOLDER, "csv_cleaner"))
        return send_file(cleaned_file, as_attachment=True)
    except Exception as e:
        return f"CSV cleaning failed: {str(e)}", 400

# ---------------- PDF TO EXCEL ----------------

@app.route("/pdf-to-excel", methods=["POST"])
def pdf_to_excel_route():
    uploaded_file = request.files.get("file")

    if not uploaded_file:
        return "No file uploaded", 400

    filename = uploaded_file.filename.lower()

    if not filename.endswith(".pdf"):
        return "Wrong file type. Please upload a PDF file only.", 400

    pdf_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(pdf_path)

    try:
        excel_file = pdf_to_excel(pdf_path, os.path.join(OUTPUT_FOLDER, "pdf_to_excel"))
        return send_file(excel_file, as_attachment=True)
    except Exception:
        return "This PDF does not contain extractable tables.", 400

# ---------------- RUN LOCAL ONLY ----------------

if __name__ == "__main__":
    app.run(debug=True)
