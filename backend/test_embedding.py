from services.embedding_service import generate_embedding


text = "My name is Yazhini. I know Python and Java."

embedding = generate_embedding(text)

print("Vector Length:", len(embedding))
print("First 10 Values:")
print(embedding[:10])