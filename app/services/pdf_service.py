import io
import re

import fitz
from fastapi import HTTPException, UploadFile


def normalize_text(text: str) -> str:
    text = text.replace("\u00ad", "").replace("\x00", " ")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


async def read_and_validate_pdf(upload: UploadFile, max_bytes: int, max_pages: int) -> tuple[bytes, list[tuple[int, str]]]:
    filename = upload.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(415, "Please upload a PDF file.")
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"The PDF exceeds the {max_bytes // 1_048_576} MB limit.")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(415, "The file does not have a valid PDF signature.")
    try:
        doc = fitz.open(stream=io.BytesIO(data), filetype="pdf")
        if doc.needs_pass:
            raise HTTPException(422, "Encrypted PDFs are not supported. Remove the password and try again.")
        if doc.page_count == 0:
            raise HTTPException(422, "This PDF has no pages.")
        if doc.page_count > max_pages:
            raise HTTPException(413, f"This PDF exceeds the {max_pages}-page limit.")
        pages = [(i + 1, normalize_text(page.get_text("text"))) for i, page in enumerate(doc)]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422, "The PDF is malformed or could not be read.") from exc
    finally:
        if "doc" in locals():
            doc.close()
    if sum(len(text) for _, text in pages) < 40:
        raise HTTPException(422, "Almost no readable text was found. This may be a scanned PDF and requires OCR.")
    return data, pages
