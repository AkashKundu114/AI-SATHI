def _chunk_text(text: str, chunk_chars: int = 800, overlap: int = 100) -> list[str]:
    
    if not text or text.strip() == "":
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_chars, text_len)
        chunk = text[start:end]
        if chunk:
            chunks.append(chunk)
        if end == text_len:
            break
        start = max(0, end - overlap)
    return chunks
