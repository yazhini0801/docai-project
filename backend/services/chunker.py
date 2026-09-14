def chunk_text(text: str, chunk_size: int = 500):
    """
    Split text into word-based chunks.
    Existing function kept for compatibility.
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


def chunk_words_with_coordinates(words, chunk_size: int = 500):
    """
    Create chunks while preserving PDF word coordinates.
    """

    chunks = []
    current_words = []
    current_length = 0

    def save_chunk():
        if not current_words:
            return

        chunks.append({
            "chunk_index": len(chunks),

            "content": " ".join(
                word["text"] for word in current_words
            ),

            "bounding_boxes": [
                {
                    "text": word["text"],
                    "x0": word["x0"],
                    "y0": word["y0"],
                    "x1": word["x1"],
                    "y1": word["y1"]
                }
                for word in current_words
            ]
        })

    for word in words:
        word_text = str(word.get("text", "")).strip()

        if not word_text:
            continue

        added_length = len(word_text) + 1

        if (
            current_words
            and current_length + added_length > chunk_size
        ):
            save_chunk()

            current_words = []
            current_length = 0

        current_words.append(word)
        current_length += added_length

    save_chunk()

    return chunks