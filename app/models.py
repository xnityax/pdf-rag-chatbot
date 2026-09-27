from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(slots=True)
class Chunk:
    id: str
    document_id: str
    page: int
    text: str
    embedding: list[float] | None = None


class AskRequest(BaseModel):
    session_id: str = Field(min_length=16, max_length=128)
    question: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    page: int
    excerpt: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    insufficient_evidence: bool = False
