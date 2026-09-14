from services.document_parser import extract_pdf_text

pdf_path = "sample.pdf"

result = extract_pdf_text(pdf_path)

print("Page count:", result["page_count"])
print("Text preview:")
print(result["full_text"][:1000])