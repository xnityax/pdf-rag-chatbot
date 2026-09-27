# PageWise — PDF RAG Chatbot

PageWise is a small FastAPI application that lets a user upload a text-based PDF and ask questions whose answers are grounded in that document. It shows each processing stage, returns page citations and excerpts, and says when the available evidence is insufficient.

## How it works

1. **Upload and extraction** — the server validates the file signature, size and page count, then extracts text page by page with PyMuPDF.
2. **Chunking** — page text is split into overlapping passages while retaining page metadata.
3. **Embedding and indexing** — OpenAI converts each passage into an embedding. The local adapter keeps embeddings in memory for the demo.
4. **Retrieval** — the question is embedded and ranked against passages using cosine similarity.
5. **Answering** — the most relevant passages are sent to the OpenAI Responses API with strict grounding and prompt-injection defenses.

The browser talks to a FastAPI API. Provider and storage responsibilities are separated into services/adapters so they can be replaced independently.

## Local setup

Prerequisites: Python 3.12 and an OpenAI API key.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Set `OPENAI_API_KEY` in `.env`, then run:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. API documentation is at `/api/docs` and health status at `/api/health`.

Run tests (external calls are mocked and need no API key):

```bash
pytest
```

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | — | Required for document indexing and answers |
| `OPENAI_CHAT_MODEL` | `gpt-5-mini` | Model used by the Responses API |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `MAX_UPLOAD_MB` | `10` | Maximum upload size |
| `MAX_PAGES` | `200` | Maximum PDF pages |
| `CHUNK_SIZE` | `1200` | Approximate characters per chunk |
| `CHUNK_OVERLAP` | `200` | Repeated characters between chunks |
| `TOP_K` | `5` | Retrieved passages per question |
| `MIN_SIMILARITY` | `0.15` | Evidence threshold |
| `SESSION_TTL_MINUTES` | `60` | Lifetime of local sessions |
| `ALLOWED_ORIGINS` | empty | Optional comma-separated CORS origins |

Model access varies by account. Change `OPENAI_CHAT_MODEL` if the default is unavailable to you.

## Publish to GitHub

```bash
git init
git add .
git commit -m "Build PageWise PDF RAG chatbot"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/YOUR_REPOSITORY.git
git push -u origin main
```

The `.gitignore` excludes `.env`, caches, environments, uploads and archives. Check staged files before pushing.

## Deploy to Vercel

1. Push the project to a GitHub repository.
2. In Vercel, create a project and import that repository.
3. Leave the project root at the repository root. `vercel.json` routes requests to `api/index.py`.
4. Add `OPENAI_API_KEY` and any model/config overrides under Project Settings → Environment Variables.
5. Deploy, then visit `/api/health` and confirm `configured` is `true`.

### Important serverless limitation

`LocalChunkStore` is intentionally a local-development adapter. Vercel functions have ephemeral, non-shared process state, so an upload handled by one invocation may not be available to the next invocation. For a reliable production deployment, implement `ChunkStore` with a persistent service such as Postgres with pgvector, and place original files in object storage only if retention is required.

For large documents, synchronous extraction and embedding can also exceed a hosting plan's request duration or payload limits. A production architecture should upload directly to object storage, enqueue ingestion, process it in a worker, save vectors in a hosted vector store, and let the UI poll a job-status endpoint. Consult the current Vercel limits for your plan before launch.

## Adding persistent storage

Implement the `ChunkStore` protocol in `app/storage/base.py` with `put`, `get`, and `delete`, then inject that adapter in `create_app`. A production implementation should:

- scope every record by a cryptographically random session or authenticated user ID;
- store vectors in a vector-capable database and retrieve there rather than loading every chunk;
- apply TTL/deletion policies and encryption appropriate to the data;
- avoid logging document text; and
- rate-limit upload and question endpoints at the edge.

## Security and privacy

- File extension, PDF signature, size, page count, encryption and extracted-text volume are validated.
- Original files are not persisted by the included application.
- Session IDs are high-entropy and local records expire.
- Uploaded text is treated as untrusted data; document instructions cannot override the answer policy.
- Provider calls disable response storage with `store=False`. Review your provider agreement and organizational policy before processing sensitive documents.
- This starter does not include authentication or distributed rate limiting; add both before exposing it to untrusted public traffic.

## Troubleshooting

- **“API key is not configured”** — create `.env`, set `OPENAI_API_KEY`, and restart.
- **Model access error** — set `OPENAI_CHAT_MODEL` to a text model available to the account.
- **Scanned PDF / almost no text** — the included build does not perform OCR. Run OCR before upload or add an OCR service.
- **Malformed or encrypted PDF** — repair/decrypt it and upload again.
- **Provider timeout or rate limit** — wait and retry; production systems should add queues and per-user throttles.
- **Session disappears on Vercel** — this is expected with the demo in-memory adapter; configure persistent storage.
- **Import failure in deployment** — ensure the repository root contains `app/`, `api/`, `requirements.txt`, and `vercel.json`.

## Project layout

```text
pdf-rag-chatbot/
├── api/index.py
├── app/
│   ├── main.py, routes.py, config.py, models.py
│   ├── services/       # extraction, chunking, embedding, retrieval, answers
│   └── storage/        # protocol and local adapter
├── static/             # responsive browser UI
├── tests/
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── vercel.json
```

## Accuracy notice

RAG reduces unsupported answers but does not eliminate them. AI output may be incomplete or inaccurate. Verify important details against the cited pages and the original document.
