from app.models import Chunk
from app.services.retrieval_service import retrieve


def test_retrieval_ranks_nearest_vector_first():
    chunks = [Chunk("a", "d", 1, "x", [1, 0]), Chunk("b", "d", 2, "y", [0, 1])]
    assert retrieve(chunks, [0.9, 0.1], 1)[0][0].id == "a"
