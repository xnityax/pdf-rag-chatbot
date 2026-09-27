import threading
import time

from app.models import Chunk


class LocalChunkStore:
    """Thread-safe, process-local demo store. Replace for serverless production."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[float, list[Chunk], str]] = {}
        self._lock = threading.RLock()

    def _purge(self) -> None:
        now = time.time()
        for key in [k for k, value in self._items.items() if now - value[0] > self.ttl_seconds]:
            self._items.pop(key, None)

    def put(self, session_id: str, chunks: list[Chunk], filename: str) -> None:
        with self._lock:
            self._purge()
            self._items[session_id] = (time.time(), chunks, filename)

    def get(self, session_id: str) -> tuple[list[Chunk], str] | None:
        with self._lock:
            self._purge()
            item = self._items.get(session_id)
            return (item[1], item[2]) if item else None

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._items.pop(session_id, None)
