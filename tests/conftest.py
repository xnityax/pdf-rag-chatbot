import os

os.environ.pop("OPENAI_API_KEY", None)

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class FakeEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0] if "revenue" in t.lower() else [0.8, 0.2] for t in texts]


class FakeAnswerer:
    def answer(self, question, matches):
        return f"Revenue grew in the period. [Page {matches[0][0].page}]"


@pytest.fixture
def client():
    with TestClient(create_app(FakeEmbedder(), FakeAnswerer())) as test_client:
        yield test_client
