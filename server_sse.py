"""
Localmind v2 — Ana Sunucu (FastAPI + SSE + StaticFiles)
Tüm API rotaları burada tanımlanır, MemoryManager üzerinden çalışır.
"""
import sys, os, asyncio, json, logging
from datetime import datetime
from contextlib import asynccontextmanager

sys.path.insert(0, "/home/xmrah/Projects/localmind")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

# LD_LIBRARY_PATH ChromaDB için gerekli
import ctypes
for lib in ["libstdc++.so.6", "libz.so.1"]:
    try: ctypes.CDLL(lib)
    except Exception: pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("localmind.server")

# ─────────────────────────────────────────────────────────
# STARTUP / SHUTDOWN
# ─────────────────────────────────────────────────────────

manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global manager
    from core.memory_manager import MemoryManager
    manager = MemoryManager()
    log.info(f"🧠 Localmind v2 başladı — {manager.collection.count()} anı yüklü")
    yield
    log.info("Localmind kapatılıyor...")

app = FastAPI(title="Localmind v2", version="2.0.0", lifespan=lifespan)

# ─────────────────────────────────────────────────────────
# REQUEST MODELLERİ
# ─────────────────────────────────────────────────────────

class AddMemoryRequest(BaseModel):
    konu: str
    bilgi: str
    oda: Optional[str] = None
    agent_id: str = "user"
    importance: float = 7.0

class ArchiveRequest(BaseModel):
    memory_id: str

# ─────────────────────────────────────────────────────────
# API ROTALARI
# ─────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    from core.intelligence import is_ollama_available
    ollama_ok = await is_ollama_available()
    return {
        "status": "ok",
        "version": "2.0.0",
        "memories": manager.collection.count() if manager else 0,
        "ollama": ollama_ok,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/stats")
async def stats():
    if not manager:
        raise HTTPException(503, "MemoryManager başlatılmadı")
    return manager.get_stats()

@app.get("/api/rooms")
async def rooms():
    if not manager:
        raise HTTPException(503)
    s = manager.get_stats()
    result = [
        {"name": k, "count": v}
        for k, v in s.items()
        if k != "total" and isinstance(v, int)
    ]
    result.sort(key=lambda x: x["count"], reverse=True)
    return result

@app.get("/api/room/{oda}")
async def room_detail(oda: str):
    if not manager:
        raise HTTPException(503)
    memories = manager.get_room_memories(oda)
    return [
        {"id": m.id, "konu": m.konu, "content": m.bilgi, "oda": m.oda,
         "importance": m.importance, "tags": m.tags, "created_at": m.created_at}
        for m in memories
    ]

@app.get("/api/graph")
async def graph():
    if not manager:
        raise HTTPException(503)
    return manager.get_graph_data()

@app.get("/api/search")
async def search(q: str = Query(..., min_length=1), oda: Optional[str] = None, n: int = 5):
    if not manager:
        raise HTTPException(503)
    return manager.search(q, n=n, oda=oda)

@app.post("/api/memory")
async def add_memory(req: AddMemoryRequest):
    """Akıllı hafıza ekleme — Ollama ile otomatik sınıflandırma ve upsert."""
    if not manager:
        raise HTTPException(503)
    result = await manager.add_memory(
        konu=req.konu,
        bilgi=req.bilgi,
        oda=req.oda,
        agent_id=req.agent_id,
        importance=req.importance
    )
    return result

@app.post("/api/memory/archive")
async def archive_memory(req: ArchiveRequest):
    if not manager:
        raise HTTPException(503)
    ok = manager.archive_memory(req.memory_id)
    if not ok:
        raise HTTPException(404, "Anı bulunamadı")
    return {"status": "archived"}

@app.get("/api/profile")
async def profile():
    """Kullanıcı profili — tüm anılardan çıkarılır."""
    if not manager:
        raise HTTPException(503)
    return manager.get_user_profile()

# ─────────────────────────────────────────────────────────
# SSE — CANLI NABİZ
# ─────────────────────────────────────────────────────────

@app.get("/api/events")
async def events():
    async def stream():
        count = 0
        while True:
            total = manager.collection.count() if manager else 0
            data = json.dumps({"type": "pulse", "total": total, "tick": count})
            yield f"data: {data}\n\n"
            count += 1
            await asyncio.sleep(5)
    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# ─────────────────────────────────────────────────────────
# STATIC FILES — Dashboard
# ─────────────────────────────────────────────────────────

app.mount("/", StaticFiles(directory="/home/xmrah/Projects/localmind/dashboard", html=True))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
