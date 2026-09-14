import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function DashboardPage() {
    const [folders, setFolders] = useState([]);
    const [folderName, setFolderName] = useState("");
    const [searchTerm, setSearchTerm] = useState("");
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const navigate = useNavigate();

    const token = localStorage.getItem("token");

    const fetchFolders = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/folders/?token=${token}`);
            setFolders(response.data.folders || []);
        } catch (error) {
            console.error(error);
            alert("Failed to load folders");
        } finally {
            setLoading(false);
        }
    };

    const createFolder = async () => {
        if (!folderName.trim()) {
            alert("Enter folder name");
            return;
        }

        try {
            setCreating(true);

            await api.post(`/folders/create?token=${token}`, {
                name: folderName,
            });

            setFolderName("");
            fetchFolders();
        } catch (error) {
            console.error(error);
            alert("Failed to create folder");
        } finally {
            setCreating(false);
        }
    };

    const deleteFolder = async (folderId) => {
        const confirmDelete = window.confirm(
            "Are you sure you want to delete this folder?"
        );

        if (!confirmDelete) return;

        try {
            await api.delete(`/folders/${folderId}?token=${token}`);
            fetchFolders();
        } catch (error) {
            console.error(error);
            alert("Failed to delete folder");
        }
    };

    const openFolder = (folder) => {
        localStorage.setItem("selectedFolderName", folder.name);
        navigate(`/upload/${folder.id}`);
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

        fetchFolders();
    }, []);

    const filteredFolders = folders.filter((folder) =>
        folder.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div style={styles.page}>
            <header style={styles.navbar}>
                <div style={styles.brand}>
                    <div style={styles.logo}>D</div>
                    <div>
                        <h2 style={styles.brandTitle}>DocAI</h2>
                        <p style={styles.brandSubtitle}>Secure Document Assistant</p>
                    </div>
                </div>

                <button style={styles.logoutButton} onClick={logout}>
                    Logout
                </button>
            </header>

            <main style={styles.main}>
                <section style={styles.hero}>
                    <div>
                        <p style={styles.eyebrow}>Workspace</p>
                        <h1 style={styles.title}>Welcome back 👋</h1>
                        <p style={styles.subtitle}>
                            Manage your folders, upload PDFs, and ask questions from
                            your private documents.
                        </p>
                    </div>

                    <div style={styles.statsCard}>
                        <p style={styles.statsNumber}>{folders.length}</p>
                        <p style={styles.statsLabel}>Total folders</p>
                    </div>
                </section>

                <section style={styles.actionCard}>
                    <div style={styles.createBox}>
                        <div>
                            <h3 style={styles.sectionTitle}>Create new folder</h3>
                            <p style={styles.sectionText}>
                                Organize your PDFs by subject, project, or topic.
                            </p>
                        </div>

                        <div style={styles.createControls}>
                            <input
                                style={styles.input}
                                type="text"
                                placeholder="Folder name"
                                value={folderName}
                                onChange={(e) => setFolderName(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") createFolder();
                                }}
                            />

                            <button
                                style={styles.primaryButton}
                                onClick={createFolder}
                                disabled={creating}
                            >
                                {creating ? "Creating..." : "+ New Folder"}
                            </button>
                        </div>
                    </div>
                </section>

                <section style={styles.toolbar}>
                    <div>
                        <h3 style={styles.sectionTitle}>Your folders</h3>
                        <p style={styles.sectionText}>
                            Open a folder to upload documents and start chatting.
                        </p>
                    </div>

                    <input
                        style={styles.searchInput}
                        type="text"
                        placeholder="Search folders..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </section>

                {loading ? (
                    <div style={styles.emptyCard}>
                        <div style={styles.spinner}></div>
                        <p>Loading folders...</p>
                    </div>
                ) : filteredFolders.length === 0 ? (
                    <div style={styles.emptyCard}>
                        <div style={styles.emptyIcon}>📁</div>
                        <h3 style={styles.emptyTitle}>No folders found</h3>
                        <p style={styles.emptyText}>
                            Create your first folder to start uploading PDF documents.
                        </p>
                    </div>
                ) : (
                    <div style={styles.folderGrid}>
                        {filteredFolders.map((folder) => (
                            <div
                                key={folder.id}
                                style={styles.folderCard}
                                onClick={() => openFolder(folder)}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.transform =
                                        "translateY(-4px)";
                                    e.currentTarget.style.boxShadow =
                                        "0 20px 42px rgba(15, 23, 42, 0.12)";
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.transform =
                                        "translateY(0)";
                                    e.currentTarget.style.boxShadow =
                                        "0 14px 32px rgba(15, 23, 42, 0.06)";
                                }}
                            >
                                <div style={styles.folderTop}>
                                    <div style={styles.folderIcon}>📁</div>

                                    <button
                                        style={styles.deleteButton}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            deleteFolder(folder.id);
                                        }}
                                        title="Delete folder"
                                    >
                                        ✕
                                    </button>
                                </div>

                                <h3 style={styles.folderName}>{folder.name}</h3>

                                <div style={styles.folderDetails}>
                                    <span style={styles.badge}>Workspace</span>
                                    <span style={styles.dot}>•</span>
                                    <span>Private</span>
                                </div>

                                <p style={styles.folderMeta}>
                                    Open this folder to upload PDFs, view documents,
                                    and chat with your sources.
                                </p>

                                <button
                                    style={styles.openButton}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        openFolder(folder);
                                    }}
                                >
                                    Open Folder →
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
    logoutButton: {
        padding: "10px 16px",
        borderRadius: "10px",
        border: "1px solid #cbd5e1",
        background: "#ffffff",
        color: "#334155",
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
        maxWidth: "650px",
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
    actionCard: {
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "24px",
        padding: "24px",
        marginBottom: "26px",
        boxShadow: "0 18px 40px rgba(15, 23, 42, 0.06)",
    },
    createBox: {
        display: "flex",
        justifyContent: "space-between",
        gap: "24px",
        alignItems: "center",
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
    createControls: {
        display: "flex",
        gap: "12px",
        minWidth: "480px",
    },
    input: {
        flex: 1,
        padding: "13px 14px",
        borderRadius: "12px",
        border: "1px solid #cbd5e1",
        fontSize: "15px",
        outline: "none",
        background: "#ffffff",
        color: "#0f172a",
    },
    primaryButton: {
        padding: "13px 18px",
        borderRadius: "12px",
        border: "none",
        background: "#2563eb",
        color: "#ffffff",
        fontWeight: "800",
        cursor: "pointer",
        whiteSpace: "nowrap",
    },
    toolbar: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "18px",
        marginBottom: "20px",
    },
    searchInput: {
        width: "320px",
        padding: "13px 14px",
        borderRadius: "12px",
        border: "1px solid #cbd5e1",
        fontSize: "15px",
        outline: "none",
        background: "#ffffff",
        color: "#0f172a",
    },
    folderGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
        gap: "22px",
    },
    folderCard: {
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "22px",
        padding: "22px",
        boxShadow: "0 14px 32px rgba(15, 23, 42, 0.06)",
        transition: "all 0.2s ease",
        cursor: "pointer",
    },
    folderTop: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "18px",
    },
    folderIcon: {
        width: "52px",
        height: "52px",
        borderRadius: "16px",
        background: "#eff6ff",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "26px",
    },
    deleteButton: {
        width: "34px",
        height: "34px",
        borderRadius: "10px",
        border: "1px solid #fecaca",
        background: "#fff1f2",
        color: "#dc2626",
        cursor: "pointer",
        fontWeight: "800",
    },
    folderName: {
        margin: "0 0 10px",
        color: "#0f172a",
        fontSize: "21px",
        fontWeight: "800",
    },
    folderDetails: {
        display: "flex",
        alignItems: "center",
        gap: "8px",
        color: "#64748b",
        fontSize: "13px",
        marginBottom: "12px",
    },
    badge: {
        background: "#eff6ff",
        color: "#2563eb",
        padding: "5px 9px",
        borderRadius: "999px",
        fontWeight: "700",
    },
    dot: {
        color: "#94a3b8",
    },
    folderMeta: {
        margin: 0,
        color: "#64748b",
        fontSize: "14px",
        lineHeight: 1.55,
        minHeight: "66px",
    },
    openButton: {
        width: "100%",
        marginTop: "20px",
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
        width: "38px",
        height: "38px",
        border: "4px solid #dbeafe",
        borderTop: "4px solid #2563eb",
        borderRadius: "50%",
        animation: "spin 1s linear infinite",
    },
};

export default DashboardPage;