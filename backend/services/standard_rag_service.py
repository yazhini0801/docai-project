from typing import List, Optional, Dict, Any
import time

from services.search_service import (
    semantic_search,
    generate_answer_from_context,
)


def run_standard_rag(
    supabase,
    user_id: str,
    question: str,
    document_ids: Optional[List[str]] = None,
    top_k: int = 5,
) -> Dict[str, Any]:

    start_time = time.perf_counter()

    # Step 1: Retrieve chunks using semantic similarity
    retrieved_chunks = semantic_search(
        supabase=supabase,
        user_id=user_id,
        question=question,
        document_ids=document_ids,
        top_k=top_k,
    )

    # Step 2: Use retrieved chunks directly
    chunks = retrieved_chunks

    # Step 3: Generate answer
    answer = generate_answer_from_context(
        question,
        chunks,
    )

    # Step 4: Confidence
    best_score = chunks[0]["score"] if chunks else 0

    if best_score >= 0.75:
        confidence = "HIGH"
    elif best_score >= 0.55:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # Step 5: Response time
    response_time = time.perf_counter() - start_time

    return {
        "answer": answer,
        "confidence": confidence,
        "best_score": round(best_score, 4),
        "chunks": chunks,
        "chunks_used": len(chunks),
        "retrieved_chunks": len(retrieved_chunks),
        "response_time": round(response_time, 4),
        "rag_mode": "standard",
    }