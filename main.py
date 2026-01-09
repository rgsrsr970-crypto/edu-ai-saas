from fastapi import FastAPI, UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional
import os, uuid, fitz

from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from openai import OpenAI

# ---------------- CONFIG ----------------
app = FastAPI(title="NotebookLM++ MVP")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

qdrant = QdrantClient(path="./qdrant_db")
COLLECTION = "docs"

qdrant.recreate_collection(
    collection_name=COLLECTION,
    vectors_config={"size": 3072, "distance": "Cosine"}
)

# ---------------- UTILS ----------------
def embed(text: str):
    return client.embeddings.create(
        model="text-embedding-3-large",
        input=text[:3000]
    ).data[0].embedding

def extract_pdf(path):
    doc = fitz.open(path)
    for i, page in enumerate(doc):
        txt = page.get_text()
        if txt.strip():
            yield i + 1, txt

# ---------------- MODELS ----------------
class AskReq(BaseModel):
    question: str
    source: Optional[str] = None

# ---------------- API ----------------

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    path = f"uploads/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    points = []
    for page, text in extract_pdf(path):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=embed(text),
            payload={
                "text": text,
                "page": page,
                "source": file.filename
            }
        ))

    qdrant.upsert(COLLECTION, points)
    return {"status": "ok", "pages": len(points)}

@app.post("/ask")
async def ask(req: AskReq):
    hits = qdrant.search(
        COLLECTION,
        query_vector=embed(req.question),
        limit=5,
        with_payload=True
    )

    context = "\n".join(
        f"{h.payload['source']} s.{h.payload['page']}: {h.payload['text']}"
        for h in hits
    )

    prompt = f"""
Sadece aşağıdaki kaynaklara dayanarak cevap ver.
Bilgi yoksa açıkça söyle.

Kaynaklar:
{context}

Soru: {req.question}
"""

    res = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    )

    return {
        "answer": res.choices[0].message.content,
        "sources": [h.payload for h in hits]
    }

@app.get("/timeline")
async def timeline(topic: str = Query(...)):
    hits = qdrant.search(
        COLLECTION,
        query_vector=embed(topic),
        limit=8,
        with_payload=True
    )

    context = "\n".join(h.payload["text"] for h in hits)

    prompt = f"""
Aşağıdaki metinlerden kronolojik bir timeline çıkar.
JSON array olarak dön.
Alanlar: year, event, page

Metinler:
{context}
"""

    res = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

    return res.choices[0].message.content

@app.get("/quiz")
async def quiz(topic: str = Query(...)):
    prompt = f"""
{topic} konusu için 5 soruluk çoktan seçmeli quiz hazırla.
Her soruda 4 şık ve doğru cevap olsun.
"""

    res = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return res.choices[0].message.content

@app.get("/kpss")
async def kpss(topic: str = Query(...)):
    prompt = f"""
KPSS tarzında, zor ve tuzaklı 5 soru hazırla.
En sona cevap anahtarı ekle.
Konu: {topic}
"""

    res = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    return res.choices[0].message.content
