import { useEffect, useRef } from "react";

function PDFCanvas({
    pdfDoc,
    currentPage,
    zoom,
    drawHighlight,
    highlightText,
}) {
    const canvasRef = useRef(null);
    const renderTaskRef = useRef(null);

    useEffect(() => {
        async function renderPage() {
            if (!pdfDoc || !canvasRef.current) return;

            try {
                if (renderTaskRef.current) {
                    renderTaskRef.current.cancel();
                }

                const page = await pdfDoc.getPage(currentPage);

                const canvas = canvasRef.current;
                const context = canvas.getContext("2d");

                const viewport = page.getViewport({
                    scale: zoom,
                });

                canvas.width = viewport.width;
                canvas.height = viewport.height;

                const renderTask = page.render({
                    canvasContext: context,
                    viewport,
                });

                renderTaskRef.current = renderTask;

                await renderTask.promise;

                if (drawHighlight) {
                    await drawHighlight(
                        page,
                        viewport,
                        context,
                        highlightText
                    );
                }
            } catch (err) {
                if (err?.name !== "RenderingCancelledException") {
                    console.error(err);
                }
            }
        }

        renderPage();

        return () => {
            if (renderTaskRef.current) {
                renderTaskRef.current.cancel();
            }
        };
    }, [
        pdfDoc,
        currentPage,
        zoom,
        drawHighlight,
        highlightText,
    ]);

    return (
        <div
            style={{
                display: "flex",
                justifyContent: "center",
                padding: "20px",
                overflow: "auto",
            }}
        >
            <canvas
                ref={canvasRef}
                style={{
                    background: "#ffffff",
                    boxShadow: "0 4px 20px rgba(0,0,0,0.15)",
                    borderRadius: "6px",
                    maxWidth: "100%",
                }}
            />
        </div>
    );
}

export default PDFCanvas;