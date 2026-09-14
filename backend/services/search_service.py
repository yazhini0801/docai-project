import os
import math
import json
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

from services.embedding_service import generate_embedding


load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MIN_SIMILARITY_SCORE = 0.55


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (norm1 * norm2)


def get_confidence(score: float) -> str:
    if score >= 0.75:
        return "HIGH"
    elif score >= 0.55:
        return "MEDIUM"
    else:
        return "LOW"


def semantic_search(
    supabase,
    user_id: str,
    question: str,
    document_ids: List[str] | None = None,
    top_k: int = 15
) -> List[Dict[str, Any]]:

    question_embedding = generate_embedding(question)

    docs_query = (
        supabase.table("documents")
        .select("id,file_name")
        .eq("user_id", user_id)
    )

    if document_ids:
        docs_query = docs_query.in_("id", document_ids)

    docs_response = docs_query.execute()
    documents = docs_response.data or []

    if not documents:
        return []

    allowed_doc_ids = [doc["id"] for doc in documents]
    doc_name_map = {
        doc["id"]: doc["file_name"]
        for doc in documents
    }

    chunks_response = (
        supabase.table("document_chunks")
        .select("*")
        .in_("document_id", allowed_doc_ids)
        .execute()
    )

    chunks = chunks_response.data or []

    if not chunks:
        return []

    chunk_ids = [
        chunk["id"]
        for chunk in chunks
    ]

    chunk_map = {
        chunk["id"]: chunk
        for chunk in chunks
    }

    embeddings_response = (
        supabase.table("chunk_embeddings")
        .select("*")
        .in_("chunk_id", chunk_ids)
        .execute()
    )

    embeddings = embeddings_response.data or []

    scored_chunks = []

    for item in embeddings:
        chunk_embedding = item.get("embedding")
        chunk_id = item.get("chunk_id")

        if not chunk_embedding or not chunk_id:
            continue

        chunk = chunk_map.get(chunk_id)

        if not chunk:
            continue

        score = cosine_similarity(
            question_embedding,
            chunk_embedding
        )

        scored_chunks.append({
            "chunk_id": chunk_id,
            "document_id": chunk["document_id"],
            "score": score
        })

    scored_chunks.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    top_results = scored_chunks[:top_k]

    final_results = []

    for result in top_results:
        chunk = chunk_map.get(
            result["chunk_id"]
        )

        if not chunk:
            continue

        chunk_text = chunk.get(
            "content",
            ""
        )

        final_results.append({
            "chunk_id": result["chunk_id"],
            "document_id":
                result["document_id"],
            "file_name":
                doc_name_map.get(
                    result["document_id"],
                    "Unknown file"
                ),
            "page_number":
                chunk.get("page_number"),
            "chunk_index":
                chunk.get("chunk_index"),
            "text":
                chunk_text,

            # NEW: carry PDF coordinates
            "bounding_boxes":
                chunk.get("bounding_boxes"),

            "score":
                result["score"],
            "confidence":
                get_confidence(
                    result["score"]
                )
        })

    return final_results


def rerank_chunks(
    question: str,
    chunks: List[Dict[str, Any]],
    top_n: int = 5
) -> List[Dict[str, Any]]:

    if not chunks:
        return []

    if len(chunks) <= top_n:
        return chunks

    context = ""

    for i, chunk in enumerate(
        chunks,
        start=1
    ):
        text = chunk["text"][:900]

        context += f"""
Chunk {i}
File: {chunk["file_name"]}
Page: {chunk.get("page_number")}
Chunk Index: {chunk.get("chunk_index")}
Text:
{text}
"""

    prompt = f"""
You are a reranking system for a secure document assistant.

Task:
Given the user question and retrieved chunks, select the most relevant chunks that directly answer the question.

Rules:
1. Return ONLY valid JSON.
2. Do not explain.
3. Choose at most {top_n} chunks.
4. Use chunk numbers from the given list.
5. Prefer chunks that directly answer the question.
6. Remove weakly related or irrelevant chunks.

User Question:
{question}

Retrieved Chunks:
{context}

Return JSON in this format:
{{
  "selected_chunks": [1, 2, 3]
}}
"""

    try:
        model = genai.GenerativeModel(
            "gemini-3.1-flash-lite"
        )

        response = model.generate_content(
            prompt
        )

        raw_text = response.text.strip()

        raw_text = (
            raw_text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        parsed = json.loads(
            raw_text
        )

        selected_numbers = parsed.get(
            "selected_chunks",
            []
        )

        reranked = []

        for number in selected_numbers:
            if isinstance(number, int):
                index = number - 1

                if 0 <= index < len(chunks):
                    reranked.append(
                        chunks[index]
                    )

        if reranked:
            return reranked[:top_n]

        return chunks[:top_n]

    except Exception:
        return chunks[:top_n]


def generate_answer_from_context(
    question: str,
    chunks: List[Dict[str, Any]]
) -> str:

    if not chunks:
        return "Not found in your documents."

    best_score = chunks[0]["score"]

    if best_score < MIN_SIMILARITY_SCORE:
        return "Not found in your documents."

    context = ""

    for i, chunk in enumerate(
        chunks,
        start=1
    ):
        context += f"""
Source {i}
File: {chunk["file_name"]}
Page: {chunk.get("page_number")}
Chunk: {chunk.get("chunk_index")}
Confidence: {chunk.get("confidence")}
Text:
{chunk["text"]}
"""

    prompt = f"""
You are a secure document assistant.

Rules:
1. Answer ONLY using the provided document context.
2. If the answer is not clearly present, say: "Not found in your documents."
3. Do not use outside knowledge.
4. Keep the answer clear, short, and helpful.
5. Add one citation at the end of the answer using this format: (File: filename, Page: page number)
6. Use only the most relevant source for the citation.
7. Do not guess.

Document Context:
{context}

User Question:
{question}

Answer:
"""

    model = genai.GenerativeModel(
        "gemini-3.1-flash-lite"
    )

    response = model.generate_content(
        prompt
    )

    return response.text