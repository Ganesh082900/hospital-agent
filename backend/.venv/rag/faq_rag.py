# backend/.venv/rag/faq_rag.py
import os
import json
from typing import List, Optional

# Use the langchain-chroma wrapper and OpenAI embeddings when available.
from langchain_chroma import Chroma

# if langchain-core Document import path differs, use a safe fallback to simple strings
try:
    from langchain_core.documents import Document
except Exception:
    # Create a tiny Document shim with same attributes for compatibility
    class Document:
        def __init__(self, page_content: str, metadata: dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "clinic_info.json")
PERSIST_DIR = os.getenv("VECTOR_DB_PERSIST_DIR", "./data/vectordb")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

def _load_documents() -> List[Document]:
    try:
        with open(DATA_PATH, "r") as f:
            docs_json = json.load(f)
    except Exception:
        docs_json = []

    documents = []
    for item in docs_json:
        title = item.get("title", "")
        body = item.get("text", "")
        text = f"{title}\n\n{body}".strip()
        documents.append(Document(page_content=text, metadata={"title": title}))
    return documents

class FAQRAG:
    def __init__(self):
        self.documents = _load_documents()

        # If OpenAI key is available, attempt to use OpenAIEmbeddings + Chroma
        if OPENAI_API_KEY:
            try:
                from langchain_openai import OpenAIEmbeddings
                emb = OpenAIEmbeddings()
                # Chroma.from_documents expects Document objects
                self.db = Chroma.from_documents(self.documents, embedding=emb, persist_directory=PERSIST_DIR)
                self.use_db = True
                return
            except Exception as e:
                # If embeddings fail, fallback to local simple search
                print("OpenAI embeddings failed or not configured correctly:", e)

        # Fallback: don't attempt to import other embedding libraries (per requirements).
        # Use a simple keyword/substring ranking over the JSON FAQ texts.
        self.db = None
        self.use_db = False
        # Precompute plain texts for substring search
        self.plain_texts = [d.page_content for d in self.documents]

    def query(self, q: str, top_k: int = 2) -> str:
        """
        If vector DB available, use similarity_search.
        Otherwise, do a simple keyword match / substring ranking fallback.
        """
        if self.use_db and self.db is not None:
            try:
                res = self.db.similarity_search(q, k=top_k)
                out = []
                for r in res:
                    if hasattr(r, "page_content"):
                        out.append(r.page_content)
                    else:
                        out.append(str(r))
                return "\n\n".join(out) if out else "Sorry — I couldn't find an answer in the FAQ."
            except Exception as e:
                # fallback to simple search if DB call fails
                print("RAG DB query failed:", e)

        # Simple substring/keyword scoring
        q_lower = q.lower()
        scored = []
        for txt in self.plain_texts:
            score = 0
            tl = txt.lower()
            # match occurrence of words
            for token in q_lower.split():
                if token and token in tl:
                    score += 1
            # also boost by any exact phrase
            if q_lower in tl:
                score += 2
            if score > 0:
                scored.append((score, txt))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return "Sorry — I couldn't find an answer in the FAQ."
        top_texts = [t for _, t in scored[:top_k]]
        return "\n\n".join(top_texts)
