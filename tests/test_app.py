import io
from pathlib import Path

import pytest
from PIL import Image

import app as zenva


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(zenva, "UPLOAD_FOLDER", tmp_path)
    zenva.app.config["TESTING"] = True
    with zenva.app.test_client() as client:
        yield client


def _image_file(name: str, size=(120, 90), color="blue", fmt=None):
    suffix = Path(name).suffix.lower()
    if fmt is None:
        fmt = "JPEG" if suffix in (".jpg", ".jpeg") else "PNG"
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    buf.seek(0)
    return (io.BytesIO(buf.read()), name)


class TestAllowedFile:
    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("photo.png", True),
            ("photo.JPG", True),
            ("photo.jpeg", True),
            ("photo.gif", False),
            ("noextension", False),
            ("", False),
        ],
    )
    def test_extension_check(self, filename, expected):
        assert zenva.allowed_file(filename) is expected


class TestParseRotate:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, 0),
            ("", 0),
            ("0", 0),
            ("90", 90),
            ("180", 180),
            ("270", 270),
            ("45", None),
            ("abc", None),
        ],
    )
    def test_parse_rotate(self, value, expected):
        assert zenva.parse_rotate(value) == expected


class TestResizeImage:
    def test_resizes_to_target_dimensions(self, tmp_path):
        src = tmp_path / "in.png"
        dest = tmp_path / "out.png"
        Image.new("RGB", (200, 100), "red").save(src)
        zenva.resize_image(src, dest, 50, 30, 85)
        with Image.open(dest) as img:
            assert img.size == (50, 30)

    def test_rotate_90_swaps_dimensions_after_resize(self, tmp_path):
        src = tmp_path / "in.png"
        dest = tmp_path / "out.png"
        Image.new("RGB", (200, 100), "red").save(src)
        zenva.resize_image(src, dest, 40, 25, 85, rotate=90)
        with Image.open(dest) as img:
            assert img.size == (25, 40)

    def test_rotate_180_keeps_dimensions(self, tmp_path):
        src = tmp_path / "in.png"
        dest = tmp_path / "out.png"
        Image.new("RGB", (200, 100), "red").save(src)
        zenva.resize_image(src, dest, 40, 25, 85, rotate=180)
        with Image.open(dest) as img:
            assert img.size == (40, 25)


class TestIndex:
    def test_get_returns_form(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"ZenvaResizer" in response.data

    def test_post_without_files_returns_400(self, client):
        response = client.post(
            "/",
            data={"width": "100", "height": "100", "quality": "80"},
        )
        assert response.status_code == 400
        assert b"Select at least one image" in response.data

    def test_post_too_many_files_returns_400(self, client):
        response = client.post(
            "/",
            data={
                "images": [
                    _image_file(f"img{i}.png")
                    for i in range(zenva.MAX_FILES + 1)
                ],
                "width": "10",
                "height": "10",
                "quality": "80",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert b"at most" in response.data

    def test_post_invalid_extension_returns_400(self, client):
        response = client.post(
            "/",
            data={
                "images": _image_file("doc.gif"),
                "width": "10",
                "height": "10",
                "quality": "80",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert b"PNG, JPEG, and JPG" in response.data

    def test_post_invalid_rotate_returns_400(self, client):
        response = client.post(
            "/",
            data={
                "images": _image_file("photo.png"),
                "width": "10",
                "height": "10",
                "quality": "80",
                "rotate": "45",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert b"Rotation must be" in response.data

    def test_post_invalid_quality_returns_400(self, client):
        response = client.post(
            "/",
            data={
                "images": _image_file("photo.png"),
                "width": "10",
                "height": "10",
                "quality": "0",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert b"quality must be 1" in response.data

    def test_post_valid_png_shows_results_and_resizes(self, client, tmp_path):
        response = client.post(
            "/",
            data={
                "images": _image_file("sample.png"),
                "width": "40",
                "height": "25",
                "quality": "90",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert b"Resized" in response.data
        saved = list(tmp_path.glob("*.png"))
        assert len(saved) == 1
        with Image.open(saved[0]) as img:
            assert img.size == (40, 25)

    def test_post_with_rotate_90_shows_rotation_in_results(self, client, tmp_path):
        response = client.post(
            "/",
            data={
                "images": _image_file("rotated.png"),
                "width": "40",
                "height": "25",
                "quality": "90",
                "rotate": "90",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert b"rotated 90" in response.data
        with Image.open(list(tmp_path.glob("*.png"))[0]) as img:
            assert img.size == (25, 40)

    def test_serve_and_download_processed_file(self, client, tmp_path):
        post = client.post(
            "/",
            data={
                "images": _image_file("dl.png"),
                "width": "20",
                "height": "20",
                "quality": "80",
            },
            content_type="multipart/form-data",
        )
        assert post.status_code == 200
        name = list(tmp_path.glob("*.png"))[0].name

        preview = client.get(f"/uploads/{name}")
        assert preview.status_code == 200
        assert preview.mimetype.startswith("image/")

        download = client.get(f"/download/{name}")
        assert download.status_code == 200
        assert download.headers.get("Content-Disposition", "").startswith(
            "attachment"
        )
