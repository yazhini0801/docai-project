import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import * as pdfjsLib from "pdfjs-dist/build/pdf.mjs";
import "pdfjs-dist/build/pdf.worker.mjs";
import "pdfjs-dist/web/pdf_viewer.css";

import { highlightRange } from "../utils/pdfHighlight";
import { findCitationRange } from "../utils/pdfSearchEngine";

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/build/pdf.worker.mjs",
    import.meta.url
).toString();

function PDFViewerPage() {
    const { documentId, pageNumber } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    const canvasRef = useRef(null);
    const textLayerRef = useRef(null);
    const renderTaskRef = useRef(null);

    const [pdfDoc, setPdfDoc] = useState(null);
    const [currentPage, setCurrentPage] = useState(Number(pageNumber) || 1);
    const [totalPages, setTotalPages] = useState(0);
    const [loading, setLoading] = useState(true);
    const [rendering, setRendering] = useState(false);
    const [error, setError] = useState("");
    const [scale, setScale] = useState(1.5);

    const highlightText = location.state?.highlightText || "";

    const API_BASE_URL =
        import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

    const token =
        searchParams.get("token") ||
        localStorage.getItem("token") ||
        localStorage.getItem("access_token");

    async function renderTextLayer(page, viewport) {
        if (!textLayerRef.current) return;

        const textLayerDiv = textLayerRef.current;
        textLayerDiv.innerHTML = "";
        textLayerDiv.style.width = `${viewport.width}px`;
        textLayerDiv.style.height = `${viewport.height}px`;

        const textContent = await page.getTextContent();

        const textLayer = new pdfjsLib.TextLayer({
            textContentSource: textContent,
            container: textLayerDiv,
            viewport,
        });

        await textLayer.render();

        const range = findCitationRange(textContent.items, highlightText);
        highlightRange(textLayerDiv, range);
    }

    useEffect(() => {
        async function loadPDF() {
            try {
                setLoading(true);
                setError("");

                if (!documentId) {
                    setError("Document ID missing");
                    return;
                }

                if (!token) {
                    setError("Token missing. Please login again.");
                    return;
                }

                const pdfUrl = `${API_BASE_URL}/documents/file/${documentId}?token=${encodeURIComponent(
                    token
                )}`;

                const loadingTask = pdfjsLib.getDocument({
                    url: pdfUrl,
                    withCredentials: false,
                });

                const loadedPdf = await loadingTask.promise;

                setPdfDoc(loadedPdf);
                setTotalPages(loadedPdf.numPages);
                setCurrentPage(Number(pageNumber) || 1);
            } catch (err) {
                console.error(err);
                setError("Failed to load PDF");
            } finally {
                setLoading(false);
            }
        }

        loadPDF();
    }, [documentId, pageNumber, token, API_BASE_URL]);

    useEffect(() => {
        async function renderPage() {
            if (!pdfDoc || !canvasRef.current) return;

            try {
                setRendering(true);

                if (renderTaskRef.current) {
                    renderTaskRef.current.cancel();
                }

                const page = await pdfDoc.getPage(currentPage);
                const canvas = canvasRef.current;
                const context = canvas.getContext("2d");

                const viewport = page.getViewport({ scale });

                canvas.width = viewport.width;
                canvas.height = viewport.height;
                canvas.style.width = `${viewport.width}px`;
                canvas.style.height = `${viewport.height}px`;

                const renderTask = page.render({
                    canvasContext: context,
                    viewport,
                });

                renderTaskRef.current = renderTask;

                await renderTask.promise;

                try {
                    await renderTextLayer(page, viewport);
                } catch (textLayerError) {
                    console.error("Text layer failed:", textLayerError);
                }
            } catch (err) {
                if (err?.name !== "RenderingCancelledException") {
                    console.error(err);
                    setError("Failed to render page");
                }
            } finally {
                setRendering(false);
            }
        }

        renderPage();
    }, [pdfDoc, currentPage, highlightText, scale]);

    function goToPreviousPage() {
        setCurrentPage((prev) => Math.max(prev - 1, 1));
    }

    function goToNextPage() {
        setCurrentPage((prev) => Math.min(prev + 1, totalPages));
    }

    function handleJump(e) {
        const value = Number(e.target.value);

        if (!value) return;

        if (value < 1) setCurrentPage(1);
        else if (value > totalPages) setCurrentPage(totalPages);
        else setCurrentPage(value);
    }

    function zoomIn() {
        setScale((prev) => Math.min(prev + 0.25, 3));
    }

    function zoomOut() {
        setScale((prev) => Math.max(prev - 0.25, 0.75));
    }

    function fitWidth() {
        setScale(1.25);
    }

    function fitPage() {
        setScale(0.95);
    }

    if (loading) {
        return (
            <div style={styles.centerPage}>
                <div style={styles.spinner}></div>
                <h2>Loading PDF...</h2>
            </div>
        );
    }

    if (error) {
        return (
            <div style={styles.centerPage}>
                <h2 style={{ color: "red" }}>{error}</h2>
                <button style={styles.primaryButton} onClick={() => navigate(-1)}>
                    Back to Chat
                </button>
            </div>
        );
    }

    return (
        <div style={styles.page}>
            <div style={styles.toolbar}>
                <button style={styles.primaryButton} onClick={() => navigate(-1)}>
                    ← Back to Chat
                </button>

                <div style={styles.group}>
                    <button
                        style={styles.button}
                        onClick={goToPreviousPage}
                        disabled={currentPage <= 1}
                    >
                        ← Previous
                    </button>

                    <span style={styles.pageText}>
                        Page
                    </span>

                    <input
                        type="number"
                        min="1"
                        max={totalPages}
                        value={currentPage}
                        onChange={handleJump}
                        style={styles.pageInput}
                    />

                    <span style={styles.pageText}>of {totalPages}</span>

                    <button
                        style={styles.button}
                        onClick={goToNextPage}
                        disabled={currentPage >= totalPages}
                    >
                        Next →
                    </button>
                </div>

                <div style={styles.group}>
                    <button style={styles.button} onClick={zoomOut}>
                        −
                    </button>

                    <span style={styles.pageText}>{Math.round(scale * 100)}%</span>

                    <button style={styles.button} onClick={zoomIn}>
                        +
                    </button>

                    <button style={styles.button} onClick={fitWidth}>
                        Fit Width
                    </button>

                    <button style={styles.button} onClick={fitPage}>
                        Fit Page
                    </button>
                </div>
            </div>

            <div style={styles.viewerArea}>
                {rendering && (
                    <div style={styles.renderBadge}>
                        Rendering...
                    </div>
                )}

                <div style={styles.pdfWrapper}>
                    <canvas ref={canvasRef} />

                    <div
                        ref={textLayerRef}
                        className="textLayer"
                        style={{
                            position: "absolute",
                            left: 0,
                            top: 0,
                            pointerEvents: "auto",
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

const styles = {
    page: {
        minHeight: "100vh",
        background: "#eef1f5",
        display: "flex",
        flexDirection: "column",
    },
    toolbar: {
        position: "sticky",
        top: 0,
        zIndex: 10,
        background: "#ffffff",
        borderBottom: "1px solid #d9dee7",
        padding: "12px 16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px",
        flexWrap: "wrap",
        boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
    },
    group: {
        display: "flex",
        alignItems: "center",
        gap: "8px",
        flexWrap: "wrap",
    },
    button: {
        padding: "8px 12px",
        border: "1px solid #cfd6e4",
        borderRadius: "8px",
        background: "#ffffff",
        cursor: "pointer",
        fontWeight: 500,
    },
    primaryButton: {
        padding: "9px 14px",
        border: "none",
        borderRadius: "8px",
        background: "#2563eb",
        color: "#ffffff",
        cursor: "pointer",
        fontWeight: 600,
    },
    pageText: {
        fontWeight: 600,
        color: "#334155",
    },
    pageInput: {
        width: "65px",
        padding: "7px",
        textAlign: "center",
        border: "1px solid #cfd6e4",
        borderRadius: "8px",
    },
    viewerArea: {
        position: "relative",
        flex: 1,
        overflow: "auto",
        padding: "24px",
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-start",
    },
    pdfWrapper: {
        position: "relative",
        background: "#ffffff",
        boxShadow: "0 8px 30px rgba(0,0,0,0.18)",
        borderRadius: "4px",
    },
    renderBadge: {
        position: "fixed",
        top: "80px",
        right: "24px",
        background: "#111827",
        color: "#ffffff",
        padding: "8px 12px",
        borderRadius: "8px",
        zIndex: 20,
        fontSize: "14px",
    },
    centerPage: {
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        gap: "14px",
        background: "#eef1f5",
    },
    spinner: {
        width: "42px",
        height: "42px",
        border: "5px solid #dbe3ef",
        borderTop: "5px solid #2563eb",
        borderRadius: "50%",
        animation: "spin 1s linear infinite",
    },
};

export default PDFViewerPage;