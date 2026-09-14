function PDFHighlightLayer({ highlightText }) {
    if (!highlightText) return null;

    return (
        <div
            style={{
                position: "fixed",
                top: "80px",
                right: "20px",
                width: "320px",
                background: "#fff8c5",
                border: "1px solid #f0c000",
                borderRadius: "8px",
                padding: "12px",
                boxShadow: "0 4px 10px rgba(0,0,0,0.15)",
                zIndex: 1000,
            }}
        >
            <h4
                style={{
                    margin: "0 0 10px 0",
                }}
            >
                Citation Preview
            </h4>

            <div
                style={{
                    fontSize: "14px",
                    lineHeight: "1.5",
                    maxHeight: "220px",
                    overflowY: "auto",
                }}
            >
                {highlightText}
            </div>
        </div>
    );
}

export default PDFHighlightLayer;