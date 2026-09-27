import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import router
from app.services.answer_service import OpenAIAnswerer
from app.services.embedding_service import OpenAIEmbedder
from app.storage.local import LocalChunkStore


def create_app(embedder=None, answerer=None, store=None) -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(title=settings.app_name, docs_url="/api/docs", redoc_url=None)
    if settings.allowed_origins:
        app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins.split(","), allow_methods=["*"], allow_headers=["*"])
    app.state.embedder = embedder or (OpenAIEmbedder(settings.openai_api_key, settings.openai_embedding_model) if settings.openai_api_key else None)
    app.state.answerer = answerer or (OpenAIAnswerer(settings.openai_api_key, settings.openai_chat_model) if settings.openai_api_key else None)
    app.state.store = store or LocalChunkStore(settings.session_ttl_minutes * 60)
    app.include_router(router)
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(settings.static_dir / "index.html")

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception):
        logging.getLogger(__name__).exception("Unhandled request error")
        return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})

    return app


app = create_app()
