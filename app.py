
from flask import Flask, request, jsonify, render_template
import pytesseract
from pdf2image import convert_from_path
import tempfile
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

logistic_keywords = ["box cost", "mailers", "pick", "shipping", "returns"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_invoice():
    file = request.files['file']
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(file.filename)
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, filename)
        file.save(filepath)
        images = convert_from_path(filepath)

        total_invoice = 0
        total_units = 0
        extracted_lines = []

        for img in images:
            text = pytesseract.image_to_string(img)
            lines = text.split('\n')
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 4:
                    try:
                        qty = int(parts[-3])
                        unit = float(parts[-2].replace(',', ''))
                        total = float(parts[-1].replace(',', ''))
                        description = ' '.join(parts[:-3])
                        desc_lower = description.lower()
                        is_logistic = any(k in desc_lower for k in logistic_keywords)
                        is_return = qty < 0 or total < 0 or 'return' in desc_lower
                        extracted_lines.append([description, qty, unit, total])
                        total_invoice += total
                        if not is_logistic and not is_return:
                            total_units += qty
                    except:
                        continue

    avg = total_invoice / total_units if total_units else 0
    return jsonify({
        "total_invoice": round(total_invoice, 2),
        "total_units": total_units,
        "avg_cost": round(avg, 2),
        "lines": extracted_lines
    })
