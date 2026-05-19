import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = Path("uploads")
ALLOWED_EXTENSIONS = {"png", "jpeg", "jpg"}
MAX_FILES = 5


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def resize_image(src: Path, dest: Path, width: int, height: int, quality: int) -> None:
    with Image.open(src) as img:
        if img.mode in ("RGBA", "P") and dest.suffix.lower() in (".jpg", ".jpeg"):
            img = img.convert("RGB")
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        if dest.suffix.lower() in (".jpg", ".jpeg"):
            resized.save(dest, quality=quality, optimize=True)
        else:
            resized.save(dest, optimize=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", max_files=MAX_FILES)

    files = request.files.getlist("images")
    files = [f for f in files if f.filename]

    if not files:
        return render_template(
            "index.html",
            max_files=MAX_FILES,
            error="Select at least one image.",
        ), 400

    if len(files) > MAX_FILES:
        return render_template(
            "index.html",
            max_files=MAX_FILES,
            error=f"You can upload at most {MAX_FILES} images.",
        ), 400

    try:
        width = int(request.form.get("width", ""))
        height = int(request.form.get("height", ""))
        quality = int(request.form.get("quality", ""))
    except (TypeError, ValueError):
        return render_template(
            "index.html",
            max_files=MAX_FILES,
            error="Width, height, and quality must be whole numbers.",
        ), 400

    if width < 1 or height < 1 or quality < 1 or quality > 100:
        return render_template(
            "index.html",
            max_files=MAX_FILES,
            error="Width and height must be at least 1; quality must be 1–100.",
        ), 400

    UPLOAD_FOLDER.mkdir(exist_ok=True)
    results = []

    for upload in files:
        if not allowed_file(upload.filename):
            return render_template(
                "index.html",
                max_files=MAX_FILES,
                error="Only PNG, JPEG, and JPG files are allowed.",
            ), 400

        safe_name = secure_filename(upload.filename)
        stem = Path(safe_name).stem or "image"
        ext = Path(safe_name).suffix.lower()
        out_name = f"{stem}_{uuid.uuid4().hex[:8]}{ext}"
        out_path = UPLOAD_FOLDER / out_name

        upload.save(out_path)
        try:
            resize_image(out_path, out_path, width, height, quality)
        except Exception:
            out_path.unlink(missing_ok=True)
            return render_template(
                "index.html",
                max_files=MAX_FILES,
                error=f"Could not process {upload.filename}.",
            ), 400

        results.append({"name": out_name, "original": upload.filename})

    return render_template(
        "results.html",
        results=results,
        width=width,
        height=height,
        quality=quality,
    )


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)


@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    app.run(debug=True)
