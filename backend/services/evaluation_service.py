import re
from typing import List, Dict, Any, Set


# ==========================================================
# TEXT HELPERS
# ==========================================================

STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "and",
    "or",
    "as",
    "at",
    "by",
    "from",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "into",
    "about",
    "what",
    "which",
    "who",
    "whom",
    "when",
    "where",
    "why",
    "how",
}


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"\(\s*file:[^)]+\)",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def tokenize(text: str) -> Set[str]:
    normalized = normalize_text(text)

    words = normalized.split()

    return {
        word
        for word in words
        if len(word) > 1
        and word not in STOP_WORDS
    }


# ==========================================================
# SCORE HELPERS
# ==========================================================

def clamp_score(score: float) -> float:
    return max(
        0.0,
        min(1.0, score),
    )


def round_score(score: float) -> float:
    return round(
        clamp_score(score),
        4,
    )


def token_overlap_score(
    source_text: str,
    target_text: str,
) -> float:

    source_tokens = tokenize(source_text)
    target_tokens = tokenize(target_text)

    if not source_tokens:
        return 0.0

    overlap = source_tokens.intersection(
        target_tokens
    )

    score = (
        len(overlap)
        / len(source_tokens)
    )

    return round_score(score)


# ==========================================================
# ANSWER RELEVANCE
# ==========================================================

def calculate_answer_relevance(
    question: str,
    answer: str,
) -> float:

    if not answer:
        return 0.0

    if (
        answer.strip().lower()
        == "not found in your documents."
    ):
        return 0.0

    question_tokens = tokenize(question)
    answer_tokens = tokenize(answer)

    if not question_tokens:
        return 0.0

    matching = (
        question_tokens
        .intersection(answer_tokens)
    )

    direct_overlap = (
        len(matching)
        / len(question_tokens)
    )

    answer_length_bonus = min(
        len(answer_tokens) / 20,
        1.0,
    )

    score = (
        0.85 * direct_overlap
        + 0.15 * answer_length_bonus
    )

    return round_score(score)


# ==========================================================
# CONTEXT RELEVANCE
# ==========================================================

def calculate_context_relevance(
    question: str,
    citations: List[Dict[str, Any]],
) -> float:

    if not citations:
        return 0.0

    question_tokens = tokenize(question)

    if not question_tokens:
        return 0.0

    citation_scores = []

    for citation in citations:
        text = (
            citation.get("text")
            or citation.get("preview")
            or ""
        )

        context_tokens = tokenize(text)

        if not context_tokens:
            continue

        overlap = (
            question_tokens
            .intersection(context_tokens)
        )

        score = (
            len(overlap)
            / len(question_tokens)
        )

        citation_scores.append(score)

    if not citation_scores:
        return 0.0

    citation_scores.sort(
        reverse=True
    )

    top_scores = citation_scores[:3]

    result = (
        sum(top_scores)
        / len(top_scores)
    )

    return round_score(result)


# ==========================================================
# CITATION CORRECTNESS
# ==========================================================

def calculate_citation_correctness(
    answer: str,
    citations: List[Dict[str, Any]],
) -> float:

    if not answer or not citations:
        return 0.0

    answer_tokens = tokenize(answer)

    if not answer_tokens:
        return 0.0

    support_scores = []

    for citation in citations:
        citation_text = (
            citation.get("text")
            or citation.get("preview")
            or ""
        )

        citation_tokens = tokenize(
            citation_text
        )

        if not citation_tokens:
            continue

        overlap = (
            answer_tokens
            .intersection(citation_tokens)
        )

        score = (
            len(overlap)
            / len(answer_tokens)
        )

        support_scores.append(score)

    if not support_scores:
        return 0.0

    best_support = max(
        support_scores
    )

    average_support = (
        sum(support_scores)
        / len(support_scores)
    )

    result = (
        0.7 * best_support
        + 0.3 * average_support
    )

    return round_score(result)


# ==========================================================
# FAITHFULNESS
# ==========================================================

def calculate_faithfulness(
    answer: str,
    citations: List[Dict[str, Any]],
) -> float:

    if not answer or not citations:
        return 0.0

    answer_tokens = tokenize(answer)

    if not answer_tokens:
        return 0.0

    combined_context = " ".join(
        (
            citation.get("text")
            or citation.get("preview")
            or ""
        )
        for citation in citations
    )

    context_tokens = tokenize(
        combined_context
    )

    if not context_tokens:
        return 0.0

    supported_tokens = (
        answer_tokens
        .intersection(context_tokens)
    )

    result = (
        len(supported_tokens)
        / len(answer_tokens)
    )

    return round_score(result)


# ==========================================================
# PROJECT METRIC 1 — ANSWER ACCURACY
# ==========================================================

def calculate_answer_accuracy(
    answer_relevance: float,
    faithfulness: float,
    citation_correctness: float,
) -> float:
    """
    Development proxy for answer accuracy.

    A stronger answer should:
    - address the question,
    - be grounded in the documents,
    - be supported by citations.
    """

    result = (
        0.40 * answer_relevance
        + 0.35 * faithfulness
        + 0.25 * citation_correctness
    )

    return round_score(result)


# ==========================================================
# PROJECT METRIC 2 — CITATION ACCURACY
# ==========================================================

def calculate_citation_accuracy(
    citation_correctness: float,
) -> float:
    """
    Citation accuracy is currently represented
    by citation correctness.
    """

    return round_score(
        citation_correctness
    )


# ==========================================================
# PROJECT METRIC 3 — RETRIEVAL PRECISION
# ==========================================================

