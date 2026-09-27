import logging
import secrets
import uuid

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from openai import APIError

from app.config import get_settings
from app.models import AskRequest, AskResponse, Source
from app.services.answer_service import FALLBACK
from app.services.chunking_service import chunk_pages
from app.services.pdf_service import read_and_validate_pdf
from app.services.retrieval_service import retrieve

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


def require_services(request: Request):
    if request.app.state.embedder is None or request.app.state.answerer is None:
        raise HTTPException(503, "The OpenAI API key is not configured. Add OPENAI_API_KEY and restart the app.")
    return request.app.state.embedder, request.app.state.answerer


@router.get("/health")
def health(request: Request):
    return {"status": "ok", "configured": request.app.state.embedder is not None}


@router.post("/upload")
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    settings = get_settings()
    embedder, _ = require_services(request)
    _, pages = await read_and_validate_pdf(file, settings.max_upload_mb * 1_048_576, settings.max_pages)
    document_id = str(uuid.uuid4())
    chunks = chunk_pages(pages, document_id, settings.chunk_size, settings.chunk_overlap)
    try:
        vectors = embedder.embed([chunk.text for chunk in chunks])
    except APIError as exc:
        logger.warning("Embedding provider error: %s", type(exc).__name__)
        raise HTTPException(502, "The AI provider could not index the document. Please try again.") from exc
    if len(vectors) != len(chunks):
        raise HTTPException(502, "The AI provider returned an incomplete index.")
    for chunk, vector in zip(chunks, vectors):
        chunk.embedding = vector
    session_id = secrets.token_urlsafe(32)
    safe_name = (file.filename or "document.pdf").replace("<", "").replace(">", "")[:120]
    request.app.state.store.put(session_id, chunks, safe_name)
    return {"session_id": session_id, "filename": safe_name, "pages": len(pages), "chunks": len(chunks)}


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, request: Request):
    settings = get_settings()
    embedder, answerer = require_services(request)
    item = request.app.state.store.get(payload.session_id)
    if item is None:
        raise HTTPException(404, "This document session expired or is unavailable. Please upload the PDF again.")
    chunks, _ = item
    try:
        query_vector = embedder.embed([payload.question])[0]
        matches = retrieve(chunks, query_vector, settings.top_k)
        if not matches or matches[0][1] < settings.min_similarity:
            return AskResponse(answer=FALLBACK, sources=[], insufficient_evidence=True)
        answer = answerer.answer(payload.question, matches)
    except (APIError, IndexError) as exc:
        logger.warning("Answer provider error: %s", type(exc).__name__)
        raise HTTPException(502, "The AI provider could not answer right now. Please try again.") from exc
    sources = [Source(page=c.page, excerpt=c.text[:240].strip(), score=round(score, 3)) for c, score in matches]
    insufficient = answer == FALLBACK
    return AskResponse(answer=answer, sources=[] if insufficient else sources, insufficient_evidence=insufficient)


@router.delete("/session/{session_id}")
def clear_session(session_id: str, request: Request):
    request.app.state.store.delete(session_id)
    return {"cleared": True}
