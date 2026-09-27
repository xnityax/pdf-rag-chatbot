from app.services.chunking_service import chunk_pages


def test_chunks_preserve_page_and_overlap():
    chunks = chunk_pages([(7, "A" * 150)], "doc", 100, 20)
    assert len(chunks) == 2
    assert all(c.page == 7 and c.document_id == "doc" for c in chunks)
    assert chunks[0].text[-20:] == chunks[1].text[:20]


def test_invalid_chunk_settings():
    import pytest
    with pytest.raises(ValueError):
        chunk_pages([(1, "text")], "doc", 20, 20)
