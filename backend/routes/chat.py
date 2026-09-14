from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase import create_client
from dotenv import load_dotenv
import os
import re


from routes.documents import get_current_user
from services.standard_rag_service import run_standard_rag
from services.docrank_rag_service import run_docrank_rag
from services.evaluation_service import evaluate_comparison


load_dotenv()


router = APIRouter()


supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)


class ChatRequest(BaseModel):
    token: str
    question: str
    session_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = 5
    rag_mode: Optional[str] = "standard"


# --------------------------------------------------
# EXTRACT PAGE NUMBERS USED IN ANSWER
# --------------------------------------------------

def extract_used_pages_from_answer(answer: str):
    used_pages = set()

    matches = re.findall(
        r"page[:\s]+(\d+)",
        answer,
        flags=re.IGNORECASE,
    )

    for page in matches:
        try:
            used_pages.add(int(page))
        except ValueError:
            pass

    return used_pages


# --------------------------------------------------
# BUILD CITATION OBJECT
# --------------------------------------------------

def make_citation(chunk, confidence):
    return {
        "document_id": chunk["document_id"],
        "file_name": chunk["file_name"],
        "page_number": chunk.get("page_number"),
        "chunk_index": chunk.get("chunk_index"),
        "score": round(chunk["score"], 4),
        "confidence": chunk.get(
            "confidence",
            confidence,
        ),
        "preview": chunk["text"][:250],
        "text": chunk["text"],
    }


# --------------------------------------------------
# REMOVE DUPLICATE CITATIONS
# --------------------------------------------------

def unique_citations(citations):
    unique = {}

    for citation in citations:
        key = (
            citation["document_id"],
            citation["page_number"],
            citation["chunk_index"],
        )

        unique[key] = citation

    return list(unique.values())


# --------------------------------------------------
# PRIMARY + SUPPORTING CITATIONS
# --------------------------------------------------

def build_primary_and_supporting_citations(
    chunks,
    answer,
    confidence,
):
    if answer == "Not found in your documents.":
        return None, [], []

    used_pages = extract_used_pages_from_answer(
        answer
    )

    all_citations = [
        make_citation(
            chunk,
            confidence,
        )
        for chunk in chunks
    ]

    all_citations = unique_citations(
        all_citations
    )

    primary_citation = None

    if used_pages:
        for citation in all_citations:
            if (
                citation.get("page_number")
                in used_pages
            ):
                primary_citation = citation
                break

    if (
        not primary_citation
        and all_citations
    ):
        primary_citation = all_citations[0]

    supporting_citations = []

    for citation in all_citations:
        if not primary_citation:
            supporting_citations.append(
                citation
            )
            continue

        same_as_primary = (
            citation["document_id"]
            == primary_citation["document_id"]
            and citation["page_number"]
            == primary_citation["page_number"]
            and citation["chunk_index"]
            == primary_citation["chunk_index"]
        )

        if not same_as_primary:
            supporting_citations.append(
                citation
            )

    combined_citations = []

    if primary_citation:
        combined_citations.append(
            primary_citation
        )

    combined_citations.extend(
        supporting_citations
    )

    return (
        primary_citation,
        supporting_citations,
        combined_citations,
    )


# --------------------------------------------------
# PREPARE RESPONSE FOR ONE RAG PIPELINE
# --------------------------------------------------

def prepare_rag_response(rag_result):
    answer = rag_result["answer"]
    confidence = rag_result["confidence"]
    chunks = rag_result["chunks"]

    (
        primary_citation,
        supporting_citations,
        citations,
    ) = build_primary_and_supporting_citations(
        chunks=chunks,
        answer=answer,
        confidence=confidence,
    )

    response = {
        "answer": answer,
        "confidence": confidence,
        "best_score": rag_result["best_score"],
        "primary_citation": primary_citation,
        "supporting_citations":
            supporting_citations,
        "citations": citations,
        "chunks_used":
            rag_result["chunks_used"],
        "retrieved_chunks":
            rag_result["retrieved_chunks"],
        "response_time":
            rag_result["response_time"],
        "rag_mode":
            rag_result["rag_mode"],
    }

    if rag_result["rag_mode"] == "docrank":
        response["documents_ranked"] = (
            rag_result.get(
                "documents_ranked",
                0,
            )
        )

        response["document_ranking"] = (
            rag_result.get(
                "document_ranking",
                [],
            )
        )

    return response


# --------------------------------------------------
# CHAT ENDPOINT
# --------------------------------------------------

