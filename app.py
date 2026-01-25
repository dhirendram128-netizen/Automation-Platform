from flask import Flask, render_template, request, send_file, jsonify
import os
import zipfile
import pandas as pd
import razorpay
import uuid

from tools.invoice_tool import generate_invoices
from tools.csv_cleaner import clean_csv
from tools.pdf_to_excel import pdf_to_excel

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------- RAZORPAY CLIENT ----------------

razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET")
    )
)

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

        return jsonify({
    "status": "ready",
    "file_path": zip_path
})

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
        return jsonify({
    "status": "ready",
    "file_path": cleaned_file
})
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
        return jsonify({
    "status": "ready",
    "file_path": excel_file
})
    except Exception:
        return "This PDF does not contain extractable tables.", 400

# ---------------- PAYMENT ORDER ----------------

@app.route("/create-order", methods=["POST"])
def create_order():
    data = request.json

    amount = int(data.get("amount")) * 100
    tool = data.get("tool")
    file_path = data.get("file_path")

    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1,
        "notes": {
            "tool": tool,
            "file_path": file_path
        }
    })

    return jsonify({
        "order_id": order["id"],
        "amount": amount,
        "key": os.getenv("RAZORPAY_KEY_ID")
    })

# ---------------- DOWNLOAD TOKEN ----------------

def generate_download_token(file_path):
    token = str(uuid.uuid4())
    token_path = os.path.join(OUTPUT_FOLDER, f"{token}.txt")

    with open(token_path, "w") as f:
        f.write(file_path)

    return token

# ---------------- RAZORPAY WEBHOOK ----------------

@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    payload = request.data
    signature = request.headers.get("X-Razorpay-Signature")

    secret = os.getenv("RAZORPAY_KEY_SECRET")

    try:
        razorpay_client.utility.verify_webhook_signature(
            payload, signature, secret
        )
    except Exception as e:
        return f"Invalid signature: {str(e)}", 400

    event = request.json

    if event.get("event") == "payment.captured":
        payment = event["payload"]["payment"]["entity"]
        file_path = payment["notes"].get("file_path")

        if not file_path:
            return "File path missing", 400

        token = generate_download_token(file_path)

        return jsonify({"download_token": token})

    return "ok"

# ---------------- SECURE DOWNLOAD ----------------

@app.route("/download/<token>")
def download_file(token):
    token_file = os.path.join(OUTPUT_FOLDER, f"{token}.txt")

    if not os.path.exists(token_file):
        return "Invalid or expired link", 403

    with open(token_file) as f:
        file_path = f.read()

    os.remove(token_file)  # one-time download

    return send_file(file_path, as_attachment=True)


# ---------------- LOCAL ONLY ----------------

if __name__ == "__main__":
    app.run(debug=True)
