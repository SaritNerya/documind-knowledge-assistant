def split_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """מחלקת טקסט לקטעים באורך chunk_size תווים, עם חפיפה של overlap תווים."""
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks