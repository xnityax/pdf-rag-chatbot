import io
import fitz
import pytest
from fastapi import HTTPException, UploadFile

from app.services.pdf_service import read_and_validate_pdf


def make_pdf(text="Readable document text with enough content to pass validation."):
    doc=fitz.open();page=doc.new_page();page.insert_text((72,72),text);data=doc.tobytes();doc.close();return data


@pytest.mark.asyncio
async def test_valid_pdf_extracts_text():
    _, pages=await read_and_validate_pdf(UploadFile(filename="safe.pdf",file=io.BytesIO(make_pdf())),1_000_000,10)
    assert pages[0][0] == 1 and "Readable" in pages[0][1]


@pytest.mark.asyncio
async def test_rejects_non_pdf_and_empty_text():
    with pytest.raises(HTTPException) as exc:
        await read_and_validate_pdf(UploadFile(filename="x.txt",file=io.BytesIO(b"hello")),100,10)
    assert exc.value.status_code == 415
    with pytest.raises(HTTPException) as exc:
        await read_and_validate_pdf(UploadFile(filename="scan.pdf",file=io.BytesIO(make_pdf("x"))),1_000_000,10)
    assert "OCR" in exc.value.detail
