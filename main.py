from fastapi import FastAPI, UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="NotebookLM++ DEMO MODE")

# -------- MODELS --------
class AskReq(BaseModel):
    question: str
    source: Optional[str] = None

# -------- DEMO ENDPOINTS --------

@app.get("/")
async def root():
    return {"status": "DEMO MODE", "ai": "disabled"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    return {
        "status": "ok",
        "filename": file.filename,
        "note": "Demo modda dosya işlenmiyor"
    }

@app.post("/ask")
async def ask(req: AskReq):
    return {
        "answer": "DEMO CEVAP: Gerçek AI kapalı. OpenAI key eklenince gerçek cevap üretilecek.",
        "sources": []
    }

@app.get("/timeline")
async def timeline(topic: str = Query(...)):
    return [
        {"year": "1923", "event": f"{topic} ile ilgili DEMO olay", "page": 1},
        {"year": "1938", "event": "İkinci DEMO olay", "page": 2}
    ]

@app.get("/quiz")
async def quiz(topic: str = Query(...)):
    return {
        "quiz": [
            {
                "question": f"{topic} DEMO soru?",
                "options": ["A", "B", "C", "D"],
                "answer": "A"
            }
        ]
    }

@app.get("/kpss")
async def kpss(topic: str = Query(...)):
    return {
        "mode": "KPSS DEMO",
        "questions": [
            f"{topic} ile ilgili tuzaklı DEMO soru"
        ]
    }

