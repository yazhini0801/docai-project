function PDFToolbar({
    currentPage,
    totalPages,
    zoom,
    onPrevious,
    onNext,
    onJump,
    onZoomIn,
    onZoomOut,
}) {
    return (
        <div
            style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: "12px",
                padding: "15px",
                background: "#ffffff",
                borderBottom: "1px solid #ddd",
                position: "sticky",
                top: 0,
                zIndex: 100,
            }}
        >
            <button
                onClick={onPrevious}
                disabled={currentPage <= 1}
            >
                ◀ Previous
            </button>

            <span
                style={{
                    fontWeight: "bold",
                }}
            >
                Page {currentPage} / {totalPages}
            </span>

            <input
                type="number"
                min={1}
                max={totalPages}
                value={currentPage}
                onChange={(e) => onJump(Number(e.target.value))}
                style={{
                    width: "70px",
                    textAlign: "center",
                    padding: "5px",
                }}
            />

            <button
                onClick={onNext}
                disabled={currentPage >= totalPages}
            >
                Next ▶
            </button>

            <div
                style={{
                    width: "1px",
                    height: "30px",
                    background: "#ddd",
                }}
            />

            <button onClick={onZoomOut}>
                −
            </button>

            <span>
                {Math.round(zoom * 100)}%
            </span>

            <button onClick={onZoomIn}>
                +
            </button>
        </div>
    );
}

export default PDFToolbar;