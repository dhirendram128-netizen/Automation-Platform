import pandas as pd
from jinja2 import Environment, FileSystemLoader
import pdfkit
import os

def generate_invoices(csv_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(csv_path)

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("invoice.html")

    generated_files = []

    for _, row in df.iterrows():
        amount = row["Quantity"] * row["Rate"]
        gst_amount = amount * row["GST_Percent"] / 100
        total = amount + gst_amount

        html = template.render(
            invoice_no=row["Invoice_No"],
            invoice_date=row["Invoice_Date"],
            customer_name=row["Customer_Name"],
            customer_address=row["Customer_Address"],
            service_name=row["Service_Name"],
            quantity=row["Quantity"],
            rate=row["Rate"],
            amount=amount,
            gst_percent=row["GST_Percent"],
            gst_amount=gst_amount,
            total=total
        )

        pdf_path = os.path.join(
            output_dir, f"invoice_{row['Invoice_No']}.pdf"
        )

        pdfkit.from_string(html, pdf_path)
        generated_files.append(pdf_path)

    return generated_files
