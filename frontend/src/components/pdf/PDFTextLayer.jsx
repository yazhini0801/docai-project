function PDFTextLayer() {
    return (
        <div
            id="pdf-text-layer"
            style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: "none",
            }}
        />
    );
}

export default PDFTextLayer;