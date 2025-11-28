from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from api.chat import router as chat_router
from api.calendly_integration import router as calendly_router

app = FastAPI(title="Appointment Scheduling Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
# Calendly endpoints live under /api/calendly/*
app.include_router(calendly_router, prefix="/api/calendly")

@app.get("/")
def index():
    return {"status": "ok", "service": "appointment-scheduling-agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("BACKEND_PORT", 8000)), reload=True)
