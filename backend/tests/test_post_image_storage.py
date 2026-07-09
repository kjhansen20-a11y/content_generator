from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.knowledge import FileKind, UploadedFile
from app.services.files import read_file_bytes, save_upload


@pytest.mark.asyncio
async def test_post_image_stores_content_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.files.settings.uploads_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.services.files.BACKEND_DIR", tmp_path)

    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock(side_effect=lambda record: setattr(record, "id", 1))

    upload = MagicMock()
    upload.filename = "photo.jpg"
    upload.content_type = "image/jpeg"
    upload.read = AsyncMock(return_value=b"fake-image-bytes")

    record = await save_upload(session, company_id=1, upload=upload, kind=FileKind.post_image)

    assert record.content_bytes == b"fake-image-bytes"
    assert record.kind == FileKind.post_image


def test_read_file_bytes_falls_back_to_database(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.files.settings.uploads_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.services.files.BACKEND_DIR", tmp_path)

    record = UploadedFile(
        id=1,
        company_id=1,
        original_filename="photo.jpg",
        stored_filename="missing.jpg",
        mime_type="image/jpeg",
        size_bytes=4,
        kind=FileKind.post_image,
        content_bytes=b"db-bytes",
    )

    assert read_file_bytes(record) == b"db-bytes"


def test_read_file_bytes_raises_when_missing_everywhere(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.files.settings.uploads_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.services.files.BACKEND_DIR", tmp_path)

    record = UploadedFile(
        id=1,
        company_id=1,
        original_filename="photo.jpg",
        stored_filename="missing.jpg",
        mime_type="image/jpeg",
        size_bytes=0,
        kind=FileKind.post_image,
        content_bytes=None,
    )

    with pytest.raises(HTTPException) as exc:
        read_file_bytes(record)
    assert exc.value.status_code == 404
