import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function SignupPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    const handleSignup = async () => {
        try {
            setLoading(true);
            setErrorMessage("");
            setSuccessMessage("");

            if (!email || !password) {
                setErrorMessage("Please enter both email and password.");
                return;
            }

            const response = await api.post("/auth/signup", {
                email,
                password,
            });

            console.log(response.data);
            setSuccessMessage("Account created successfully. You can now log in.");
        } catch (error) {
            console.error(error);
            setErrorMessage(
                error.response?.data?.detail || "Signup failed. Please try again."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={styles.page}>
            <div style={styles.leftPanel}>
                <div style={styles.brandBox}>
                    <div style={styles.logo}>D</div>
                    <h1 style={styles.brandTitle}>DocAI</h1>
                    <p style={styles.brandSubtitle}>
                        Secure document assistant for private PDF question answering.
                    </p>
                </div>

                <div style={styles.featureList}>
                    <div style={styles.feature}>🔐 Private document access</div>
                    <div style={styles.feature}>📄 PDF citation support</div>
                    <div style={styles.feature}>✨ AI answers from your own files</div>
                </div>
            </div>

            <div style={styles.rightPanel}>
                <div style={styles.card}>
                    <h2 style={styles.title}>Create account</h2>
                    <p style={styles.subtitle}>
                        Start building your private document workspace.
                    </p>

                    {errorMessage && (
                        <div style={styles.errorBox}>{errorMessage}</div>
                    )}

                    {successMessage && (
                        <div style={styles.successBox}>{successMessage}</div>
                    )}

                    <label style={styles.label}>Email</label>
                    <input
                        style={styles.input}
                        type="email"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />

                    <label style={styles.label}>Password</label>
                    <input
                        style={styles.input}
                        type="password"
                        placeholder="Create a password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") handleSignup();
                        }}
                    />

                    <button
                        style={{
                            ...styles.signupButton,
                            opacity: loading ? 0.7 : 1,
                            cursor: loading ? "not-allowed" : "pointer",
                        }}
                        onClick={handleSignup}
                        disabled={loading}
                    >
                        {loading ? "Creating..." : "Create Account"}
                    </button>

                    <p style={styles.signupText}>
                        Already have an account?{" "}
                        <Link style={styles.link} to="/">
                            Login
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

const styles = {
    page: {
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        background: "#f4f7fb",
        fontFamily: "system-ui, Segoe UI, Roboto, sans-serif",
    },
    leftPanel: {
        background: "linear-gradient(135deg, #2563eb, #7c3aed)",
        color: "#ffffff",
        padding: "70px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
    },
    brandBox: {
        maxWidth: "520px",
    },
    logo: {
        width: "54px",
        height: "54px",
        borderRadius: "16px",
        background: "rgba(255,255,255,0.2)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "28px",
        fontWeight: "800",
        marginBottom: "20px",
    },
    brandTitle: {
        fontSize: "54px",
        margin: "0 0 16px",
        color: "#ffffff",
        fontWeight: "800",
    },
    brandSubtitle: {
        fontSize: "20px",
        lineHeight: "1.6",
        opacity: 0.92,
    },
    featureList: {
        display: "grid",
        gap: "14px",
    },
    feature: {
        padding: "14px 16px",
        borderRadius: "14px",
        background: "rgba(255,255,255,0.14)",
        backdropFilter: "blur(8px)",
        fontSize: "16px",
    },
    rightPanel: {
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px",
    },
    card: {
        width: "100%",
        maxWidth: "430px",
        background: "#ffffff",
        padding: "38px",
        borderRadius: "22px",
        boxShadow: "0 20px 45px rgba(15, 23, 42, 0.12)",
        textAlign: "left",
    },
    title: {
        margin: "0 0 8px",
        fontSize: "30px",
        fontWeight: "750",
        color: "#0f172a",
    },
    subtitle: {
        margin: "0 0 28px",
        color: "#64748b",
        fontSize: "15px",
        lineHeight: "1.5",
    },
    label: {
        display: "block",
        marginBottom: "8px",
        marginTop: "16px",
        fontSize: "14px",
        fontWeight: "650",
        color: "#334155",
    },
    input: {
        width: "100%",
        boxSizing: "border-box",
        padding: "13px 14px",
        borderRadius: "12px",
        border: "1px solid #cbd5e1",
        fontSize: "15px",
        outline: "none",
        color: "#0f172a",
        background: "#ffffff",
    },
    signupButton: {
        width: "100%",
        marginTop: "24px",
        padding: "14px",
        border: "none",
        borderRadius: "12px",
        background: "#2563eb",
        color: "#ffffff",
        fontSize: "16px",
        fontWeight: "700",
    },
    signupText: {
        marginTop: "22px",
        textAlign: "center",
        color: "#64748b",
        fontSize: "14px",
    },
    link: {
        color: "#2563eb",
        fontWeight: "700",
        textDecoration: "none",
    },
    errorBox: {
        background: "#fee2e2",
        color: "#991b1b",
        padding: "12px 14px",
        borderRadius: "12px",
        fontSize: "14px",
        marginBottom: "14px",
        border: "1px solid #fecaca",
    },
    successBox: {
        background: "#dcfce7",
        color: "#166534",
        padding: "12px 14px",
        borderRadius: "12px",
        fontSize: "14px",
        marginBottom: "14px",
        border: "1px solid #bbf7d0",
    },
};

export default SignupPage;