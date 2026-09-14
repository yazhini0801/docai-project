from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from supabase import create_client
from dotenv import load_dotenv
from services.document_parser import extract_pdf_text
from services.chunker import chunk_text
from services.embedding_service import generate_embedding
from io import BytesIO
import os
import tempfile


load_dotenv()

router = APIRouter()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)


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


@router.post("/upload")
async def upload_document(
    token: str = Form(...),
    folder_id: str = Form(...),
    file: UploadFile = File(...)
):
    user = get_current_user(token)

    file_bytes = await file.read()

    file_path = f"{user.id}/{folder_id}/{file.filename}"

    supabase.storage.from_("documents").upload(
        file_path,
        file_bytes
    )

    file_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/documents/{file_path}"

    status = "uploaded"
    extracted_text = None
    page_count = None
    parsed_pages = []
    chunks_saved = 0
    embeddings_saved = 0

    if file.content_type == "application/pdf":
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name

            parsed_result = extract_pdf_text(temp_file_path)

            extracted_text = parsed_result["full_text"]
            page_count = parsed_result["page_count"]
            parsed_pages = parsed_result["pages"]
            status = "processed"

            os.remove(temp_file_path)

        except Exception as e:
            status = "failed"
            extracted_text = f"PDF extraction failed: {str(e)}"

    result = supabase.table("documents").insert({
        "user_id": user.id,
        "folder_id": folder_id,
        "file_name": file.filename,
        "file_type": file.content_type,
        "file_url": file_url,
        "file_size": len(file_bytes),
        "status": status,
        "extracted_text": extracted_text,
        "page_count": page_count
    }).execute()

    if parsed_pages and status == "processed":
        document_id = result.data[0]["id"]

        chunk_rows = []
        global_chunk_index = 0

        for page in parsed_pages:
            page_number = page["page_number"]
            page_text = page["text"]

            if not page_text.strip():
                continue

            page_chunks = chunk_text(page_text)

            for chunk in page_chunks:
                chunk_rows.append({
                    "document_id": document_id,
                    "chunk_index": global_chunk_index,
                    "content": chunk["content"],
                    "page_number": page_number
                })

                global_chunk_index += 1

        if chunk_rows:
            chunk_result = supabase.table("document_chunks").insert(chunk_rows).execute()
            chunks_saved = len(chunk_rows)

            embedding_rows = []

            for saved_chunk in chunk_result.data:
                embedding = generate_embedding(saved_chunk["content"])

                embedding_rows.append({
                    "chunk_id": saved_chunk["id"],
                    "embedding": embedding
                })

            if embedding_rows:
                supabase.table("chunk_embeddings").insert(embedding_rows).execute()
                embeddings_saved = len(embedding_rows)

    return {
        "message": "File uploaded, processed, chunked, and embedded successfully",
        "document": result.data,
        "chunks_saved": chunks_saved,
        "embeddings_saved": embeddings_saved
    }


@router.get("/")
def list_documents(token: str, folder_id: str):
    user = get_current_user(token)

    result = supabase.table("documents") \
        .select("*") \
        .eq("user_id", user.id) \
        .eq("folder_id", folder_id) \
        .execute()

    return {
        "documents": result.data
    }


@router.get("/file/{document_id}")
def get_pdf_file(document_id: str, token: str):
    user = get_current_user(token)

    result = (
        supabase.table("documents")
        .select("id,file_name,file_url,user_id,file_type")
        .eq("id", document_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    document = result.data

    if document["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if document["file_type"] != "application/pdf":
        raise HTTPException(status_code=400, detail="File is not a PDF")

    marker = "/storage/v1/object/documents/"

    if marker not in document["file_url"]:
        raise HTTPException(status_code=500, detail="Invalid file URL")

    file_path = document["file_url"].split(marker)[1]

    try:
        file_bytes = supabase.storage.from_("documents").download(file_path)

        return StreamingResponse(
            BytesIO(file_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{document["file_name"]}"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load PDF file: {str(e)}"
        )


@router.get("/preview/{document_id}")
def preview_document(document_id: str, token: str):
    user = get_current_user(token)

    result = (
        supabase.table("documents")
        .select("id,file_name,file_url,page_count,user_id,status,file_type")
        .eq("id", document_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    document = result.data

    if document["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "document_id": document["id"],
        "file_name": document["file_name"],
        "file_url": document["file_url"],
        "page_count": document["page_count"],
        "status": document["status"],
        "file_type": document["file_type"]
    }


@router.get("/page/{document_id}/{page_number}")
def get_document_page(document_id: str, page_number: int, token: str):
    user = get_current_user(token)

    document_result = (
        supabase.table("documents")
        .select("id,file_name,user_id,page_count")
        .eq("id", document_id)
        .single()
        .execute()
    )

    if not document_result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    document = document_result.data

    if document["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    chunks_result = (
        supabase.table("document_chunks")
        .select("id,chunk_index,content,page_number")
        .eq("document_id", document_id)
        .eq("page_number", page_number)
        .order("chunk_index", desc=False)
        .execute()
    )

    return {
        "document_id": document["id"],
        "file_name": document["file_name"],
        "page_number": page_number,
        "page_count": document["page_count"],
        "chunks": chunks_result.data
    }


@router.get("/highlight/{document_id}")
def get_highlight(
    document_id: str,
    page_number: int,
    chunk_index: int,
    token: str
):
    user = get_current_user(token)

    document_result = (
        supabase.table("documents")
        .select("id,user_id,file_name")
        .eq("id", document_id)
        .single()
        .execute()
    )

    if not document_result.data:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    document = document_result.data

    if document["user_id"] != user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    chunk_result = (
        supabase.table("document_chunks")
        .select("*")
        .eq("document_id", document_id)
        .eq("page_number", page_number)
        .eq("chunk_index", chunk_index)
        .single()
        .execute()
    )

    if not chunk_result.data:
        raise HTTPException(
            status_code=404,
            detail="Chunk not found"
        )

    chunk = chunk_result.data

    return {
        "document_id": document_id,
        "file_name": document["file_name"],
        "page_number": page_number,
        "chunk_index": chunk_index,
        "highlight_text": chunk["content"]
    }