from flask import Flask, render_template, request, send_file, jsonify, abort
import os, zipfile, pandas as pd, razorpay, uuid, json, re, traceback, shutil
from tools.invoice_tool import generate_invoices
from tools.csv_cleaner import clean_csv
from tools.pdf_to_excel import pdf_to_excel
from tools.pdf_processor import merge_pdfs, split_pdf
from tools.excel_formula_engine import generate_formula
import hmac, hashlib
from datetime import date, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
JOB_DB = "jobs.json"

FREE_DB = "free_usage.json"
FREE_LIMIT = 2
FREE_SIZE_MB = 4

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------- HELPER: SMART RENAME ----------------

def smart_rename(tool_prefix, ext):
    """
    Generates a consistent, human-readable filename.
    Pattern: {tool}_{date}_{short_uuid}.{ext}
    """
    timestamp = date.today().strftime("%Y-%m-%d")
    unique_id = str(uuid.uuid4())[:6]
    if not ext.startswith("."):
        ext = "." + ext
    return f"{tool_prefix}_{timestamp}_{unique_id}{ext}"

# ---------------- JOB STORE ----------------

def load_jobs():
    if not os.path.exists(JOB_DB):
        return {}
    with open(JOB_DB) as f:
        return json.load(f)

def save_jobs(data):
    with open(JOB_DB, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- FREE USAGE ----------------

def load_free_usage():
    if not os.path.exists(FREE_DB):
        return {}
    with open(FREE_DB) as f:
        return json.load(f)

def save_free_usage(data):
    with open(FREE_DB, "w") as f:
        json.dump(data, f, indent=2)

def get_visitor_id(req):
    fp = req.headers.get("X-Visitor-ID")
    if fp:
        return fp
    return req.remote_addr

def can_use_free(visitor_id, file_size_bytes):
    today = str(date.today())
    size_mb = file_size_bytes / (1024 * 1024)

    if size_mb > FREE_SIZE_MB:
        return False

    data = load_free_usage()

    if visitor_id not in data or data[visitor_id]["date"] != today:
        return True

    if data[visitor_id]["count"] < FREE_LIMIT:
        return True

    return False

def mark_free_used(visitor_id):
    today = str(date.today())
    data = load_free_usage()

    if visitor_id not in data or data[visitor_id]["date"] != today:
        data[visitor_id] = {"date": today, "count": 1}
    else:
        data[visitor_id]["count"] += 1

    save_free_usage(data)

# ---------------- RAZORPAY ----------------

RAZORPAY_KEY_ID = "rzp_live_S8myWrOoEHdaYS"
RAZORPAY_KEY_SECRET = "qQuwpLgp6kJMQngGNDPeApHO"
WEBHOOK_SECRET = "my_name_is_lakhan_by_dhirendra"

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/refund")
def refund():
    return render_template("refund.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ---------------- INVOICE ----------------

@app.route("/invoice", methods=["POST"])
def invoice():
    try:
        uploaded_file = request.files.get("file")
        if not uploaded_file or not uploaded_file.filename.endswith(".csv"):
            return jsonify({"error": "Invalid CSV file. Please upload a valid .csv file."}), 400

        visitor_id = get_visitor_id(request)
        file_size = uploaded_file.content_length or 0
        is_free = can_use_free(visitor_id, file_size)

        csv_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{uploaded_file.filename}")
        uploaded_file.save(csv_path)

        invoice_output = os.path.join(OUTPUT_FOLDER, str(uuid.uuid4()))
        pdf_files = generate_invoices(csv_path, invoice_output)

        output_filename = smart_rename("invoices", ".zip")
        zip_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for pdf in pdf_files:
                zipf.write(pdf, os.path.basename(pdf))

        # Job Tracking
        job_id = str(uuid.uuid4())
        jobs = load_jobs()
        jobs[job_id] = {
            "file": zip_path,
            "filename": output_filename,
            "paid": False,
            "free": is_free
        }
        save_jobs(jobs)

        if is_free:
            mark_free_used(visitor_id)
        
        # Cleanup input
        if os.path.exists(csv_path): os.remove(csv_path)

        return jsonify({"status": "ready", "job_id": job_id, "free": is_free})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to process invoice CSV. Ensure format is correct."}), 500

# ---------------- CSV CLEANER ----------------

@app.route("/csv-cleaner", methods=["POST"])
def csv_cleaner_route():
    try:
        uploaded_file = request.files.get("file")
        if not uploaded_file or not uploaded_file.filename.endswith(".csv"):
            return jsonify({"error": "Invalid file. Please upload a .csv file."}), 400

        visitor_id = get_visitor_id(request)
        file_size = uploaded_file.content_length or 0
        is_free = can_use_free(visitor_id, file_size)

        upload_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{uploaded_file.filename}")
        uploaded_file.save(upload_path)

        # Output with smart name
        output_filename = smart_rename("cleaned_csv", ".csv")
        output_path = os.path.join(OUTPUT_FOLDER, "csv_cleaner")
        os.makedirs(output_path, exist_ok=True)
        
        # The tool returns the full path, so we might need to move/rename it or pass the name
        # Looking at clean_csv signature, it takes input and output dir.
        cleaned_file_path = clean_csv(upload_path, output_path)
        
        # Renaissance the file to our smart logic
        final_path = os.path.join(OUTPUT_FOLDER, output_filename)
        shutil.move(cleaned_file_path, final_path)

        job_id = str(uuid.uuid4())
        jobs = load_jobs()
        jobs[job_id] = {
            "file": final_path,
            "filename": output_filename,
            "paid": False,
            "free": is_free
        }
        save_jobs(jobs)

        if is_free:
            mark_free_used(visitor_id)
            
        if os.path.exists(upload_path): os.remove(upload_path)

        return jsonify({"status": "ready", "job_id": job_id, "free": is_free})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Could not clean CSV. File might be empty or corrupted."}), 500

# ---------------- PDF ----------------

@app.route("/pdf-to-excel", methods=["POST"])
def pdf_to_excel_route():
    try:
        uploaded_file = request.files.get("file")
        if not uploaded_file or not uploaded_file.filename.endswith(".pdf"):
            return jsonify({"error": "Invalid file. Please upload a .pdf file."}), 400

        visitor_id = get_visitor_id(request)
        file_size = uploaded_file.content_length or 0
        is_free = can_use_free(visitor_id, file_size)

        pdf_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{uploaded_file.filename}")
        uploaded_file.save(pdf_path)

        output_subfolder = os.path.join(OUTPUT_FOLDER, "pdf_to_excel")
        os.makedirs(output_subfolder, exist_ok=True)
        
        # Tool returns path to "output.xlsx" usually
        excel_file = pdf_to_excel(pdf_path, output_subfolder)
        
        # Rename
        output_filename = smart_rename("ocr_excel", ".xlsx")
        final_path = os.path.join(OUTPUT_FOLDER, output_filename)
        shutil.move(excel_file, final_path)

        job_id = str(uuid.uuid4())
        jobs = load_jobs()
        jobs[job_id] = {
            "file": final_path,
            "filename": output_filename,
            "paid": False,
            "free": is_free
        }
        save_jobs(jobs)

        if is_free:
            mark_free_used(visitor_id)
            
        if os.path.exists(pdf_path): os.remove(pdf_path)

        return jsonify({"status": "ready", "job_id": job_id, "free": is_free})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "PDF conversion failed. File might be password protected or corrupted."}), 500

