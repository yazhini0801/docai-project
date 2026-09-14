from services.chunker import chunk_text

sample_text = """
This is a sample document.
""" * 100

chunks = chunk_text(sample_text)

print(f"Total Chunks: {len(chunks)}")

for chunk in chunks[:3]:
    print(chunk)