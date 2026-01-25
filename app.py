from flask import Flask, render_template, request, send_file
import os
import zipfile
from tools.invoice_tool import generate_invoices
from tools.csv_cleaner import clean_csv

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html", title="Automation Platform")

@app.route("/invoice", methods=["POST"])
def invoice():
    uploaded_file = request.files["file"]

    csv_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(csv_path)

    invoice_output = os.path.join(OUTPUT_FOLDER, "invoices")
    pdf_files = generate_invoices(csv_path, invoice_output)

    zip_path = os.path.join(OUTPUT_FOLDER, "invoices.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for pdf in pdf_files:
            zipf.write(pdf, os.path.basename(pdf))

    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
    
@app.route("/csv-cleaner", methods=["POST"])
def csv_cleaner():
    uploaded_file = request.files["file"]

    upload_path = os.path.join("uploads", uploaded_file.filename)
    uploaded_file.save(upload_path)

    output_dir = os.path.join("outputs", "csv_cleaner")
    cleaned_file = clean_csv(upload_path, output_dir)

    return send_file(cleaned_file, as_attachment=True)
