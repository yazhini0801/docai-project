import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { supabase } from "../services/supabase";


function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const [resetLoading, setResetLoading] = useState(false);


    const handleLogin = async () => {
        try {
            setLoading(true);
            setErrorMessage("");
            setSuccessMessage("");


            if (!email || !password) {
                setErrorMessage("Please enter both email and password.");
                return;
            }


            const response = await api.post("/auth/login", {
                email,
                password,
            });


            localStorage.setItem("token", response.data.access_token);
            window.location.href = "/dashboard";
        } catch (error) {
            console.error("Login Error:", error);

            setErrorMessage(
                error.response?.data?.detail ||
                    "Login failed. Please check your email and password."
            );
        } finally {
            setLoading(false);
        }
    };


    const handleForgotPassword = async () => {
        if (!email.trim()) {
            setErrorMessage("Please enter your email first.");
            setSuccessMessage("");
            return;
        }


        try {
            setResetLoading(true);
            setErrorMessage("");
            setSuccessMessage("");


            const { error } = await supabase.auth.resetPasswordForEmail(email, {
                redirectTo: "http://localhost:5173/reset-password",
            });


            if (error) {
                throw error;
            }


            setSuccessMessage(
                "Password reset email sent. Please check your inbox."
            );
        } catch (error) {
            console.error("Password Reset Error:", error);

            setErrorMessage(
                error.message || "Failed to send password reset email."
            );
        } finally {
            setResetLoading(false);
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
                    <div style={styles.feature}>
                        🔐 Private document access
                    </div>

                    <div style={styles.feature}>
                        📄 PDF citation support
                    </div>

                    <div style={styles.feature}>
                        ✨ AI answers from your own files
                    </div>
                </div>
            </div>


            <div style={styles.rightPanel}>
                <div style={styles.card}>
                    <h2 style={styles.title}>
                        Welcome back
                    </h2>


                    <p style={styles.subtitle}>
                        Login to continue to your document workspace.
                    </p>


                    {errorMessage && (
                        <div style={styles.errorBox}>
                            {errorMessage}
                        </div>
                    )}


                    {successMessage && (
                        <div style={styles.successBox}>
                            {successMessage}
                        </div>
                    )}


                    <label style={styles.label}>
                        Email
                    </label>


                    <input
                        style={styles.input}
                        type="email"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />


                    <label style={styles.label}>
                        Password
                    </label>


                    <input
                        style={styles.input}
                        type="password"
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                handleLogin();
                            }
                        }}
                    />


                    <div style={styles.forgotContainer}>
                        <button
                            type="button"
                            onClick={handleForgotPassword}
                            disabled={resetLoading}
                            style={styles.forgotButton}
                        >
                            {resetLoading
                                ? "Sending..."
                                : "Forgot Password?"}
                        </button>
                    </div>


                    <button
                        style={{
                            ...styles.loginButton,
                            opacity: loading ? 0.7 : 1,
                            cursor: loading
                                ? "not-allowed"
                                : "pointer",
                        }}
                        onClick={handleLogin}
                        disabled={loading}
                    >
                        {loading
                            ? "Logging in..."
                            : "Login"}
                    </button>


                    <p style={styles.signupText}>
                        Don't have an account?{" "}
                        <Link
                            style={styles.link}
                            to="/signup"
                        >
                            Sign Up
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

    forgotContainer: {
        marginTop: "10px",
        textAlign: "right",
    },

    forgotButton: {
        border: "none",
        background: "transparent",
        color: "#2563eb",
        fontSize: "14px",
        fontWeight: "700",
        cursor: "pointer",
        padding: 0,
    },

    loginButton: {
        width: "100%",
        marginTop: "20px",
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


export default LoginPage;