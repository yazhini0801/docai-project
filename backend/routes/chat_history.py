from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client
from dotenv import load_dotenv
import os

from routes.documents import get_current_user


load_dotenv()

router = APIRouter()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)


class CreateSessionRequest(BaseModel):
    token: str
    title: str


class SaveMessageRequest(BaseModel):
    session_id: str
    role: str
    message: str
    citations: list = []


class SessionListRequest(BaseModel):
    token: str


class SessionMessagesRequest(BaseModel):
    session_id: str


@router.post("/sessions")
def create_chat_session(request: CreateSessionRequest):
    try:
        user = get_current_user(request.token)

        result = supabase.table("chat_sessions").insert({
            "user_id": user.id,
            "title": request.title
        }).execute()

        return {
            "message": "Chat session created successfully",
            "session": result.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages")
def save_message(request: SaveMessageRequest):
    try:
        result = supabase.table("chat_messages").insert({
            "session_id": request.session_id,
            "role": request.role,
            "message": request.message,
            "citations": request.citations
        }).execute()

        return {
            "message": "Chat message saved successfully",
            "chat_message": result.data[0]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/list")
def list_chat_sessions(request: SessionListRequest):
    try:
        user = get_current_user(request.token)

        result = (
            supabase.table("chat_sessions")
            .select("*")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
        )

        return {
            "sessions": result.data
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/session/messages")
def get_session_messages(request: SessionMessagesRequest):
    try:
        result = (
            supabase.table("chat_messages")
            .select("*")
            .eq("session_id", request.session_id)
            .order("created_at", desc=False)
            .execute()
        )

        return {
            "messages": result.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))