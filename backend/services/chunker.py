def chunk_text(text: str, chunk_size: int = 500):
    """
    Split text into word-based chunks.
    """

    words = text.split()

    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= chunk_size:
            current_chunk.append(word)
            current_length += len(word) + 1
        else:
            chunks.append({
                "chunk_index": len(chunks),
                "content": " ".join(current_chunk)
            })

            current_chunk = [word]
            current_length = len(word)

    if current_chunk:
        chunks.append({
            "chunk_index": len(chunks),
            "content": " ".join(current_chunk)
        })

    return chunks