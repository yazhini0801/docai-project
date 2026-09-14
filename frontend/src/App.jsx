import {
    BrowserRouter,
    Routes,
    Route
} from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import ChatPage from "./pages/ChatPage";
import PDFViewerPage from "./pages/PDFViewerPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";


function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<LoginPage />} />
                <Route path="/signup" element={<SignupPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />

                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/upload/:folderId" element={<UploadPage />} />
                <Route path="/chat/:folderId" element={<ChatPage />} />

                <Route
                    path="/viewer/:documentId/:pageNumber?"
                    element={<PDFViewerPage />}
                />
            </Routes>
        </BrowserRouter>
    );
}


export default App;