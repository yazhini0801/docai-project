import {
    useEffect,
    useRef,
    useState,
} from "react";

import {
    useLocation,
    useNavigate,
    useParams,
    useSearchParams,
} from "react-router-dom";

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
    const highlightLayerRef = useRef(null);
    const renderTaskRef = useRef(null);

    const [pdfDoc, setPdfDoc] = useState(null);

    const [currentPage, setCurrentPage] = useState(
        Number(pageNumber) || 1
    );

    const [totalPages, setTotalPages] = useState(0);

    const [loading, setLoading] = useState(true);
    const [rendering, setRendering] = useState(false);

    const [error, setError] = useState("");

    const [scale, setScale] = useState(1.5);


    // ==================================================
    // HIGHLIGHT DATA FROM CHAT PAGE
    // ==================================================

    const highlightText =
        location.state?.highlightText || "";

    const boundingBoxes =
        location.state?.boundingBoxes || [];


    const API_BASE_URL =
        import.meta.env.VITE_API_BASE_URL ||
        "http://127.0.0.1:8000";


    const token =
        searchParams.get("token") ||
        localStorage.getItem("token") ||
        localStorage.getItem("access_token");


    // ==================================================
    // OLD TEXT HIGHLIGHT FALLBACK
    // ==================================================

    async function renderTextLayer(page, viewport) {
        if (!textLayerRef.current) return;

        const textLayerDiv = textLayerRef.current;

        textLayerDiv.innerHTML = "";

        textLayerDiv.style.width =
            `${viewport.width}px`;

        textLayerDiv.style.height =
            `${viewport.height}px`;


        const textContent =
            await page.getTextContent();


        const textLayer =
            new pdfjsLib.TextLayer({
                textContentSource: textContent,
                container: textLayerDiv,
                viewport,
            });


        await textLayer.render();


        // If we already have coordinate highlights,
        // do NOT use text matching.
        if (
            Array.isArray(boundingBoxes) &&
            boundingBoxes.length > 0
        ) {
            return;
        }


        // Fallback for old PDFs that do not
        // contain bounding boxes.
        const range = findCitationRange(
            textContent.items,
            highlightText
        );

        highlightRange(
            textLayerDiv,
            range
        );
    }


    // ==================================================
    // NEW COORDINATE-BASED HIGHLIGHT
    // ==================================================

    function renderCoordinateHighlights(viewport) {
        const highlightLayer =
            highlightLayerRef.current;

        if (!highlightLayer) return;


        highlightLayer.innerHTML = "";

        highlightLayer.style.width =
            `${viewport.width}px`;

        highlightLayer.style.height =
            `${viewport.height}px`;


        if (
            !Array.isArray(boundingBoxes) ||
            boundingBoxes.length === 0
        ) {
            return;
        }


        boundingBoxes.forEach((box) => {
            const x0 = Number(box.x0);
            const y0 = Number(box.y0);
            const x1 = Number(box.x1);
            const y1 = Number(box.y1);


            if (
                !Number.isFinite(x0) ||
                !Number.isFinite(y0) ||
                !Number.isFinite(x1) ||
                !Number.isFinite(y1)
            ) {
                return;
            }


            /*
             * PyMuPDF coordinates use the
             * top-left of the PDF page.
             *
             * Our PDF.js viewer is rendered
             * with the same page orientation,
             * so scaling the coordinates gives
             * the correct screen position.
             */

            const left = x0 * scale;
            const top = y0 * scale;

            const width =
                Math.max(
                    (x1 - x0) * scale,
                    1
                );

            const height =
                Math.max(
                    (y1 - y0) * scale,
                    1
                );


            const highlight =
                document.createElement("div");


            highlight.style.position =
                "absolute";

            highlight.style.left =
                `${left}px`;

            highlight.style.top =
                `${top}px`;

            highlight.style.width =
                `${width}px`;

            highlight.style.height =
                `${height}px`;

            highlight.style.background =
                "rgba(255, 235, 59, 0.55)";

            highlight.style.borderRadius =
                "2px";

            highlight.style.pointerEvents =
                "none";


            highlightLayer.appendChild(
                highlight
            );
        });


        // Scroll to the first coordinate
        // highlight automatically.
        const firstHighlight =
            highlightLayer.firstElementChild;

        if (firstHighlight) {
            setTimeout(() => {
                firstHighlight.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                });
            }, 100);
        }
    }


    // ==================================================
    // LOAD PDF
    // ==================================================

    useEffect(() => {
        async function loadPDF() {
            try {
                setLoading(true);
                setError("");


                if (!documentId) {
                    setError(
                        "Document ID missing"
                    );

                    return;
                }


                if (!token) {
                    setError(
                        "Token missing. Please login again."
                    );

                    return;
                }


                const pdfUrl =
                    `${API_BASE_URL}/documents/file/${documentId}?token=${encodeURIComponent(
                        token
                    )}`;


                const loadingTask =
                    pdfjsLib.getDocument({
                        url: pdfUrl,
                        withCredentials: false,
                    });


                const loadedPdf =
                    await loadingTask.promise;


                setPdfDoc(loadedPdf);

                setTotalPages(
                    loadedPdf.numPages
                );

                setCurrentPage(
                    Number(pageNumber) || 1
                );

            } catch (err) {

                console.error(err);

                setError(
                    "Failed to load PDF"
                );

            } finally {

                setLoading(false);
            }
        }


        loadPDF();

    }, [
        documentId,
        pageNumber,
        token,
        API_BASE_URL,
    ]);


    // ==================================================
    // RENDER PDF PAGE
    // ==================================================

    useEffect(() => {

        async function renderPage() {

            if (
                !pdfDoc ||
                !canvasRef.current
            ) {
                return;
            }


            try {
                setRendering(true);


                if (
                    renderTaskRef.current
                ) {
                    renderTaskRef.current.cancel();
                }


                const page =
                    await pdfDoc.getPage(
                        currentPage
                    );


                const canvas =
                    canvasRef.current;


                const context =
                    canvas.getContext("2d");


                const viewport =
                    page.getViewport({
                        scale,
                    });


                canvas.width =
                    viewport.width;

                canvas.height =
                    viewport.height;


                canvas.style.width =
                    `${viewport.width}px`;

                canvas.style.height =
                    `${viewport.height}px`;


                const renderTask =
                    page.render({
                        canvasContext: context,
                        viewport,
                    });


                renderTaskRef.current =
                    renderTask;


                await renderTask.promise;


                // ------------------------------
                // Render selectable PDF text
                // ------------------------------

                try {
                    await renderTextLayer(
                        page,
                        viewport
                    );
                } catch (
                    textLayerError
                ) {
                    console.error(
                        "Text layer failed:",
                        textLayerError
                    );
                }


                // ------------------------------
                // Render coordinate highlight
                // ------------------------------

                renderCoordinateHighlights(
                    viewport
                );


            } catch (err) {

                if (
                    err?.name !==
                    "RenderingCancelledException"
                ) {
                    console.error(err);

                    setError(
                        "Failed to render page"
                    );
                }

            } finally {

                setRendering(false);
            }
        }


        renderPage();

    }, [
        pdfDoc,
        currentPage,
        highlightText,
        boundingBoxes,
        scale,
    ]);


    // ==================================================
    // PAGE CONTROLS
    // ==================================================

    function goToPreviousPage() {
        setCurrentPage(
            (prev) =>
                Math.max(
                    prev - 1,
                    1
                )
        );
    }


    function goToNextPage() {
        setCurrentPage(
            (prev) =>
                Math.min(
                    prev + 1,
                    totalPages
                )
        );
    }


    function handleJump(e) {
        const value =
            Number(e.target.value);


        if (!value) return;


        if (value < 1) {
            setCurrentPage(1);
        }

        else if (
            value > totalPages
        ) {
            setCurrentPage(
                totalPages
            );
        }

        else {
            setCurrentPage(
                value
            );
        }
    }


    // ==================================================
    // ZOOM CONTROLS
    // ==================================================

    function zoomIn() {
        setScale(
            (prev) =>
                Math.min(
                    prev + 0.25,
                    3
                )
        );
    }


    function zoomOut() {
        setScale(
            (prev) =>
                Math.max(
                    prev - 0.25,
                    0.75
                )
        );
    }


    function fitWidth() {
        setScale(1.25);
    }


    function fitPage() {
        setScale(0.95);
    }


    // ==================================================
    // LOADING
    // ==================================================

    if (loading) {
        return (
            <div style={styles.centerPage}>

                <div
                    style={styles.spinner}
                />

                <h2>
                    Loading PDF...
                </h2>

            </div>
        );
    }


    // ==================================================
    // ERROR
    // ==================================================

    if (error) {
        return (
            <div style={styles.centerPage}>

                <h2
                    style={{
                        color: "red",
                    }}
                >
                    {error}
                </h2>

                <button
                    style={
                        styles.primaryButton
                    }
                    onClick={() =>
                        navigate(-1)
                    }
                >
                    Back to Chat
                </button>

            </div>
        );
    }


    // ==================================================
    // UI
    // ==================================================

    return (
        <div style={styles.page}>

            <div style={styles.toolbar}>

                <button
                    style={
                        styles.primaryButton
                    }
                    onClick={() =>
                        navigate(-1)
                    }
                >
                    ← Back to Chat
                </button>


                <div style={styles.group}>

                    <button
                        style={
                            styles.button
                        }
                        onClick={
                            goToPreviousPage
                        }
                        disabled={
                            currentPage <= 1
                        }
                    >
                        ← Previous
                    </button>


                    <span
                        style={
                            styles.pageText
                        }
                    >
                        Page
                    </span>


                    <input
                        type="number"
                        min="1"
                        max={totalPages}
                        value={currentPage}
                        onChange={
                            handleJump
                        }
                        style={
                            styles.pageInput
                        }
                    />


                    <span
                        style={
                            styles.pageText
                        }
                    >
                        of {totalPages}
                    </span>


                    <button
                        style={
                            styles.button
                        }
                        onClick={
                            goToNextPage
                        }
                        disabled={
                            currentPage >=
                            totalPages
                        }
                    >
                        Next →
                    </button>

                </div>


                <div style={styles.group}>

                    <button
                        style={
                            styles.button
                        }
                        onClick={
                            zoomOut
                        }
                    >
                        −
                    </button>


                    <span
                        style={
                            styles.pageText
                        }
                    >
                        {Math.round(
                            scale * 100
                        )}
                        %
                    </span>


                    <button
                        style={
                            styles.button
                        }
                        onClick={
                            zoomIn
                        }
                    >
                        +
                    </button>


                    <button
                        style={
                            styles.button
                        }
                        onClick={
                            fitWidth
                        }
                    >
                        Fit Width
                    </button>


                    <button
                        style={
                            styles.button
                        }
                        onClick={
                            fitPage
                        }
                    >
                        Fit Page
                    </button>

                </div>

            </div>


            <div style={styles.viewerArea}>

                {rendering && (
                    <div
                        style={
                            styles.renderBadge
                        }
                    >
                        Rendering...
                    </div>
                )}


                <div style={styles.pdfWrapper}>

                    <canvas
                        ref={canvasRef}
                    />


                    {/* PDF TEXT LAYER */}

                    <div
                        ref={
                            textLayerRef
                        }
                        className="textLayer"
                        style={{
                            position:
                                "absolute",

                            left: 0,
                            top: 0,

                            zIndex: 2,

                            pointerEvents:
                                "auto",
                        }}
                    />


                    {/* NEW COORDINATE HIGHLIGHT LAYER */}

                    <div
                        ref={
                            highlightLayerRef
                        }
                        style={{
                            position:
                                "absolute",

                            left: 0,
                            top: 0,

                            zIndex: 3,

                            pointerEvents:
                                "none",
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

        flexDirection:
            "column",
    },


    toolbar: {
        position: "sticky",

        top: 0,

        zIndex: 10,

        background:
            "#ffffff",

        borderBottom:
            "1px solid #d9dee7",

        padding:
            "12px 16px",

        display:
            "flex",

        alignItems:
            "center",

        justifyContent:
            "space-between",

        gap: "12px",

        flexWrap:
            "wrap",

        boxShadow:
            "0 2px 8px rgba(0,0,0,0.08)",
    },


    group: {
        display:
            "flex",

        alignItems:
            "center",

        gap: "8px",

        flexWrap:
            "wrap",
    },


    button: {
        padding:
            "8px 12px",

        border:
            "1px solid #cfd6e4",

        borderRadius:
            "8px",

        background:
            "#ffffff",

        cursor:
            "pointer",

        fontWeight:
            500,
    },


    primaryButton: {
        padding:
            "9px 14px",

        border:
            "none",

        borderRadius:
            "8px",

        background:
            "#2563eb",

        color:
            "#ffffff",

        cursor:
            "pointer",

        fontWeight:
            600,
    },


    pageText: {
        fontWeight:
            600,

        color:
            "#334155",
    },


    pageInput: {
        width:
            "65px",

        padding:
            "7px",

        textAlign:
            "center",

        border:
            "1px solid #cfd6e4",

        borderRadius:
            "8px",
    },


    viewerArea: {
        position:
            "relative",

        flex: 1,

        overflow:
            "auto",

        padding:
            "24px",

        display:
            "flex",

        justifyContent:
            "center",

        alignItems:
            "flex-start",
    },


    pdfWrapper: {
        position:
            "relative",

        background:
            "#ffffff",

        boxShadow:
            "0 8px 30px rgba(0,0,0,0.18)",

        borderRadius:
            "4px",
    },


    renderBadge: {
        position:
            "fixed",

        top:
            "80px",

        right:
            "24px",

        background:
            "#111827",

        color:
            "#ffffff",

        padding:
            "8px 12px",

        borderRadius:
            "8px",

        zIndex:
            20,

        fontSize:
            "14px",
    },


    centerPage: {
        minHeight:
            "100vh",

        display:
            "flex",

        flexDirection:
            "column",

        justifyContent:
            "center",

        alignItems:
            "center",

        gap:
            "14px",

        background:
            "#eef1f5",
    },


    spinner: {
        width:
            "42px",

        height:
            "42px",

        border:
            "5px solid #dbe3ef",

        borderTop:
            "5px solid #2563eb",

        borderRadius:
            "50%",

        animation:
            "spin 1s linear infinite",
    },
};


export default PDFViewerPage;