def calculate_retrieval_precision(
    question: str,
    citations: List[Dict[str, Any]],
) -> float:
    """
    Development proxy for retrieval precision.

    Measures how strongly each retrieved chunk
    matches the important concepts in the question.

    Instead of counting a chunk as relevant when
    only one word matches, this calculates the
    proportion of question concepts found in each
    chunk.
    """

    if not citations:
        return 0.0

    question_tokens = tokenize(question)

    if not question_tokens:
        return 0.0

    relevance_scores = []

    for citation in citations:
        text = (
            citation.get("text")
            or citation.get("preview")
            or ""
        )

        context_tokens = tokenize(text)

        if not context_tokens:
            continue

        overlap = (
            question_tokens
            .intersection(context_tokens)
        )

        chunk_relevance = (
            len(overlap)
            / len(question_tokens)
        )

        relevance_scores.append(
            chunk_relevance
        )

    if not relevance_scores:
        return 0.0

    precision = (
        sum(relevance_scores)
        / len(relevance_scores)
    )

    return round_score(precision)


# ==========================================================
# PROJECT METRIC 4 — HALLUCINATION RATE
# ==========================================================

def calculate_hallucination_rate(
    faithfulness: float,
) -> float:
    """
    Unsupported answer proportion.

    Higher faithfulness means lower
    hallucination rate.
    """

    result = (
        1.0 - faithfulness
    )

    return round_score(result)


# ==========================================================
# OVERALL QUALITY SCORE
# ==========================================================

def calculate_overall_score(
    answer_relevance: float,
    context_relevance: float,
    citation_correctness: float,
    faithfulness: float,
) -> float:

    result = (
        0.30 * answer_relevance
        + 0.20 * context_relevance
        + 0.20 * citation_correctness
        + 0.30 * faithfulness
    )

    return round_score(result)


# ==========================================================
# PROJECT OVERALL SCORE
# ==========================================================

def calculate_project_score(
    answer_accuracy: float,
    citation_accuracy: float,
    retrieval_precision: float,
    hallucination_rate: float,
) -> float:
    """
    Higher:
    - answer accuracy
    - citation accuracy
    - retrieval precision

    Lower:
    - hallucination rate
    """

    hallucination_quality = (
        1.0 - hallucination_rate
    )

    result = (
        0.35 * answer_accuracy
        + 0.25 * citation_accuracy
        + 0.20 * retrieval_precision
        + 0.20 * hallucination_quality
    )

    return round_score(result)


# ==========================================================
# EVALUATE ONE RAG RESULT
# ==========================================================

def evaluate_rag_result(
    question: str,
    rag_result: Dict[str, Any],
) -> Dict[str, Any]:

    answer = (
        rag_result.get("answer")
        or ""
    )

    citations = (
        rag_result.get("citations")
        or []
    )

    response_time = float(
        rag_result.get(
            "response_time",
            0,
        )
        or 0
    )

    # ------------------------------------------------------
    # Existing RAG metrics
    # ------------------------------------------------------

    answer_relevance = (
        calculate_answer_relevance(
            question,
            answer,
        )
    )

    context_relevance = (
        calculate_context_relevance(
            question,
            citations,
        )
    )

    citation_correctness = (
        calculate_citation_correctness(
            answer,
            citations,
        )
    )

    faithfulness = (
        calculate_faithfulness(
            answer,
            citations,
        )
    )

    overall_score = (
        calculate_overall_score(
            answer_relevance,
            context_relevance,
            citation_correctness,
            faithfulness,
        )
    )

    # ------------------------------------------------------
    # Five project metrics
    # ------------------------------------------------------

    answer_accuracy = (
        calculate_answer_accuracy(
            answer_relevance,
            faithfulness,
            citation_correctness,
        )
    )

    citation_accuracy = (
        calculate_citation_accuracy(
            citation_correctness
        )
    )

    retrieval_precision = (
        calculate_retrieval_precision(
            question,
            citations,
        )
    )

    hallucination_rate = (
        calculate_hallucination_rate(
            faithfulness
        )
    )

    project_score = (
        calculate_project_score(
            answer_accuracy,
            citation_accuracy,
            retrieval_precision,
            hallucination_rate,
        )
    )

    return {
        # Existing metrics
        "answer_relevance":
            answer_relevance,

        "context_relevance":
            context_relevance,

        "citation_correctness":
            citation_correctness,

        "faithfulness":
            faithfulness,

        "overall_score":
            overall_score,

        # Five project metrics
        "answer_accuracy":
            answer_accuracy,

        "citation_accuracy":
            citation_accuracy,

        "retrieval_precision":
            retrieval_precision,

        "response_time":
            round(response_time, 4),

        "hallucination_rate":
            hallucination_rate,

        "project_score":
            project_score,
    }


# ==========================================================
# COMPARE STANDARD VS DOCRANK
# ==========================================================

def evaluate_comparison(
    question: str,
    standard_result: Dict[str, Any],
    docrank_result: Dict[str, Any],
) -> Dict[str, Any]:

    standard_metrics = (
        evaluate_rag_result(
            question,
            standard_result,
        )
    )

    docrank_metrics = (
        evaluate_rag_result(
            question,
            docrank_result,
        )
    )

    standard_score = (
        standard_metrics[
            "project_score"
        ]
    )

    docrank_score = (
        docrank_metrics[
            "project_score"
        ]
    )

    if docrank_score > standard_score:
        better_system = "docrank"

    elif standard_score > docrank_score:
        better_system = "standard"

    else:
        better_system = "tie"

    improvement = (
        docrank_score
        - standard_score
    )

    return {
        "standard":
            standard_metrics,

        "docrank":
            docrank_metrics,

        "better_system":
            better_system,

        "docrank_improvement":
            round(
                improvement,
                4,
            ),

        "evaluation_type":
            "local_heuristic",
    }