# api/chat.py 
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from agent.scheduling_agent import SchedulingAgent

router = APIRouter()
agent = SchedulingAgent()

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

@router.post("/chat")
def chat(req: ChatRequest):
    try:
        resp = agent.handle_message(req.session_id, req.message)
        return resp
    except Exception as e:
        # avoid leaking sensitive internals but return message for debugging in dev
        raise HTTPException(status_code=500, detail=str(e))
