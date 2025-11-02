from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Depends
from pydantic import BaseModel
import tempfile
import os
from models.pdf_processor import extract_text_from_pdf
from agents.pdf_chain import create_pdf_chain
import logging
from typing import List
import json

#configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PDF Agent API")

vectorstore_cache = {}

AGENT_API_KEY = os.getenv("AGENT_API_KEY")

if not AGENT_API_KEY:
    raise ValueError("AGENT_API_KEY not set in environment variables")


class Message(BaseModel):
    role: str 
    content: str


async def verify_api_key(x_api_key: str = Header(...)):
    """Verify that the request has a valid API key."""
    if x_api_key != AGENT_API_KEY:
        logger.warning(f"Unauthorized access attempt with invalid API key")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True


def format_history_for_context(messages: List[Message]) -> str:
    """Convert message list to text context for the LLM."""
    if not messages:
        return ""
    
    lines = []
    for msg in messages:
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    
    return "\n".join(lines)


@app.post("/index_pdf")
async def index_pdf(
    file_id: str = Form(...),
    file: UploadFile = File(...),
    _: bool = Depends(verify_api_key)
):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        #check if already indexed
        if file_id in vectorstore_cache:
            logger.info(f"File already indexed: {file_id}")
            return {
                "file_id": file_id,
                "file_name": file.filename,
                "already_indexed": True
            }
        
        #extract text and index
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            text = extract_text_from_pdf(tmp_path)
            if not text:
                raise HTTPException(status_code=400, detail="Could not extract text from PDF")

            #cache by file_id
            vectorstore_cache[file_id] = {
                'text': text,
                'file_name': file.filename,
                'text_length': len(text)
            }
            
            logger.info(f"Indexed {file.filename} (file_id: {file_id}) - {len(text)} chars")
            
            return {
                "file_id": file_id,
                "file_name": file.filename,
                "text_length": len(text),
                "already_indexed": False
            }
        
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"Error indexing PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query(
    file_id: str = Form(...),
    query: str = Form(...),
    chat_history: str = Form("[]"),
    _: bool = Depends(verify_api_key)
):
    try:
        if file_id not in vectorstore_cache:
            raise HTTPException(
                status_code=404,
                detail="File not indexed. Call /index_pdf first."
            )
        
        try:
            history_data = json.loads(chat_history)
            messages = [Message(**msg) for msg in history_data]
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid chat_history: {e}")

        cached = vectorstore_cache[file_id]
        chain = create_pdf_chain(cached['text'])

        if messages:
            history_text = format_history_for_context(messages)
            full_query = f"Previous conversation:\n{history_text}\n\nCurrent question: {query}"
        else:
            full_query = query

        result = await chain.ainvoke({"input": full_query})
        response = result.get("answer", "No answer found.")
        
        logger.info(f"Query processed for file_id: {file_id}")
        
        return {
            "response": response
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/{file_id}")
async def delete_from_cache(
    file_id: str,
    _: bool = Depends(verify_api_key)
):

    if file_id in vectorstore_cache:
        file_name = vectorstore_cache[file_id]["file_name"]
        del vectorstore_cache[file_id]
        logger.info(f"Removed file_id {file_id} ({file_name}) from cache")
        return {"message": f"Removed {file_name} from cache"}
    else:
        raise HTTPException(status_code=404, detail="File not found in cache")


@app.get("/health")
async def health_check():
    """Public health check endpoint (no auth required)."""
    return {
        "status": "healthy",
        "indexed_files": len(vectorstore_cache)
    }


@app.get("/cache_stats")
async def cache_stats(_: bool = Depends(verify_api_key)):
    return {
        "indexed_files": len(vectorstore_cache),
        "files": [
            {
                "file_id": file_id,
                "name": info["file_name"],
                "text_length": info["text_length"]
            }
            for file_id, info in vectorstore_cache.items()
        ]
    }


@app.post("/clear_cache")
async def clear_cache(_: bool = Depends(verify_api_key)):
    count = len(vectorstore_cache)
    vectorstore_cache.clear()
    logger.info(f"Cleared {count} files from cache")
    return {"message": f"Cleared {count} files from cache"}


@app.get("/")
async def read_root():
    return {
        "service": "PDF Agent API",
        "version": "1.0",
        "description": "Protected PDF question-answering service",
        "note": "All endpoints except /health and / require X-API-Key header",
        "endpoints": {
            "public": {
                "health": "GET /health",
                "root": "GET /"
            },
            "protected": {
                "index": "POST /index_pdf (requires X-API-Key)",
                "query": "POST /query (requires X-API-Key)",
                "delete": "DELETE /cache/{file_id} (requires X-API-Key)",
                "stats": "GET /cache_stats (requires X-API-Key)",
                "clear": "POST /clear_cache (requires X-API-Key)"
            }
        }
    }