# ---------------- DOWNLOAD ----------------

@app.route("/download/<job_id>")
def download_file(job_id):
    jobs = load_jobs()
    if job_id not in jobs:
        abort(404)

    job = jobs[job_id]

    if job.get("free") or job.get("paid"):
        filename = job.get("filename", os.path.basename(job["file"]))
        return send_file(job["file"], as_attachment=True, download_name=filename)

    return "Payment required", 403

# ---------------- PDF MERGE / SPLIT ----------------

@app.route("/pdf-merge", methods=["POST"])
def pdf_merge_route():
    try:
        uploaded_files = request.files.getlist("files")
        if not uploaded_files or len(uploaded_files) < 2:
            return jsonify({"error": "Need at least 2 PDFs to merge."}), 400

        visitor_id = get_visitor_id(request)
        total_size = sum([f.content_length or 0 for f in uploaded_files])
        is_free = can_use_free(visitor_id, total_size)

        input_paths = []
        for f in uploaded_files:
            path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + "_" + f.filename)
            f.save(path)
            input_paths.append(path)

        output_filename = smart_rename("pdf_merge", ".pdf")
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        merge_pdfs(input_paths, output_path)

        # Cleanup inputs
        for p in input_paths:
            if os.path.exists(p): os.remove(p)

        job_id = str(uuid.uuid4())
        jobs = load_jobs()
        jobs[job_id] = {
            "file": output_path,
            "filename": output_filename,
            "paid": False,
            "free": is_free
        }
        save_jobs(jobs)

        if is_free:
            mark_free_used(visitor_id)

        return jsonify({"status": "ready", "job_id": job_id, "free": is_free})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Merge failed. Some files might be corrupted."}), 500

