function PDFLoader({ loading, error }) {
    if (loading) {
        return (
            <div
                style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    height: "80vh",
                    fontSize: "22px",
                    fontWeight: "bold",
                }}
            >
                Loading PDF...
            </div>
        );
    }

    if (error) {
        return (
            <div
                style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    height: "80vh",
                    color: "red",
                    fontSize: "20px",
                    fontWeight: "bold",
                }}
            >
                {error}
            </div>
        );
    }

    return null;
}

export default PDFLoader;