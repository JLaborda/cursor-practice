# ZenvaResizer

A minimal Flask web app for batch image resizing. Upload up to five images, set target dimensions and JPEG quality, optionally rotate, then preview and download each result in the browser.

Built with **Flask**, **Pillow**, and **Jinja2**. The UI uses a neon-themed layout with a shared header and footer.

## Features

- Upload **up to 5 images** per batch (PNG, JPEG, JPG — validated by file extension)
- Resize to custom **width** and **height** (LANCZOS resampling)
- Adjust **JPEG quality** (1–100; applies to `.jpg` / `.jpeg` output)
- Optional **rotation** — 90°, 180°, or 270° (applied after resize)
- **In-browser preview** of processed images
- **Download** files one at a time
- Processed files stored in a local `uploads/` directory and served via `send_from_directory`

## Requirements

- Python 3.10+
- See [requirements.txt](requirements.txt) for Python dependencies

## Quick start

```bash
# Clone and enter the project
cd cursor-practice

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Usage

1. On the home page, choose one or more image files.
2. Enter target **width**, **height**, and **quality**.
3. Optionally pick a **rotation** (defaults to none).
4. Click **Resize**.
5. On the results page, preview each image and use the download link to save it.

Uploaded and processed files are written to `uploads/` (gitignored). Filenames are sanitized with `secure_filename` and given a short unique suffix.

## Project structure

```
├── app.py                 # Flask routes and image processing
├── requirements.txt       # Runtime and test dependencies
├── pytest.ini             # Pytest config (pythonpath = .)
├── templates/
│   ├── base.html          # Shared neon layout, header, footer
│   ├── index.html         # Upload form
│   └── results.html       # Previews and downloads
├── tests/
│   └── test_app.py        # Unit and integration tests
└── uploads/               # Created at runtime (not in git)
```

## Running tests

```bash
pytest
# or
pytest tests/test_app.py -v
```

The suite covers extension checks, resize/rotate helpers, form validation, and upload/download routes. Tests use a temporary upload directory so they do not touch your local `uploads/` folder.

## API routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Upload form |
| `/` | POST | Process images, show results |
| `/uploads/<filename>` | GET | Preview a processed image |
| `/download/<filename>` | GET | Download a processed image |

## Configuration

Defaults are defined in `app.py`:

| Setting | Value |
|---------|--------|
| Max files per batch | 5 |
| Allowed extensions | `png`, `jpeg`, `jpg` |
| Allowed rotations | `0`, `90`, `180`, `270` |
| Upload folder | `uploads/` |

## Notes

This is a **learning/demo** app, not production-hardened:

- No authentication or user accounts
- No CSRF protection
- No security headers or rate limiting
- File type checking is **extension-only** (not MIME sniffing)

Use only on trusted networks or behind appropriate controls if deployed beyond local development.

## License

See [LICENSE](LICENSE).
