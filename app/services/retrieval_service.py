import math

from app.models import Chunk


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    denominator = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / denominator if denominator else 0.0


def retrieve(chunks: list[Chunk], query_embedding: list[float], top_k: int) -> list[tuple[Chunk, float]]:
    ranked = [(chunk, cosine_similarity(chunk.embedding or [], query_embedding)) for chunk in chunks]
    return sorted(ranked, key=lambda item: item[1], reverse=True)[:top_k]
