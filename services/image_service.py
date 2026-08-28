"""Safe local storage for uploaded book-cover images."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from config import BASE_DIR
from utils.constants import ALLOWED_COVER_FORMATS, MAX_COVER_UPLOAD_BYTES

COVERS_DIR = BASE_DIR / "uploads" / "book_covers"


class ImageService:
    """Validate cover content and store only safe relative file paths."""

    @staticmethod
    def save_cover(uploaded_file: object) -> str:
        """Validate an uploaded image and return its relative storage path."""
        file_size = int(getattr(uploaded_file, "size", 0))
        if file_size > MAX_COVER_UPLOAD_BYTES:
            raise ValueError("Cover image must be 5 MB or smaller.")
        content = uploaded_file.getvalue()
        try:
            with Image.open(BytesIO(content)) as image:
                image.verify()
            with Image.open(BytesIO(content)) as image:
                image_format = image.format
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError("Upload a valid PNG, JPEG, or WEBP image.") from error
        if image_format not in ALLOWED_COVER_FORMATS:
            raise ValueError("Cover image must be PNG, JPG, JPEG, or WEBP.")
        extension = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}[image_format]
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}.{extension}"
        destination = COVERS_DIR / filename
        destination.write_bytes(content)
        return str(Path("uploads") / "book_covers" / filename)

    @staticmethod
    def resolve_cover(relative_path: str | None) -> Path | None:
        """Resolve a stored relative cover path without allowing traversal."""
        if not relative_path:
            return None
        candidate = (BASE_DIR / relative_path).resolve()
        covers_root = COVERS_DIR.resolve()
        if covers_root not in candidate.parents or not candidate.is_file():
            return None
        return candidate

    @staticmethod
    def delete_cover(relative_path: str | None) -> None:
        """Delete a stored cover only if it resolves inside the covers directory."""
        if path := ImageService.resolve_cover(relative_path):
            path.unlink(missing_ok=True)