@app.route("/pdf-split", methods=["POST"])
def pdf_split_route():
    try:
        uploaded_file = request.files.get("file")
        if not uploaded_file or not uploaded_file.filename.endswith(".pdf"):
            return jsonify({"error": "Invalid PDF file."}), 400

        visitor_id = get_visitor_id(request)
        file_size = uploaded_file.content_length or 0
        is_free = can_use_free(visitor_id, file_size)

        pdf_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + "_" + uploaded_file.filename)
        uploaded_file.save(pdf_path)

        split_dir = os.path.join(OUTPUT_FOLDER, str(uuid.uuid4()) + "_split")
        split_files = split_pdf(pdf_path, split_dir)

        output_filename = smart_rename("pdf_split", ".zip")
        zip_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for f in split_files:
                zipf.write(f, os.path.basename(f))

        # Cleanup inputs and split folder
        if os.path.exists(pdf_path): os.remove(pdf_path)
        for f in split_files:
            if os.path.exists(f): os.remove(f)
        if os.path.exists(split_dir): os.rmdir(split_dir)

        job_id = str(uuid.uuid4())
        jobs = load_jobs()
        jobs[job_id] = {
            "file": zip_path,
            "filename": output_filename,
            "paid": False,
            "free": is_free
        }
        save_jobs(jobs)

        if is_free:
            mark_free_used(visitor_id)

        return jsonify({"status": "ready", "job_id": job_id, "free": is_free})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Split failed. File might be corrupted."}), 500

# ---------------- EXCEL FORMULA ----------------

@app.route("/excel-formula", methods=["POST"])
def excel_formula_route():
    """
    Production-grade Excel formula generator.
    NEVER fails. NEVER asks questions. ALWAYS returns a valid formula.
    """
    try:
        data = request.json
        prompt = data.get("prompt", "")
        
        # Generate formula using bulletproof engine
        formula = generate_formula(prompt)
        
        # Return ONLY the formula (no explanation as per requirements)
        return jsonify({"formula": formula})
    except Exception as e:
        # Failsafe
        return jsonify({"formula": '="ERROR: Could not generate formula"'})

# ---------------- STATUS ----------------

@app.route("/check-status/<job_id>")
def check_status(job_id):
    jobs = load_jobs()
    if job_id not in jobs:
        return jsonify({"status": "not_found"})

    if jobs[job_id].get("free") or jobs[job_id].get("paid"):
        return jsonify({"status": "paid"})

    return jsonify({"status": "pending"})

# ---------------- WEBHOOK ----------------

@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    payload = request.data
    received_signature = request.headers.get("X-Razorpay-Signature")

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if received_signature != expected_signature:
        return "Invalid signature", 400

    data = json.loads(payload)

    if data["event"] == "payment.captured":
        payment = data["payload"]["payment"]["entity"]
        job_id = payment["notes"].get("job_id")

        jobs = load_jobs()
        if job_id in jobs:
            jobs[job_id]["paid"] = True
            save_jobs(jobs)

    return "OK", 200

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
