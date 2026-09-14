import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

function UploadPage() {
    const { folderId } = useParams();
    const navigate = useNavigate();
    const fileInputRef = useRef(null);

    const [file, setFile] = useState(null);
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [documentsLoading, setDocumentsLoading] = useState(true);
    const [dragActive, setDragActive] = useState(false);

    const token = localStorage.getItem("token");
    const folderName = localStorage.getItem("selectedFolderName");

    const fetchDocuments = async () => {
        try {
            setDocumentsLoading(true);

            const response = await api.get(
                `/documents/?token=${token}&folder_id=${folderId}`
            );

            setDocuments(response.data.documents || []);
        } catch (error) {
            console.error(error);
            alert("Failed to load documents");
        } finally {
            setDocumentsLoading(false);
        }
    };

    const uploadDocument = async () => {
        if (!file) {
            alert("Please choose a PDF file");
            return;
        }

        const formData = new FormData();
        formData.append("token", token);
        formData.append("folder_id", folderId);
        formData.append("file", file);

        try {
            setLoading(true);

            const response = await api.post("/documents/upload", formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });

            console.log(response.data);
            alert("Document uploaded successfully");

            setFile(null);

            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }

            fetchDocuments();
        } catch (error) {
            console.error(error);
            alert(JSON.stringify(error.response?.data || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleFileSelect = (selectedFile) => {
        if (!selectedFile) return;

        if (selectedFile.type !== "application/pdf") {
            alert("Only PDF files are allowed");
            return;
        }

        setFile(selectedFile);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragActive(false);

        const droppedFile = e.dataTransfer.files?.[0];
        handleFileSelect(droppedFile);
    };

    const logout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("selectedFolderName");
        navigate("/");
    };

    useEffect(() => {
        if (!token) {
            navigate("/");
            return;
        }

        fetchDocuments();
    }, []);

    return (
        <div style={styles.page}>
            <header style={styles.navbar}>
                <div style={styles.brand}>
                    <div style={styles.logo}>D</div>
                    <div>
                        <h2 style={styles.brandTitle}>DocAI</h2>
                        <p style={styles.brandSubtitle}>
                            Secure Document Assistant
                        </p>
                    </div>
                </div>

                <div style={styles.navActions}>
                    <button
                        style={styles.secondaryButton}
                        onClick={() => navigate("/dashboard")}
                    >
                        Dashboard
                    </button>

                    <button
                        style={styles.primaryButton}
                        onClick={() => navigate(`/chat/${folderId}`)}
                    >
                        Open Chat
                    </button>

                    <button style={styles.logoutButton} onClick={logout}>
                        Logout
                    </button>
                </div>
            </header>

            <main style={styles.main}>
                <section style={styles.hero}>
                    <div>
                        <p style={styles.eyebrow}>Folder workspace</p>
                        <h1 style={styles.title}>{folderName || "Selected Folder"}</h1>
                        <p style={styles.subtitle}>
                            Upload PDFs into this folder, process them securely, and
                            chat with your documents using citations.
                        </p>
                    </div>

                    <div style={styles.statsCard}>
                        <p style={styles.statsNumber}>{documents.length}</p>
                        <p style={styles.statsLabel}>Documents</p>
                    </div>
                </section>

                <section style={styles.uploadCard}>
                    <div>
                        <h3 style={styles.sectionTitle}>Upload PDF document</h3>
                        <p style={styles.sectionText}>
                            Choose a PDF file or drag and drop it below.
                        </p>
                    </div>

                    <div
                        style={{
                            ...styles.dropZone,
                            borderColor: dragActive ? "#2563eb" : "#cbd5e1",
                            background: dragActive ? "#eff6ff" : "#f8fafc",
                        }}
                        onDragOver={(e) => {
                            e.preventDefault();
                            setDragActive(true);
                        }}
                        onDragLeave={() => setDragActive(false)}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <div style={styles.uploadIcon}>📄</div>

                        <h3 style={styles.dropTitle}>
                            {file ? file.name : "Drop your PDF here"}
                        </h3>

                        <p style={styles.dropText}>
                            {file
                                ? "Ready to upload. Click the upload button below."
                                : "or click to browse from your computer"}
                        </p>

                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="application/pdf"
                            style={{ display: "none" }}
                            onChange={(e) => handleFileSelect(e.target.files[0])}
                        />
                    </div>

                    <div style={styles.uploadActions}>
                        {file && (
                            <button
                                style={styles.clearButton}
                                onClick={() => {
                                    setFile(null);
                                    if (fileInputRef.current) {
                                        fileInputRef.current.value = "";
                                    }
                                }}
                            >
                                Remove File
                            </button>
                        )}

                        <button
                            style={styles.uploadButton}
                            onClick={uploadDocument}
                            disabled={loading}
                        >
                            {loading ? "Uploading & Processing..." : "Upload PDF"}
                        </button>
                    </div>

                    {loading && (
                        <div style={styles.processingBox}>
                            <div style={styles.spinner}></div>
                            <div>
                                <strong>Processing document...</strong>
                                <p style={styles.processingText}>
                                    Extracting text, creating chunks, and generating
                                    embeddings.
                                </p>
                            </div>
                        </div>
                    )}
                </section>

                <section style={styles.documentsHeader}>
                    <div>
                        <h3 style={styles.sectionTitle}>Uploaded documents</h3>
                        <p style={styles.sectionText}>
                            Open a PDF to preview it or use chat to ask questions.
                        </p>
                    </div>
                </section>

                {documentsLoading ? (
                    <div style={styles.emptyCard}>
                        <div style={styles.spinner}></div>
                        <p>Loading documents...</p>
                    </div>
                ) : documents.length === 0 ? (
                    <div style={styles.emptyCard}>
                        <div style={styles.emptyIcon}>📄</div>
                        <h3 style={styles.emptyTitle}>No documents uploaded</h3>
                        <p style={styles.emptyText}>
                            Upload your first PDF to start asking document-based
                            questions.
                        </p>
                    </div>
                ) : (
                    <div style={styles.documentGrid}>
                        {documents.map((doc) => (
                            <div key={doc.id} style={styles.documentCard}>
                                <div style={styles.documentTop}>
                                    <div style={styles.documentIcon}>PDF</div>

                                    <span
                                        style={{
                                            ...styles.statusBadge,
                                            background:
                                                doc.status === "processed"
                                                    ? "#dcfce7"
                                                    : "#fef3c7",
                                            color:
                                                doc.status === "processed"
                                                    ? "#166534"
                                                    : "#92400e",
                                        }}
                                    >
                                        {doc.status || "uploaded"}
                                    </span>
                                </div>

                                <h3 style={styles.documentName}>
                                    {doc.file_name}
                                </h3>

                                <div style={styles.documentMeta}>
                                    <span>📄 {doc.page_count || "N/A"} pages</span>
                                    <span>•</span>
                                    <span>Private</span>
                                </div>

                                <button
                                    style={styles.openPdfButton}
                                    onClick={() => navigate(`/viewer/${doc.id}/1`)}
                                >
                                    Open PDF →
                                </button>
                            </div>
                        ))}
                    </div>
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
        fontFamily: "system-ui, Segoe UI, Roboto, sans-serif",
    },
    navbar: {
        height: "78px",
        background: "#ffffff",
        borderBottom: "1px solid #e2e8f0",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 48px",
        boxShadow: "0 2px 10px rgba(15, 23, 42, 0.04)",
    },
    brand: {
        display: "flex",
        alignItems: "center",
        gap: "14px",
    },
    logo: {
        width: "46px",
        height: "46px",
        borderRadius: "14px",
        background: "linear-gradient(135deg, #2563eb, #7c3aed)",
        color: "#ffffff",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: "800",
        fontSize: "22px",
    },
    brandTitle: {
        margin: 0,
        fontSize: "22px",
        fontWeight: "800",
        color: "#0f172a",
    },
    brandSubtitle: {
        margin: 0,
        color: "#64748b",
        fontSize: "13px",
    },
    navActions: {
        display: "flex",
        gap: "10px",
        alignItems: "center",
    },
    secondaryButton: {
        padding: "10px 16px",
        borderRadius: "10px",
        border: "1px solid #cbd5e1",
        background: "#ffffff",
        color: "#334155",
        fontWeight: "700",
        cursor: "pointer",
    },
    primaryButton: {
        padding: "10px 16px",
        borderRadius: "10px",
        border: "none",
        background: "#2563eb",
        color: "#ffffff",
        fontWeight: "800",
        cursor: "pointer",
    },
    logoutButton: {
        padding: "10px 16px",
        borderRadius: "10px",
        border: "1px solid #fecaca",
        background: "#fff1f2",
        color: "#dc2626",
        fontWeight: "700",
        cursor: "pointer",
    },
    main: {
        maxWidth: "1180px",
        margin: "0 auto",
        padding: "42px 28px 60px",
    },
    hero: {
        display: "flex",
        justifyContent: "space-between",
        gap: "24px",
        alignItems: "center",
        marginBottom: "28px",
    },
    eyebrow: {
        margin: "0 0 8px",
        color: "#2563eb",
        fontWeight: "800",
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        fontSize: "13px",
    },
    title: {
        margin: 0,
        color: "#0f172a",
        fontSize: "42px",
        lineHeight: 1.1,
        fontWeight: "850",
    },
    subtitle: {
        marginTop: "12px",
        maxWidth: "690px",
        color: "#64748b",
        fontSize: "17px",
        lineHeight: 1.6,
    },
    statsCard: {
        minWidth: "180px",
        background: "linear-gradient(135deg, #2563eb, #7c3aed)",
        color: "#ffffff",
        borderRadius: "22px",
        padding: "24px",
        boxShadow: "0 18px 35px rgba(37, 99, 235, 0.22)",
    },
    statsNumber: {
        margin: 0,
        fontSize: "42px",
        fontWeight: "850",
        lineHeight: 1,
    },
    statsLabel: {
        marginTop: "8px",
        opacity: 0.9,
        fontSize: "15px",
    },
    uploadCard: {
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "24px",
        padding: "26px",
        boxShadow: "0 18px 40px rgba(15, 23, 42, 0.06)",
        marginBottom: "30px",
    },
    sectionTitle: {
        margin: 0,
        color: "#0f172a",
        fontSize: "22px",
        fontWeight: "800",
    },
    sectionText: {
        marginTop: "6px",
        color: "#64748b",
        fontSize: "15px",
    },
    dropZone: {
        marginTop: "22px",
        border: "2px dashed #cbd5e1",
        borderRadius: "22px",
        padding: "44px 24px",
        textAlign: "center",
        cursor: "pointer",
        transition: "all 0.2s ease",
    },
    uploadIcon: {
        width: "64px",
        height: "64px",
        margin: "0 auto 16px",
        borderRadius: "20px",
        background: "#eff6ff",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "30px",
    },
    dropTitle: {
        margin: "0 0 8px",
        color: "#0f172a",
        fontSize: "22px",
        fontWeight: "800",
    },
    dropText: {
        margin: 0,
        color: "#64748b",
        fontSize: "15px",
    },
    uploadActions: {
        marginTop: "20px",
        display: "flex",
        justifyContent: "flex-end",
        gap: "12px",
    },
    clearButton: {
        padding: "12px 16px",
        borderRadius: "12px",
        border: "1px solid #cbd5e1",
        background: "#ffffff",
        color: "#334155",
        fontWeight: "700",
        cursor: "pointer",
    },
    uploadButton: {
        padding: "12px 18px",
        borderRadius: "12px",
        border: "none",
        background: "#2563eb",
        color: "#ffffff",
        fontWeight: "800",
        cursor: "pointer",
    },
    processingBox: {
        marginTop: "18px",
        background: "#eff6ff",
        border: "1px solid #bfdbfe",
        borderRadius: "16px",
        padding: "16px",
        display: "flex",
        gap: "14px",
        alignItems: "center",
        color: "#1e3a8a",
    },
    processingText: {
        marginTop: "4px",
        color: "#475569",
        fontSize: "14px",
    },
    documentsHeader: {
        marginBottom: "18px",
    },
    documentGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
        gap: "20px",
    },
    documentCard: {
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "22px",
        padding: "22px",
        boxShadow: "0 14px 32px rgba(15, 23, 42, 0.06)",
    },
    documentTop: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "18px",
    },
    documentIcon: {
        width: "52px",
        height: "52px",
        borderRadius: "16px",
        background: "#fee2e2",
        color: "#dc2626",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: "900",
        fontSize: "13px",
    },
    statusBadge: {
        padding: "6px 10px",
        borderRadius: "999px",
        fontSize: "13px",
        fontWeight: "800",
        textTransform: "capitalize",
    },
    documentName: {
        margin: "0 0 12px",
        color: "#0f172a",
        fontSize: "19px",
        fontWeight: "800",
        lineHeight: 1.35,
    },
    documentMeta: {
        display: "flex",
        gap: "8px",
        color: "#64748b",
        fontSize: "14px",
        marginBottom: "20px",
    },
    openPdfButton: {
        width: "100%",
        padding: "12px",
        borderRadius: "12px",
        border: "none",
        background: "#eff6ff",
        color: "#2563eb",
        fontWeight: "800",
        cursor: "pointer",
    },
    emptyCard: {
        minHeight: "260px",
        background: "#ffffff",
        border: "1px dashed #cbd5e1",
        borderRadius: "24px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "#64748b",
        gap: "10px",
    },
    emptyIcon: {
        fontSize: "44px",
    },
    emptyTitle: {
        margin: 0,
        color: "#0f172a",
        fontSize: "22px",
    },
    emptyText: {
        margin: 0,
        maxWidth: "420px",
        textAlign: "center",
        lineHeight: 1.5,
    },
    spinner: {
        width: "34px",
        height: "34px",
        border: "4px solid #dbeafe",
        borderTop: "4px solid #2563eb",
        borderRadius: "50%",
        animation: "spin 1s linear infinite",
    },
};

export default UploadPage;