from flask import Flask, render_template, request, send_file, jsonify, abort
import os, zipfile, pandas as pd, razorpay, uuid, json

from tools.invoice_tool import generate_invoices
from tools.csv_cleaner import clean_csv
from tools.pdf_to_excel import pdf_to_excel

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
JOB_DB = "jobs.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------- JOB STORE ----------------

def load_jobs():
    if not os.path.exists(JOB_DB):
        return {}
    with open(JOB_DB) as f:
        return json.load(f)

def save_jobs(data):
    with open(JOB_DB, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- RAZORPAY ----------------

razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")

# ---------------- INVOICE ----------------

@app.route("/invoice", methods=["POST"])
def invoice():
    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename.endswith(".csv"):
        return "Invalid CSV", 400

    csv_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(csv_path)

    invoice_output = os.path.join(OUTPUT_FOLDER, "invoices")
    pdf_files = generate_invoices(csv_path, invoice_output)

    zip_path = os.path.join(OUTPUT_FOLDER, "invoices.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for pdf in pdf_files:
            zipf.write(pdf, os.path.basename(pdf))

    job_id = str(uuid.uuid4())
    jobs = load_jobs()
    jobs[job_id] = {"file": zip_path, "paid": False}
    save_jobs(jobs)

    return jsonify({"status": "ready", "job_id": job_id})

# ---------------- CSV CLEANER ----------------

@app.route("/csv-cleaner", methods=["POST"])
def csv_cleaner_route():
    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename.endswith(".csv"):
        return "Invalid CSV", 400

    upload_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(upload_path)

    cleaned_file = clean_csv(upload_path, os.path.join(OUTPUT_FOLDER, "csv_cleaner"))

    job_id = str(uuid.uuid4())
    jobs = load_jobs()
    jobs[job_id] = {"file": cleaned_file, "paid": False}
    save_jobs(jobs)

    return jsonify({"status": "ready", "job_id": job_id})

# ---------------- PDF ----------------

@app.route("/pdf-to-excel", methods=["POST"])
def pdf_to_excel_route():
    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename.endswith(".pdf"):
        return "Invalid PDF", 400

    pdf_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(pdf_path)

    excel_file = pdf_to_excel(pdf_path, os.path.join(OUTPUT_FOLDER, "pdf_to_excel"))

    job_id = str(uuid.uuid4())
    jobs = load_jobs()
    jobs[job_id] = {"file": excel_file, "paid": False}
    save_jobs(jobs)

    return jsonify({"status": "ready", "job_id": job_id})

# ---------------- CREATE ORDER ----------------

@app.route("/create-order", methods=["POST"])
def create_order():
    data = request.json
    job_id = data.get("job_id")

    jobs = load_jobs()
    if job_id not in jobs:
        abort(400)

    order = razorpay_client.order.create({
        "amount": 49 * 100,
        "currency": "INR",
        "payment_capture": 1,
        "notes": {"job_id": job_id}
    })

    return jsonify({
        "order_id": order["id"],
        "amount": 49 * 100,
        "key": os.getenv("RAZORPAY_KEY_ID")
    })

# ---------------- WEBHOOK ----------------

@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    payload = request.data
    sig = request.headers.get("X-Razorpay-Signature")

    razorpay_client.utility.verify_webhook_signature(
        payload, sig, os.getenv("RAZORPAY_KEY_SECRET")
    )

    event = request.json
    if event.get("event") == "payment.captured":
        job_id = event["payload"]["payment"]["entity"]["notes"].get("job_id")
        jobs = load_jobs()
        if job_id in jobs:
            jobs[job_id]["paid"] = True
            save_jobs(jobs)

    return "ok"

# ---------------- DOWNLOAD ----------------

@app.route("/download/<job_id>")
def download_file(job_id):
    jobs = load_jobs()
    if job_id not in jobs or not jobs[job_id]["paid"]:
        return "Payment required", 403

    return send_file(jobs[job_id]["file"], as_attachment=True)
@app.route("/check-status/<job_id>")
def check_status(job_id):
    jobs = load_jobs()

    if job_id not in jobs:
        return jsonify({"status": "not_found"})

    if jobs[job_id]["paid"]:
        return jsonify({"status": "paid"})
    else:
        return jsonify({"status": "pending"})

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
