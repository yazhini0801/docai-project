import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";


function ChatPage() {
    const { folderId } = useParams();
    const navigate = useNavigate();

    const storageKey = `docai_compare_chat_state_${folderId}`;
    const folderName = localStorage.getItem("selectedFolderName");

    const [question, setQuestion] = useState("");
    const [standardResult, setStandardResult] = useState(null);
    const [docrankResult, setDocrankResult] = useState(null);
    const [evaluation, setEvaluation] = useState(null);

    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [restored, setRestored] = useState(false);

    const API_BASE_URL =
        import.meta.env.VITE_API_BASE_URL ||
        "http://127.0.0.1:8000";


    // ==================================================
    // RESTORE STATE
    // ==================================================

    useEffect(() => {
        const savedState = localStorage.getItem(storageKey);

        if (savedState) {
            try {
                const parsed = JSON.parse(savedState);

                setQuestion(parsed.question || "");
                setStandardResult(parsed.standardResult || null);
                setDocrankResult(parsed.docrankResult || null);
                setEvaluation(parsed.evaluation || null);
            } catch (error) {
                console.error(
                    "Failed to restore chat:",
                    error
                );
            }
        }

        setRestored(true);
    }, [storageKey]);


    // ==================================================
    // SAVE STATE
    // ==================================================

    useEffect(() => {
        if (!restored) return;

        localStorage.setItem(
            storageKey,
            JSON.stringify({
                question,
                standardResult,
                docrankResult,
                evaluation,
            })
        );
    }, [
        question,
        standardResult,
        docrankResult,
        evaluation,
        storageKey,
        restored,
    ]);


    // ==================================================
    // LOAD DOCUMENTS
    // ==================================================

    useEffect(() => {
        async function loadDocuments() {
            try {
                const token = localStorage.getItem("token");

                const response = await axios.get(
                    `${API_BASE_URL}/documents/`,
                    {
                        params: {
                            token,
                            folder_id: folderId,
                        },
                    }
                );

                setDocuments(
                    response.data.documents || []
                );
            } catch (error) {
                console.error(
                    "Document loading error:",
                    error
                );

                alert(
                    error.response?.data?.detail ||
                        "Failed to load documents"
                );
            }
        }

        loadDocuments();
    }, [folderId, API_BASE_URL]);


    // ==================================================
    // ASK QUESTION
    // ==================================================

    const askQuestion = async () => {
        if (!question.trim()) {
            alert("Please enter a question.");
            return;
        }

        if (documents.length === 0) {
            alert(
                "No documents are available in this folder."
            );
            return;
        }

        try {
            setLoading(true);

            setStandardResult(null);
            setDocrankResult(null);
            setEvaluation(null);

            const token = localStorage.getItem("token");

            const documentIds = documents.map(
                (doc) => doc.id
            );

            const response = await axios.post(
                `${API_BASE_URL}/chat/`,
                {
                    token,
                    question,
                    document_ids: documentIds,
                    top_k: 5,
                    rag_mode: "compare",
                }
            );

            setStandardResult(
                response.data.standard || null
            );

            setDocrankResult(
                response.data.docrank || null
            );

            setEvaluation(
                response.data.evaluation || null
            );
        } catch (error) {
            console.error(
                "Compare RAG Error:",
                error
            );

            const detail =
                error.response?.data?.detail ||
                "Failed to compare RAG pipelines.";

            if (
                String(detail).includes("429") ||
                String(detail)
                    .toLowerCase()
                    .includes("quota")
            ) {
                alert(
                    "Gemini API quota/rate limit reached. Please wait before trying again."
                );
            } else {
                alert(detail);
            }
        } finally {
            setLoading(false);
        }
    };


    // ==================================================
    // CLEAR
    // ==================================================

    const clearChat = () => {
        setQuestion("");
        setStandardResult(null);
        setDocrankResult(null);
        setEvaluation(null);

        localStorage.removeItem(storageKey);
    };


    // ==================================================
    // LOGOUT
    // ==================================================

    const logout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("selectedFolderName");

        navigate("/");
    };


    // ==================================================
    // OPEN PDF
    // ==================================================

    const openCitationPDF = (citation) => {
        const documentId = citation?.document_id;
        const pageNumber = citation?.page_number || 1;

        const highlightText =
            citation?.text ||
            citation?.preview ||
            "";

        if (!documentId) {
            alert("Document ID not found.");
            return;
        }

        navigate(
            `/viewer/${documentId}/${pageNumber}`,
            {
                state: {
                    highlightText,
                    returnTo: `/chat/${folderId}`,
                },
            }
        );
    };


    // ==================================================
    // CLEAN ANSWER
    // ==================================================

    const cleanAnswer = (answer = "") => {
        return answer
            .replace(
                /\(\s*File:[^)]+\)/gi,
                ""
            )
            .replace(
                /\n\s*\n\s*\n/g,
                "\n\n"
            )
            .trim();
    };


    // ==================================================
    // COPY
    // ==================================================

    const copyAnswer = async (answer) => {
        try {
            await navigator.clipboard.writeText(
                cleanAnswer(answer)
            );

            alert("Answer copied");
        } catch (error) {
            console.error(error);
            alert("Could not copy answer.");
        }
    };


    // ==================================================
    // CONFIDENCE STYLE
    // ==================================================

    const getConfidenceStyle = (confidence) => {
        if (confidence === "HIGH") {
            return {
                background: "#dcfce7",
                color: "#166534",
                label: "High Confidence",
            };
        }

        if (confidence === "MEDIUM") {
            return {
                background: "#fef9c3",
                color: "#854d0e",
                label: "Medium Confidence",
            };
        }

        return {
            background: "#fee2e2",
            color: "#991b1b",
            label: "Low Confidence",
        };
    };


    // ==================================================
    // FORMAT METRIC
    // ==================================================

    const formatMetric = (value) => {
        if (
            value === undefined ||
            value === null
        ) {
            return "—";
        }

        return `${(
            Number(value) * 100
        ).toFixed(1)}%`;
    };


    // ==================================================
    // CITATION CARD
    // ==================================================

    const renderCitation = (
        citation,
        isPrimary = false
    ) => {
        if (!citation) return null;

        return (
            <div style={styles.citationCard}>
                <div style={{ minWidth: 0 }}>
                    {isPrimary && (
                        <div style={styles.primaryTag}>
                            Primary citation
                        </div>
                    )}

                    <div style={styles.citationTitle}>
                        📄{" "}
                        {citation.file_name ||
                            "Unknown file"}
                    </div>

                    <div style={styles.citationMeta}>
                        Page{" "}
                        {citation.page_number || 1}
                    </div>

                    {citation.score !== undefined &&
                        citation.score !== null && (
                            <div
                                style={
                                    styles.citationScore
                                }
                            >
                                Similarity:{" "}
                                {Number(
                                    citation.score
                                ).toFixed(4)}
                            </div>
                        )}
                </div>

                <button
                    style={styles.openPdfButton}
                    onClick={() =>
                        openCitationPDF(citation)
                    }
                >
                    Open PDF →
                </button>
            </div>
        );
    };


    // ==================================================
    // RESULT PANEL
    // ==================================================

    const renderResultPanel = (
        title,
        subtitle,
        result,
        enhanced = false
    ) => {
        if (!result) return null;

        const confidenceStyle =
            getConfidenceStyle(
                result.confidence
            );

        const supporting =
            result.supporting_citations || [];

        return (
            <div
                style={{
                    ...styles.resultPanel,
                    ...(enhanced
                        ? styles.docrankPanel
                        : styles.standardPanel),
                }}
            >
                <div style={styles.resultHeader}>
                    <div>
                        <div
                            style={{
                                ...styles.pipelineBadge,
                                ...(enhanced
                                    ? styles.docrankBadge
                                    : styles.standardBadge),
                            }}
                        >
                            {enhanced
                                ? "ENHANCED"
                                : "BASELINE"}
                        </div>

                        <h2 style={styles.resultTitle}>
                            {title}
                        </h2>

                        <p
                            style={
                                styles.resultSubtitle
                            }
                        >
                            {subtitle}
                        </p>
                    </div>

                    <div
                        style={{
                            ...styles.confidenceBadge,
                            background:
                                confidenceStyle.background,
                            color:
                                confidenceStyle.color,
                        }}
                    >
                        ● {confidenceStyle.label}
                    </div>
                </div>

                <div style={styles.sectionBlock}>
                    <h3 style={styles.sectionTitle}>
                        Answer
                    </h3>

                    <div style={styles.answerBox}>
                        {result.answer}
                    </div>
                </div>

                <div style={styles.statsGrid}>
                    <div style={styles.statCard}>
                        <span
                            style={styles.statLabel}
                        >
                            Best Score
                        </span>

                        <strong
                            style={styles.statValue}
                        >
                            {result.best_score !==
                                undefined &&
                            result.best_score !== null
                                ? Number(
                                      result.best_score
                                  ).toFixed(4)
                                : "—"}
                        </strong>
                    </div>

                    <div style={styles.statCard}>
                        <span
                            style={styles.statLabel}
                        >
                            Response Time
                        </span>

                        <strong
                            style={styles.statValue}
                        >
                            {result.response_time !==
                                undefined &&
                            result.response_time !==
                                null
                                ? `${Number(
                                      result.response_time
                                  ).toFixed(2)} s`
                                : "—"}
                        </strong>
                    </div>

                    <div style={styles.statCard}>
                        <span
                            style={styles.statLabel}
                        >
                            Retrieved
                        </span>

                        <strong
                            style={styles.statValue}
                        >
                            {result.retrieved_chunks ??
                                "—"}
                        </strong>
                    </div>

                    <div style={styles.statCard}>
                        <span
                            style={styles.statLabel}
                        >
                            Chunks Used
                        </span>

                        <strong
                            style={styles.statValue}
                        >
                            {result.chunks_used ?? "—"}
                        </strong>
                    </div>
                </div>

                {enhanced &&
                    result.documents_ranked !==
                        undefined && (
                        <div
                            style={
                                styles.enhancedInfo
                            }
                        >
                            Documents ranked by
                            DocRank:{" "}
                            <strong>
                                {
                                    result.documents_ranked
                                }
                            </strong>
                        </div>
                    )}

                <div style={styles.sectionBlock}>
                    <h3 style={styles.sectionTitle}>
                        ⭐ Primary Source
                    </h3>

                    {result.primary_citation ? (
                        renderCitation(
                            result.primary_citation,
                            true
                        )
                    ) : (
                        <p style={styles.mutedText}>
                            No primary citation.
                        </p>
                    )}
                </div>

                <div style={styles.sectionBlock}>
                    <h3 style={styles.sectionTitle}>
                        📚 Supporting Sources
                    </h3>

                    {supporting.length > 0 ? (
                        <div
                            style={
                                styles.citationList
                            }
                        >
                            {supporting.map(
                                (
                                    citation,
                                    index
                                ) => (
                                    <div key={index}>
                                        {renderCitation(
                                            citation
                                        )}
                                    </div>
                                )
                            )}
                        </div>
                    ) : (
                        <p style={styles.mutedText}>
                            No supporting citations.
                        </p>
                    )}
                </div>

                <div style={styles.finalSection}>
                    <div style={styles.finalHeader}>
                        <h3
                            style={
                                styles.sectionTitle
                            }
                        >
                            Final Answer
                        </h3>

                        <button
                            style={styles.copyButton}
                            onClick={() =>
                                copyAnswer(
                                    result.answer
                                )
                            }
                        >
                            Copy
                        </button>
                    </div>

                    <div
                        style={styles.finalAnswer}
                    >
                        {cleanAnswer(
                            result.answer
                        )}
                    </div>
                </div>
            </div>
        );
    };


    // ==================================================
    // COMPARISON
    // ==================================================

    const renderComparison = () => {
        if (
            !standardResult ||
            !docrankResult
        ) {
            return null;
        }

        const standardTime =
            Number(
                standardResult.response_time
            ) || 0;

        const docrankTime =
            Number(
                docrankResult.response_time
            ) || 0;

        const standardScore =
            Number(
                standardResult.best_score
            ) || 0;

        const docrankScore =
            Number(
                docrankResult.best_score
            ) || 0;

        const standardEvaluation =
            evaluation?.standard || {};

        const docrankEvaluation =
            evaluation?.docrank || {};

        const betterSystem =
            evaluation?.better_system;

        const improvement =
            evaluation?.docrank_improvement;

        return (
            <section
                style={styles.comparisonSection}
            >
                <div
                    style={styles.comparisonHeader}
                >
                    <p
                        style={
                            styles.comparisonEyebrow
                        }
                    >
                        RAG EVALUATION
                    </p>

                    <h2
                        style={
                            styles.comparisonTitle
                        }
                    >
                        Performance Comparison
                    </h2>

                    <p
                        style={
                            styles.comparisonDescription
                        }
                    >
                        Compare Standard RAG with
                        the enhanced RankFusion-RAG
                        pipeline.
                    </p>
                </div>

                <div
                    style={styles.tableWrapper}
                >
                    <table
                        style={
                            styles.comparisonTable
                        }
                    >
                        <thead>
                            <tr>
                                <th
                                    style={
                                        styles.tableHeader
                                    }
                                >
                                    Metric
                                </th>

                                <th
                                    style={
                                        styles.tableHeader
                                    }
                                >
                                    Standard RAG
                                </th>

                                <th
                                    style={
                                        styles.tableHeader
                                    }
                                >
                                    RankFusion-RAG
                                </th>
                            </tr>
                        </thead>

                        <tbody>
                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Answer Relevance
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.answer_relevance
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.answer_relevance
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Context Relevance
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.context_relevance
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.context_relevance
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Citation Correctness
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.citation_correctness
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.citation_correctness
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Faithfulness
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.faithfulness
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.faithfulness
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Overall Score
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.overall_score
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.overall_score
                                    )}
                                </td>
                            </tr>

                            {/* PROJECT METRICS */}

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Answer Accuracy
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.answer_accuracy
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.answer_accuracy
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Citation Accuracy
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.citation_accuracy
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.citation_accuracy
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Retrieval Precision
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.retrieval_precision
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.retrieval_precision
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Hallucination Rate
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.hallucination_rate
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.hallucination_rate
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Project Score
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        standardEvaluation.project_score
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {formatMetric(
                                        docrankEvaluation.project_score
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Best Retrieval Score
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {standardScore.toFixed(
                                        4
                                    )}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {docrankScore.toFixed(
                                        4
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Confidence
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {standardResult.confidence ||
                                        "—"}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {docrankResult.confidence ||
                                        "—"}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Retrieved Chunks
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {standardResult.retrieved_chunks ??
                                        "—"}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {docrankResult.retrieved_chunks ??
                                        "—"}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Chunks Used
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {standardResult.chunks_used ??
                                        "—"}
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {docrankResult.chunks_used ??
                                        "—"}
                                </td>
                            </tr>

                            <tr>
                                <td
                                    style={
                                        styles.tableCellLabel
                                    }
                                >
                                    Response Time
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {standardTime.toFixed(
                                        2
                                    )}{" "}
                                    s
                                </td>

                                <td
                                    style={
                                        styles.tableCell
                                    }
                                >
                                    {docrankTime.toFixed(
                                        2
                                    )}{" "}
                                    s
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                {evaluation && (
                    <div style={styles.winnerCard}>
                        <div
                            style={
                                styles.winnerIcon
                            }
                        >
                            🏆
                        </div>

                        <div>
                            <p
                                style={
                                    styles.winnerLabel
                                }
                            >
                                Better Result
                            </p>

                            <h3
                                style={
                                    styles.winnerTitle
                                }
                            >
                                {betterSystem ===
                                "docrank"
                                    ? "RankFusion-RAG"
                                    : betterSystem ===
                                      "standard"
                                    ? "Standard RAG"
                                    : "Tie"}
                            </h3>

                            {improvement !==
                                undefined &&
                                improvement !==
                                    null && (
                                    <p
                                        style={
                                            styles.improvementText
                                        }
                                    >
                                        RankFusion
                                        improvement:{" "}
                                        {(
                                            Number(
                                                improvement
                                            ) * 100
                                        ).toFixed(1)}
                                        %
                                    </p>
                                )}
                        </div>
                    </div>
                )}

                <div style={styles.metricsNotice}>
                    These relevance, accuracy,
                    correctness, precision,
                    faithfulness and hallucination
                    scores are currently calculated
                    using the local development
                    evaluation service. They can
                    later be validated using the
                    final evaluation methodology.
                </div>
            </section>
        );
    };


    // ==================================================
    // UI
    // ==================================================

    return (
        <div style={styles.page}>
            <header style={styles.navbar}>
                <div style={styles.brand}>
                    <div style={styles.logo}>
                        D
                    </div>

                    <div>
                        <h2
                            style={
                                styles.brandTitle
                            }
                        >
                            DocAI
                        </h2>

                        <p
                            style={
                                styles.brandSubtitle
                            }
                        >
                            Secure Document
                            Assistant
                        </p>
                    </div>
                </div>

                <div style={styles.navActions}>
                    <button
                        style={
                            styles.secondaryButton
                        }
                        onClick={() =>
                            navigate(
                                "/dashboard"
                            )
                        }
                    >
                        Dashboard
                    </button>

                    <button
                        style={
                            styles.primaryNavButton
                        }
                        onClick={() =>
                            navigate(
                                `/upload/${folderId}`
                            )
                        }
                    >
                        Upload
                    </button>

                    <button
                        style={
                            styles.logoutButton
                        }
                        onClick={logout}
                    >
                        Logout
                    </button>
                </div>
            </header>

            <main style={styles.main}>
                <section style={styles.hero}>
                    <p style={styles.eyebrow}>
                        DOCUMENT CHAT
                    </p>

                    <h1 style={styles.title}>
                        Compare your RAG pipelines
                    </h1>

                    <p style={styles.subtitle}>
                        Folder:{" "}
                        <strong>
                            {folderName ||
                                folderId}
                        </strong>{" "}
                        • {documents.length}{" "}
                        document
                        {documents.length !== 1
                            ? "s"
                            : ""}{" "}
                        loaded
                    </p>
                </section>

                <section
                    style={
                        styles.questionSection
                    }
                >
                    <div>
                        <h3
                            style={
                                styles.questionTitle
                            }
                        >
                            Ask once. Compare both.
                        </h3>

                        <p
                            style={
                                styles.questionDescription
                            }
                        >
                            The same question will
                            run through Standard RAG
                            and DocRank-RAG
                            automatically.
                        </p>
                    </div>

                    <textarea
                        rows="4"
                        placeholder="Ask anything about your documents..."
                        value={question}
                        onChange={(e) =>
                            setQuestion(
                                e.target.value
                            )
                        }
                        onKeyDown={(e) => {
                            if (
                                e.key ===
                                    "Enter" &&
                                !e.shiftKey
                            ) {
                                e.preventDefault();

                                if (!loading) {
                                    askQuestion();
                                }
                            }
                        }}
                        style={styles.textarea}
                    />

                    <div style={styles.inputFooter}>
                        <button
                            style={
                                styles.clearButton
                            }
                            onClick={clearChat}
                            disabled={loading}
                        >
                            Clear
                        </button>

                        <button
                            style={{
                                ...styles.compareButton,
                                opacity: loading
                                    ? 0.7
                                    : 1,
                                cursor: loading
                                    ? "not-allowed"
                                    : "pointer",
                            }}
                            onClick={askQuestion}
                            disabled={loading}
                        >
                            {loading
                                ? "Running both pipelines..."
                                : "Compare RAG →"}
                        </button>
                    </div>

                    <p style={styles.hint}>
                        Enter to compare • Shift +
                        Enter for a new line
                    </p>
                </section>

                {loading && (
                    <section
                        style={
                            styles.loadingCard
                        }
                    >
                        <div
                            style={styles.spinner}
                        />

                        <div>
                            <h3
                                style={
                                    styles.loadingTitle
                                }
                            >
                                Comparing RAG
                                pipelines...
                            </h3>

                            <p
                                style={
                                    styles.loadingText
                                }
                            >
                                Running Standard
                                RAG and DocRank-RAG
                                on the same question.
                            </p>
                        </div>
                    </section>
                )}

                {!loading &&
                    !standardResult &&
                    !docrankResult && (
                        <section
                            style={
                                styles.emptyState
                            }
                        >
                            <div
                                style={
                                    styles.emptyIcon
                                }
                            >
                                ⚖️
                            </div>

                            <h2
                                style={
                                    styles.emptyTitle
                                }
                            >
                                Ready to compare
                            </h2>

                            <p
                                style={
                                    styles.emptyText
                                }
                            >
                                Ask a question above.
                                Both RAG pipelines
                                will answer it so you
                                can compare retrieval
                                and performance.
                            </p>
                        </section>
                    )}

                {!loading &&
                    (standardResult ||
                        docrankResult) && (
                        <>
                            <div
                                style={
                                    styles.questionBubble
                                }
                            >
                                <span
                                    style={
                                        styles.youLabel
                                    }
                                >
                                    You
                                </span>

                                <p
                                    style={
                                        styles.questionText
                                    }
                                >
                                    {question}
                                </p>
                            </div>

                            <section
                                style={
                                    styles.resultsGrid
                                }
                            >
                                {renderResultPanel(
                                    "Standard RAG",
                                    "Baseline semantic retrieval pipeline",
                                    standardResult,
                                    false
                                )}

                                {renderResultPanel(
                                    "RankFusion-RAG",
                                    "Enhanced document-ranking pipeline",
                                    docrankResult,
                                    true
                                )}
                            </section>

                            {renderComparison()}
                        </>
                    )}
            </main>
        </div>
    );
}


const styles = {
    page: {
        minHeight: "100vh",
        background: "#f4f7fb",
        color: "#0f172a",
        fontFamily:
            "system-ui, Segoe UI, Roboto, sans-serif",
    },

    navbar: {
        height: "76px",
        background: "#ffffff",
        borderBottom:
            "1px solid #e2e8f0",
        display: "flex",
        alignItems: "center",
        justifyContent:
            "space-between",
        padding: "0 40px",
        boxShadow:
            "0 2px 10px rgba(15,23,42,0.04)",
    },

    brand: {
        display: "flex",
        alignItems: "center",
        gap: "12px",
    },

    logo: {
        width: "44px",
        height: "44px",
        borderRadius: "13px",
        background:
            "linear-gradient(135deg,#2563eb,#7c3aed)",
        color: "#ffffff",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: "900",
        fontSize: "21px",
    },

    brandTitle: {
        margin: 0,
        fontSize: "21px",
        fontWeight: "850",
        color: "#0f172a",
    },

    brandSubtitle: {
        margin: "2px 0 0",
        fontSize: "12px",
        color: "#64748b",
    },

    navActions: {
        display: "flex",
        gap: "10px",
    },

    secondaryButton: {
        padding: "9px 14px",
        borderRadius: "9px",
        border:
            "1px solid #cbd5e1",
        background: "#ffffff",
        color: "#334155",
        fontWeight: "700",
        cursor: "pointer",
    },

    primaryNavButton: {
        padding: "9px 14px",
        borderRadius: "9px",
        border: "none",
        background: "#2563eb",
        color: "#ffffff",
        fontWeight: "750",
        cursor: "pointer",
    },

    logoutButton: {
        padding: "9px 14px",
        borderRadius: "9px",
        border:
            "1px solid #fecaca",
        background: "#fff1f2",
        color: "#dc2626",
        fontWeight: "700",
        cursor: "pointer",
    },

    main: {
        maxWidth: "1500px",
        margin: "0 auto",
        padding:
            "38px 30px 70px",
    },

    hero: {
        marginBottom: "22px",
    },

    eyebrow: {
        margin: "0 0 7px",
        color: "#2563eb",
        fontWeight: "850",
        letterSpacing: "0.08em",
        fontSize: "12px",
    },

    title: {
        margin: 0,
        fontSize: "38px",
        fontWeight: "850",
        color: "#0f172a",
    },

    subtitle: {
        margin: "10px 0 0",
        color: "#64748b",
        fontSize: "14px",
    },

    questionSection: {
        background: "#ffffff",
        border:
            "1px solid #e2e8f0",
        borderRadius: "20px",
        padding: "22px",
        boxShadow:
            "0 10px 30px rgba(15,23,42,0.05)",
        marginBottom: "22px",
    },

    questionTitle: {
        margin: 0,
        fontSize: "18px",
        fontWeight: "850",
        color: "#0f172a",
    },

    questionDescription: {
        margin: "5px 0 16px",
        color: "#64748b",
        fontSize: "13px",
    },

    textarea: {
        width: "100%",
        boxSizing: "border-box",
        border:
            "1px solid #cbd5e1",
        borderRadius: "14px",
        padding: "15px",
        resize: "vertical",
        outline: "none",
        fontFamily: "inherit",
        fontSize: "14px",
        lineHeight: 1.6,
        background: "#ffffff",
        color: "#0f172a",
    },

    inputFooter: {
        display: "flex",
        justifyContent: "flex-end",
        gap: "10px",
        marginTop: "12px",
    },

    clearButton: {
        padding: "11px 16px",
        borderRadius: "10px",
        border:
            "1px solid #cbd5e1",
        background: "#ffffff",
        color: "#334155",
        fontWeight: "750",
        cursor: "pointer",
    },

    compareButton: {
        padding: "11px 18px",
        borderRadius: "10px",
        border: "none",
        background: "#2563eb",
        color: "#ffffff",
        fontWeight: "800",
    },

    hint: {
        margin: "8px 0 0",
        textAlign: "right",
        color: "#94a3b8",
        fontSize: "12px",
    },

    loadingCard: {
        background: "#eff6ff",
        border:
            "1px solid #bfdbfe",
        borderRadius: "18px",
        padding: "22px",
        display: "flex",
        alignItems: "center",
        gap: "16px",
        marginBottom: "22px",
    },

    spinner: {
        width: "34px",
        height: "34px",
        borderRadius: "50%",
        border:
            "4px solid #dbeafe",
        borderTop:
            "4px solid #2563eb",
    },

    loadingTitle: {
        margin: 0,
        fontSize: "17px",
        color: "#0f172a",
    },

    loadingText: {
        margin: "5px 0 0",
        color: "#64748b",
        fontSize: "13px",
    },

    emptyState: {
        background: "#ffffff",
        border:
            "1px solid #e2e8f0",
        borderRadius: "20px",
        padding: "70px 20px",
        textAlign: "center",
    },

    emptyIcon: {
        fontSize: "45px",
    },

    emptyTitle: {
        margin: "12px 0 6px",
        fontSize: "23px",
        color: "#0f172a",
    },

    emptyText: {
        maxWidth: "560px",
        margin: "0 auto",
        color: "#64748b",
        lineHeight: 1.6,
    },

    questionBubble: {
        background: "#eff6ff",
        border:
            "1px solid #bfdbfe",
        borderRadius: "16px",
        padding: "15px 18px",
        marginBottom: "18px",
    },

    youLabel: {
        color: "#2563eb",
        fontWeight: "850",
        fontSize: "12px",
    },

    questionText: {
        margin: "5px 0 0",
        lineHeight: 1.6,
        color: "#0f172a",
    },

    resultsGrid: {
        display: "grid",
        gridTemplateColumns:
            "repeat(auto-fit, minmax(500px, 1fr))",
        gap: "20px",
        alignItems: "start",
    },

    resultPanel: {
        background: "#ffffff",
        borderRadius: "22px",
        padding: "22px",
        boxShadow:
            "0 15px 35px rgba(15,23,42,0.06)",
    },

    standardPanel: {
        border:
            "1px solid #bfdbfe",
    },

    docrankPanel: {
        border:
            "1px solid #ddd6fe",
    },

    resultHeader: {
        display: "flex",
        justifyContent:
            "space-between",
        alignItems:
            "flex-start",
        gap: "12px",
        borderBottom:
            "1px solid #e2e8f0",
        paddingBottom: "17px",
    },

    pipelineBadge: {
        display:
            "inline-block",
        padding: "5px 9px",
        borderRadius: "999px",
        fontSize: "10px",
        fontWeight: "900",
        letterSpacing:
            "0.05em",
        marginBottom: "8px",
    },

    standardBadge: {
        background: "#dbeafe",
        color: "#1d4ed8",
    },

    docrankBadge: {
        background: "#ede9fe",
        color: "#6d28d9",
    },

    resultTitle: {
        margin: 0,
        fontSize: "25px",
        fontWeight: "850",
        color: "#0f172a",
    },

    resultSubtitle: {
        margin: "4px 0 0",
        color: "#64748b",
        fontSize: "12px",
    },

    confidenceBadge: {
        padding: "7px 10px",
        borderRadius: "999px",
        fontSize: "11px",
        fontWeight: "850",
        whiteSpace: "nowrap",
    },

    sectionBlock: {
        marginTop: "20px",
    },

    sectionTitle: {
        margin: "0 0 10px",
        fontSize: "16px",
        fontWeight: "850",
        color: "#0f172a",
    },

    answerBox: {
        padding: "16px",
        background: "#f8fafc",
        border:
            "1px solid #e2e8f0",
        borderRadius: "13px",
        lineHeight: 1.7,
        whiteSpace: "pre-wrap",
        fontSize: "14px",
        color: "#0f172a",
    },

    statsGrid: {
        display: "grid",
        gridTemplateColumns:
            "repeat(2, minmax(0, 1fr))",
        gap: "10px",
        marginTop: "16px",
    },

    statCard: {
        background: "#f8fafc",
        border:
            "1px solid #e2e8f0",
        borderRadius: "12px",
        padding: "12px",
        display: "flex",
        flexDirection: "column",
        gap: "4px",
    },

    statLabel: {
        color: "#64748b",
        fontSize: "11px",
        fontWeight: "700",
    },

    statValue: {
        fontSize: "16px",
        color: "#0f172a",
    },

    enhancedInfo: {
        marginTop: "12px",
        padding: "11px 13px",
        borderRadius: "11px",
        background: "#f5f3ff",
        color: "#5b21b6",
        fontSize: "12px",
    },

    citationList: {
        display: "grid",
        gap: "9px",
    },

    citationCard: {
        padding: "13px",
        border:
            "1px solid #e2e8f0",
        borderRadius: "12px",
        background: "#f8fafc",
        display: "flex",
        justifyContent:
            "space-between",
        alignItems: "center",
        gap: "10px",
    },

    primaryTag: {
        color: "#2563eb",
        fontWeight: "850",
        fontSize: "10px",
        marginBottom: "5px",
    },

    citationTitle: {
        fontSize: "12px",
        fontWeight: "800",
        overflow: "hidden",
        textOverflow:
            "ellipsis",
        color: "#0f172a",
    },

    citationMeta: {
        color: "#64748b",
        fontSize: "11px",
        marginTop: "4px",
    },

    citationScore: {
        color: "#64748b",
        fontSize: "10px",
        marginTop: "3px",
    },

    openPdfButton: {
        padding: "8px 11px",
        borderRadius: "9px",
        border: "none",
        background: "#2563eb",
        color: "#ffffff",
        fontWeight: "800",
        fontSize: "11px",
        cursor: "pointer",
        whiteSpace: "nowrap",
    },

    mutedText: {
        color: "#64748b",
        fontSize: "13px",
    },

    finalSection: {
        marginTop: "20px",
        borderTop:
            "1px solid #e2e8f0",
        paddingTop: "18px",
    },

    finalHeader: {
        display: "flex",
        justifyContent:
            "space-between",
        alignItems: "center",
    },

    copyButton: {
        padding: "7px 11px",
        borderRadius: "8px",
        border: "none",
        background: "#111827",
        color: "#ffffff",
        fontSize: "11px",
        fontWeight: "800",
        cursor: "pointer",
    },

    finalAnswer: {
        padding: "15px",
        background: "#f8fafc",
        border:
            "1px solid #e2e8f0",
        borderRadius: "12px",
        lineHeight: 1.7,
        whiteSpace: "pre-wrap",
        fontSize: "13px",
        color: "#0f172a",
    },

    comparisonSection: {
        marginTop: "24px",
        background: "#ffffff",
        border:
            "1px solid #e2e8f0",
        borderRadius: "22px",
        padding: "24px",
        boxShadow:
            "0 15px 35px rgba(15,23,42,0.05)",
    },

    comparisonHeader: {
        marginBottom: "18px",
    },

    comparisonEyebrow: {
        margin: "0 0 5px",
        color: "#7c3aed",
        fontSize: "11px",
        fontWeight: "900",
        letterSpacing:
            "0.08em",
    },

    comparisonTitle: {
        margin: 0,
        fontSize: "25px",
        color: "#0f172a",
    },

    comparisonDescription: {
        margin: "6px 0 0",
        color: "#64748b",
        fontSize: "13px",
    },

    tableWrapper: {
        overflowX: "auto",
        border:
            "1px solid #e2e8f0",
        borderRadius: "13px",
    },

    comparisonTable: {
        width: "100%",
        borderCollapse:
            "collapse",
        color: "#0f172a",
    },

    tableHeader: {
        background: "#f8fafc",
        padding: "13px",
        textAlign: "left",
        borderBottom:
            "1px solid #e2e8f0",
        fontSize: "12px",
        color: "#0f172a",
    },

    tableCellLabel: {
        padding: "13px",
        borderBottom:
            "1px solid #e2e8f0",
        fontWeight: "750",
        fontSize: "12px",
        color: "#0f172a",
    },

    tableCell: {
        padding: "13px",
        borderBottom:
            "1px solid #e2e8f0",
        fontSize: "12px",
        color: "#0f172a",
    },

    winnerCard: {
        marginTop: "18px",
        padding: "18px",
        borderRadius: "14px",
        background: "#ecfdf5",
        border:
            "1px solid #bbf7d0",
        display: "flex",
        alignItems: "center",
        gap: "14px",
    },

    winnerIcon: {
        fontSize: "34px",
    },

    winnerLabel: {
        margin: 0,
        color: "#64748b",
        fontSize: "11px",
        fontWeight: "800",
        textTransform:
            "uppercase",
    },

    winnerTitle: {
        margin: "3px 0 0",
        fontSize: "21px",
        color: "#166534",
    },

    improvementText: {
        margin: "5px 0 0",
        color: "#166534",
        fontSize: "12px",
    },

    metricsNotice: {
        marginTop: "16px",
        padding: "14px",
        background: "#f5f3ff",
        border:
            "1px solid #ddd6fe",
        borderRadius: "12px",
        color: "#5b21b6",
        fontSize: "12px",
        lineHeight: 1.6,
    },
};


export default ChatPage;

