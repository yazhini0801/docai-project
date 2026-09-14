import fitz  # PyMuPDF


def extract_pdf_text(file_path: str):
    """
    Extract text, page count, and word coordinates from a PDF file.
    """

    try:
        doc = fitz.open(file_path)

        pages = []

        for page_index in range(len(doc)):
            page = doc[page_index]

            # Keep the existing page text extraction
            text = page.get_text("text")

            # NEW: Extract every word together with its PDF coordinates
            raw_words = page.get_text("words")

            words = []

            for word in raw_words:
                x0, y0, x1, y1, word_text, block_no, line_no, word_no = word

                words.append({
                    "text": word_text,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "block_no": block_no,
                    "line_no": line_no,
                    "word_no": word_no
                })

            pages.append({
                "page_number": page_index + 1,
                "text": text.strip(),
                "width": page.rect.width,
                "height": page.rect.height,
                "words": words
            })

        result = {
            "page_count": len(doc),
            "pages": pages,
            "full_text": "\n\n".join(
                [
                    f"--- Page {p['page_number']} ---\n{p['text']}"
                    for p in pages
                ]
            )
        }

        doc.close()
        return result

    except Exception as e:
        raise Exception(f"PDF text extraction failed: {str(e)}")