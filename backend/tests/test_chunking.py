from app.services.chunking import split_text


def test_empty_text_returns_no_chunks():
    assert split_text("") == []


def test_short_text_is_single_chunk():
    assert split_text("שלום עולם") == ["שלום עולם"]


def test_chunks_do_not_exceed_max_size():
    chunks = split_text("א" * 2000, chunk_size=800, overlap=100)
    assert all(len(c) <= 800 for c in chunks)


def test_consecutive_chunks_overlap():
    text = "".join(str(i % 10) for i in range(1000))
    chunks = split_text(text, chunk_size=300, overlap=50)
    assert chunks[0][-50:] == chunks[1][:50]