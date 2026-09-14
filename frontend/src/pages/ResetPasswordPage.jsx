import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../services/supabase";


function ResetPasswordPage() {
    const navigate = useNavigate();

    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");


    const handleResetPassword = async () => {
        try {
            setErrorMessage("");
            setSuccessMessage("");


            if (!password || !confirmPassword) {
                setErrorMessage("Please enter and confirm your new password.");
                return;
            }


            if (password !== confirmPassword) {
                setErrorMessage("Passwords do not match.");
                return;
            }


            if (password.length < 6) {
                setErrorMessage("Password must be at least 6 characters.");
                return;
            }


            setLoading(true);


            const { error } = await supabase.auth.updateUser({
                password,
            });


            if (error) {
                throw error;
            }


            setSuccessMessage("Password updated successfully.");


            setTimeout(() => {
                navigate("/");
            }, 1500);

        } catch (error) {
            console.error("Reset Password Error:", error);

            setErrorMessage(
                error.message || "Failed to update password."
            );
        } finally {
            setLoading(false);
        }
    };


    return (
        <div style={styles.page}>
            <div style={styles.card}>
                <div style={styles.logo}>D</div>

                <h2 style={styles.title}>Reset your password</h2>

                <p style={styles.subtitle}>
                    Enter a new password for your DocAI account.
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
                    New Password
                </label>

                <input
                    type="password"
                    placeholder="Enter new password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={styles.input}
                />


                <label style={styles.label}>
                    Confirm Password
                </label>

                <input
                    type="password"
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={styles.input}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") {
                            handleResetPassword();
                        }
                    }}
                />


                <button
                    onClick={handleResetPassword}
                    disabled={loading}
                    style={{
                        ...styles.button,
                        opacity: loading ? 0.7 : 1,
                        cursor: loading ? "not-allowed" : "pointer",
                    }}
                >
                    {loading ? "Updating..." : "Update Password"}
                </button>


                <button
                    onClick={() => navigate("/")}
                    style={styles.backButton}
                >
                    Back to Login
                </button>
            </div>
        </div>
    );
}


const styles = {
    page: {
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f4f7fb",
        fontFamily: "system-ui, Segoe UI, Roboto, sans-serif",
        padding: "24px",
    },

    card: {
        width: "100%",
        maxWidth: "430px",
        background: "#ffffff",
        padding: "38px",
        borderRadius: "22px",
        boxShadow: "0 20px 45px rgba(15, 23, 42, 0.12)",
    },

    logo: {
        width: "52px",
        height: "52px",
        borderRadius: "16px",
        background: "linear-gradient(135deg, #2563eb, #7c3aed)",
        color: "#ffffff",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: "800",
        fontSize: "24px",
        marginBottom: "22px",
    },

    title: {
        margin: "0 0 8px",
        fontSize: "30px",
        fontWeight: "750",
        color: "#0f172a",
    },

    subtitle: {
        margin: "0 0 26px",
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

    button: {
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

    backButton: {
        width: "100%",
        marginTop: "12px",
        padding: "12px",
        borderRadius: "12px",
        border: "1px solid #cbd5e1",
        background: "#ffffff",
        color: "#334155",
        fontWeight: "700",
        cursor: "pointer",
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


export default ResetPasswordPage;