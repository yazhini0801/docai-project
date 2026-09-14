from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="DocAI Backend")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Routes
from auth import router as auth_router
app.include_router(auth_router, prefix="/auth")

# Folder Routes
from routes.folders import router as folders_router
app.include_router(
    folders_router,
    prefix="/folders",
    tags=["Folders"]
)

# Document Routes
from routes.documents import router as documents_router
app.include_router(
    documents_router,
    prefix="/documents",
    tags=["Documents"]
)

# Chat / RAG Routes
from routes.chat import router as chat_router
app.include_router(
    chat_router,
    prefix="/chat",
    tags=["Chat"]
)

# Chat History Routes
from routes.chat_history import router as chat_history_router
app.include_router(
    chat_history_router,
    prefix="/chat-history",
    tags=["Chat History"]
)

@app.get("/")
def root():
    return {"message": "DocAI Backend is running!"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "supabase": os.getenv("SUPABASE_URL"),
        "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "missing"
    }