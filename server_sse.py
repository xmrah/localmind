"""
Localmind v2 — Ana Sunucu (FastAPI + SSE + StaticFiles)
Tüm API rotaları burada tanımlanır, MemoryManager üzerinden çalışır.
"""
import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

# LD_LIBRARY_PATH ChromaDB için gerekli
import ctypes

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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
    counts = manager.get_memory_counts()
    log.info(f"🧠 Localmind v2 başladı — {counts['active']} aktif anı ({counts['total']} toplam) yüklü")
    yield
    log.info("Localmind kapatılıyor...")

app = FastAPI(title="Localmind v2", version="2.0.0", lifespan=lifespan)

# Güvenlik: Yalnızca yerel dashboard ve araçların erişimine izin ver (Drive-by ve DNS Rebinding koruması)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────
# REQUEST MODELLERİ
# ─────────────────────────────────────────────────────────

class AddMemoryRequest(BaseModel):
    konu: str
    bilgi: str
    oda: str | None = None
    kanat: str | None = None
    dolap: str | None = None
    created_at: str | None = None
    agent_id: str = "user"
    importance: float = 7.0
    use_ai: bool = False

class ArchiveRequest(BaseModel):
    memory_id: str

class SettingsUpdateRequest(BaseModel):
    fast_model: str | None = None
    smart_model: str | None = None
    conv_model: str | None = None
    decay_factor: float | None = None
    auto_archive_conflicts: bool | None = None
    ollama_base: str | None = None

class TestModelRequest(BaseModel):
    model: str

# ─────────────────────────────────────────────────────────
# API ROTALARI
# ─────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    from core.intelligence import is_ollama_available
    ollama_ok = await is_ollama_available()
    counts = manager.get_memory_counts() if manager else {"active": 0, "archived": 0, "total": 0}
    return {
        "status": "ok",
        "version": "2.0.0",
        "memories": counts["active"],
        "active_memories": counts["active"],
        "archived_memories": counts["archived"],
        "total_documents": counts["total"],
        "ollama": ollama_ok,
        "timestamp": datetime.now().astimezone().isoformat()
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
         "kanat": m.kanat, "dolap": m.dolap,
         "importance": m.importance, "tags": m.tags, "created_at": m.created_at}
        for m in memories
    ]

@app.get("/api/memories")
async def all_memories(include_archived: bool = False):
    """Tüm anıları kanat, dolap ve tüm metadata ile döndürür."""
    if not manager:
        raise HTTPException(503)
    memories = manager.get_all_memories(include_archived=include_archived)
    return [
        {
            "id": m.id,
            "konu": m.konu,
            "content": m.bilgi,
            "oda": m.oda,
            "kanat": m.kanat,
            "dolap": m.dolap,
            "importance": m.importance,
            "access_count": m.access_count,
            "tags": m.tags,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
            "agent_id": m.agent_id,
            "archived": m.archived
        }
        for m in memories
    ]

@app.get("/api/graph")
async def graph():
    if not manager:
        raise HTTPException(503)
    return manager.get_graph_data()

@app.get("/api/search")
async def search(q: str = Query(..., min_length=1), oda: str | None = None, n: int = 5):
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
        kanat=req.kanat or "genel",
        dolap=req.dolap or "genel",
        created_at=req.created_at,
        agent_id=req.agent_id,
        importance=req.importance,
        use_ai=req.use_ai
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

@app.get("/api/memory/archived")
async def get_archived():
    if not manager:
        raise HTTPException(503)
    memories = manager.get_archived_memories()
    return [
        {"id": m.id, "konu": m.konu, "content": m.bilgi, "oda": m.oda,
         "kanat": m.kanat, "dolap": m.dolap,
         "importance": m.importance, "tags": m.tags, "created_at": m.created_at}
        for m in memories
    ]

@app.post("/api/memory/unarchive")
async def unarchive_memory(req: ArchiveRequest):
    if not manager:
        raise HTTPException(503)
    ok = manager.unarchive_memory(req.memory_id)
    if not ok:
        raise HTTPException(404, "Anı bulunamadı")
    return {"status": "unarchived"}

@app.get("/api/settings")
async def get_settings():
    from core.config import get_config
    from core.intelligence import get_ollama_models
    cfg = get_config()
    models = await get_ollama_models()
    return {
        "config": cfg,
        "available_models": models
    }

@app.post("/api/settings")
async def update_settings(req: SettingsUpdateRequest):
    from core.config import save_config
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    new_cfg = save_config(data)
    return {"status": "ok", "config": new_cfg, "message": "Ayarlar başarıyla kaydedildi ve uygulandı"}

@app.post("/api/settings/test-model")
async def test_model(req: TestModelRequest):
    from core.intelligence import test_ollama_model
    res = await test_ollama_model(req.model)
    return res

@app.delete("/api/memory/{memory_id}")
async def delete_memory(memory_id: str):
    if not manager:
        raise HTTPException(503)
    ok = manager.delete_memory(memory_id)
    if not ok:
        raise HTTPException(404, "Anı bulunamadı veya silinemedi")
    return {"status": "deleted"}

@app.get("/api/profile")
async def profile():
    """Kullanıcı profili — tüm anılardan çıkarılır."""
    if not manager:
        raise HTTPException(503)
    return manager.get_user_profile()

@app.get("/api/reminders")
async def reminders(n: int = 5):
    """Hatırlatılması gereken anılar — Ebbinghaus unutma eğrisi."""
    if not manager:
        raise HTTPException(503)
    return manager.get_reminders(n=n)

# ─────────────────────────────────────────────────────────
# SSE — CANLI NABİZ
# ─────────────────────────────────────────────────────────

@app.get("/api/events")
async def events(request: Request):
    async def stream():
        count = 0
        try:
            while True:
                if await request.is_disconnected():
                    break
                counts = manager.get_memory_counts() if manager else {"active": 0, "archived": 0, "total": 0}
                data = json.dumps({
                    "type": "pulse",
                    "total": counts["active"],
                    "active": counts["active"],
                    "archived": counts["archived"],
                    "tick": count
                })
                yield f"data: {data}\n\n"
                count += 1
                await asyncio.sleep(5)
        except (asyncio.CancelledError, GeneratorExit):
            pass
    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# ─────────────────────────────────────────────────────────
# STATIC FILES — Dashboard
# ─────────────────────────────────────────────────────────

DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboard")
app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info", timeout_graceful_shutdown=2)
