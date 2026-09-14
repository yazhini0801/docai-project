import fitz  # PyMuPDF


def extract_pdf_text(file_path: str):
    """
    Extract text and page count from a PDF file.
    """

    try:
        doc = fitz.open(file_path)

        pages = []

        for page_index in range(len(doc)):
            page = doc[page_index]
            text = page.get_text("text")

            pages.append({
                "page_number": page_index + 1,
                "text": text.strip()
            })

        result = {
            "page_count": len(doc),
            "pages": pages,
            "full_text": "\n\n".join(
                [f"--- Page {p['page_number']} ---\n{p['text']}" for p in pages]
            )
        }

        doc.close()
        return result

    except Exception as e:
        raise Exception(f"PDF text extraction failed: {str(e)}")