@router.post("/")
def chat_with_documents(request: ChatRequest):
    try:
        user = get_current_user(
            request.token
        )

        if not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty",
            )

        session_id = request.session_id

        # --------------------------------------------------
        # CREATE CHAT SESSION
        # --------------------------------------------------

        if not session_id:
            title = request.question[:50]

            session_result = (
                supabase
                .table("chat_sessions")
                .insert(
                    {
                        "user_id": user.id,
                        "title": title,
                    }
                )
                .execute()
            )

            session_id = (
                session_result
                .data[0]["id"]
            )

        # ==================================================
        # STANDARD RAG
        # ==================================================

        if request.rag_mode == "standard":

            rag_result = run_standard_rag(
                supabase=supabase,
                user_id=user.id,
                question=request.question,
                document_ids=
                    request.document_ids,
                top_k=request.top_k or 5,
            )

            result = prepare_rag_response(
                rag_result
            )

            supabase.table(
                "chat_messages"
            ).insert(
                {
                    "session_id": session_id,
                    "role": "user",
                    "message":
                        request.question,
                    "citations": [],
                }
            ).execute()

            supabase.table(
                "chat_messages"
            ).insert(
                {
                    "session_id": session_id,
                    "role": "assistant",
                    "message":
                        result["answer"],
                    "citations":
                        result["citations"],
                }
            ).execute()

            return {
                "session_id": session_id,
                "question":
                    request.question,
                **result,
            }

        # ==================================================
        # DOCRANK-RAG
        # ==================================================

        elif request.rag_mode == "docrank":

            rag_result = run_docrank_rag(
                supabase=supabase,
                user_id=user.id,
                question=request.question,
                document_ids=
                    request.document_ids,
                top_k=request.top_k or 5,
            )

            result = prepare_rag_response(
                rag_result
            )

            supabase.table(
                "chat_messages"
            ).insert(
                {
                    "session_id": session_id,
                    "role": "user",
                    "message":
                        request.question,
                    "citations": [],
                }
            ).execute()

            supabase.table(
                "chat_messages"
            ).insert(
                {
                    "session_id": session_id,
                    "role": "assistant",
                    "message":
                        result["answer"],
                    "citations":
                        result["citations"],
                }
            ).execute()

            return {
                "session_id": session_id,
                "question":
                    request.question,
                **result,
            }

        # ==================================================
        # COMPARE MODE
        # ==================================================

        elif request.rag_mode == "compare":

            # ------------------------------------------
            # Run Standard RAG
            # ------------------------------------------

            standard_raw = (
                run_standard_rag(
                    supabase=supabase,
                    user_id=user.id,
                    question=
                        request.question,
                    document_ids=
                        request.document_ids,
                    top_k=
                        request.top_k or 5,
                )
            )

            standard_result = (
                prepare_rag_response(
                    standard_raw
                )
            )

            # ------------------------------------------
            # Run DocRank-RAG
            # ------------------------------------------

            docrank_raw = (
                run_docrank_rag(
                    supabase=supabase,
                    user_id=user.id,
                    question=
                        request.question,
                    document_ids=
                        request.document_ids,
                    top_k=
                        request.top_k or 5,
                )
            )

            docrank_result = (
                prepare_rag_response(
                    docrank_raw
                )
            )

            # ------------------------------------------
            # EVALUATE BOTH RESULTS
            # ------------------------------------------

            evaluation = (
                evaluate_comparison(
                    question=request.question,
                    standard_result=
                        standard_result,
                    docrank_result=
                        docrank_result,
                )
            )

            # ------------------------------------------
            # SAVE QUESTION ONCE
            # ------------------------------------------

            supabase.table(
                "chat_messages"
            ).insert(
                {
                    "session_id":
                        session_id,
                    "role": "user",
                    "message":
                        request.question,
                    "citations": [],
                }
            ).execute()

            # ------------------------------------------
            # SAVE STANDARD ANSWER
            # ------------------------------------------

            supabase.table(
                "chat_messages"
            ).insert(
                {
                    "session_id":
                        session_id,
                    "role":
                        "assistant",
                    "message":
                        (
                            "[Standard RAG]\n"
                            + standard_result[
                                "answer"
                            ]
                        ),
                    "citations":
                        standard_result[
                            "citations"
                        ],
                }
            ).execute()

            # ------------------------------------------
            # SAVE DOCRANK ANSWER
            # ------------------------------------------

            supabase.table(
                "chat_messages"
            ).insert(
                {
                    "session_id":
                        session_id,
                    "role":
                        "assistant",
                    "message":
                        (
                            "[DocRank-RAG]\n"
                            + docrank_result[
                                "answer"
                            ]
                        ),
                    "citations":
                        docrank_result[
                            "citations"
                        ],
                }
            ).execute()

            # ------------------------------------------
            # RETURN BOTH RESULTS + EVALUATION
            # ------------------------------------------

            return {
                "session_id":
                    session_id,

                "question":
                    request.question,

                "rag_mode":
                    "compare",

                "standard":
                    standard_result,

                "docrank":
                    docrank_result,

                "evaluation":
                    evaluation,
            }

        # ==================================================
        # INVALID MODE
        # ==================================================

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported RAG mode: "
                    f"{request.rag_mode}"
                ),
            )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )