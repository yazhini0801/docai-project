from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

class FolderRequest(BaseModel):
    name: str

def get_current_user(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        token = token.replace("Bearer ", "").strip()
        user_response = supabase.auth.get_user(token)

        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid user")

        return user_response.user

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

@router.post("/create")
def create_folder(data: FolderRequest, token: str):
    user = get_current_user(token)

    result = supabase.table("folders").insert({
        "user_id": user.id,
        "name": data.name
    }).execute()

    return {
        "message": "Folder created successfully",
        "folder": result.data
    }

@router.get("/")
def list_folders(token: str):
    user = get_current_user(token)

    result = supabase.table("folders").select("*").eq("user_id", user.id).execute()

    return {
        "folders": result.data
    }

@router.delete("/{folder_id}")
def delete_folder(folder_id: str, token: str):
    user = get_current_user(token)

    result = supabase.table("folders").delete().eq("id", folder_id).eq("user_id", user.id).execute()

    return {
        "message": "Folder deleted successfully",
        "deleted": result.data
    }