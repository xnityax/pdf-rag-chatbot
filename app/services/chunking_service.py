import re
import uuid

from app.models import Chunk


def chunk_pages(pages: list[tuple[int, str]], document_id: str, size: int, overlap: int) -> list[Chunk]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Chunk size must be positive and overlap smaller than size.")
    chunks: list[Chunk] = []
    for page, text in pages:
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):
                candidates = [m.end() for m in re.finditer(r"[.!?]\s+|\n+", text[start:end])]
                if candidates and candidates[-1] >= size // 2:
                    end = start + candidates[-1]
            passage = text[start:end].strip()
            if passage:
                chunks.append(Chunk(str(uuid.uuid4()), document_id, page, passage))
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)
    return chunks
