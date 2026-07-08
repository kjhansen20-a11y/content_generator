from io import BytesIO

MAX_EXTRACT_CHARS = 50_000

ALLOWED_PLAN_EXTENSIONS = {"txt", "md", "csv", "pdf"}
ALLOWED_PLAN_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/pdf",
}


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def extract_text_from_bytes(
    filename: str,
    data: bytes,
    mime_type: str | None = None,
) -> str:
    ext = _extension(filename)
    if mime_type == "application/pdf" or ext == "pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        extracted = "\n".join(parts).strip()
        if not extracted:
            raise ValueError(
                "No text could be extracted from this PDF. "
                "Scanned/image-only PDFs are not supported yet."
            )
        return extracted[:MAX_EXTRACT_CHARS]

    if ext in {"txt", "md", "csv"} or mime_type in {"text/plain", "text/markdown", "text/csv"}:
        text = data.decode("utf-8", errors="replace").strip()
        if not text:
            raise ValueError("The uploaded file is empty.")
        return text[:MAX_EXTRACT_CHARS]

    raise ValueError(
        f"Unsupported file type. Use one of: {', '.join(sorted(ALLOWED_PLAN_EXTENSIONS))}"
    )
