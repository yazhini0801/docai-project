import time
from typing import List, Optional, Dict, Any
from collections import defaultdict

from services.search_service import (
    semantic_search,
    rerank_chunks,
    generate_answer_from_context,
)


def calculate_document_scores(
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Rank documents using the relevance scores of their retrieved chunks.

    Document score combines:
    - Best chunk similarity
    - Average similarity of relevant chunks
    - Number of retrieved relevant chunks
    """

    if not chunks:
        return []

    grouped_documents = defaultdict(list)

    for chunk in chunks:
        grouped_documents[chunk["document_id"]].append(chunk)

    ranked_documents = []

    for document_id, document_chunks in grouped_documents.items():

        scores = [
            chunk["score"]
            for chunk in document_chunks
        ]

        best_score = max(scores)

        average_score = sum(scores) / len(scores)

        relevant_chunk_count = len(document_chunks)

        # Document-level ranking score
        document_score = (
            (0.60 * best_score)
            + (0.30 * average_score)
            + (0.10 * min(relevant_chunk_count / 5, 1.0))
        )

        ranked_documents.append({
            "document_id": document_id,
            "file_name": document_chunks[0]["file_name"],
            "document_score": document_score,
            "best_chunk_score": best_score,
            "average_chunk_score": average_score,
            "relevant_chunk_count": relevant_chunk_count,
            "chunks": document_chunks,
        })

    ranked_documents.sort(
        key=lambda item: item["document_score"],
        reverse=True,
    )

    return ranked_documents


def select_chunks_from_ranked_documents(
    ranked_documents: List[Dict[str, Any]],
    max_documents: int = 3,
) -> List[Dict[str, Any]]:
    """
    Keep chunks belonging to the highest-ranked documents.
    """

    selected_chunks = []

    top_documents = ranked_documents[:max_documents]

    for document in top_documents:
        selected_chunks.extend(document["chunks"])

    selected_chunks.sort(
        key=lambda chunk: chunk["score"],
        reverse=True,
    )

    return selected_chunks


def run_docrank_rag(
    supabase,
    user_id: str,
    question: str,
    document_ids: Optional[List[str]] = None,
    top_k: int = 5,
) -> Dict[str, Any]:

    start_time = time.perf_counter()

    # --------------------------------------------------
    # STEP 1: Broad semantic retrieval
    # --------------------------------------------------

    retrieved_chunks = semantic_search(
        supabase=supabase,
        user_id=user_id,
        question=question,
        document_ids=document_ids,
        top_k=30,
    )

    # --------------------------------------------------
    # STEP 2: Document-level ranking
    # --------------------------------------------------

    ranked_documents = calculate_document_scores(
        retrieved_chunks
    )

    # --------------------------------------------------
    # STEP 3: Select chunks from best documents
    # --------------------------------------------------

    document_filtered_chunks = (
        select_chunks_from_ranked_documents(
            ranked_documents,
            max_documents=3,
        )
    )

    # --------------------------------------------------
    # STEP 4: Rerank chunks
    # --------------------------------------------------

    chunks = rerank_chunks(
        question=question,
        chunks=document_filtered_chunks,
        top_n=top_k,
    )

    # --------------------------------------------------
    # STEP 5: Generate grounded answer
    # --------------------------------------------------

    answer = generate_answer_from_context(
        question,
        chunks,
    )

    # --------------------------------------------------
    # STEP 6: Confidence
    # --------------------------------------------------

    best_score = chunks[0]["score"] if chunks else 0

    if best_score >= 0.75:
        confidence = "HIGH"

    elif best_score >= 0.55:
        confidence = "MEDIUM"

    else:
        confidence = "LOW"

    # --------------------------------------------------
    # STEP 7: Response time
    # --------------------------------------------------

    response_time = time.perf_counter() - start_time

    document_ranking = []

    for rank, document in enumerate(
        ranked_documents,
        start=1,
    ):
        document_ranking.append({
            "rank": rank,
            "document_id": document["document_id"],
            "file_name": document["file_name"],
            "document_score": round(
                document["document_score"],
                4,
            ),
            "best_chunk_score": round(
                document["best_chunk_score"],
                4,
            ),
            "average_chunk_score": round(
                document["average_chunk_score"],
                4,
            ),
            "relevant_chunk_count":
                document["relevant_chunk_count"],
        })

    return {
        "answer": answer,
        "confidence": confidence,
        "best_score": round(best_score, 4),

        "chunks": chunks,

        "chunks_used": len(chunks),

        "retrieved_chunks": len(retrieved_chunks),

        "documents_ranked": len(ranked_documents),

        "document_ranking": document_ranking,

        "response_time": round(response_time, 4),

        "rag_mode": "docrank",
    }