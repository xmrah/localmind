"""
Localmind v2 — Veri Modelleri
Tüm sistem bu modeller üzerinden konuşur.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class Memory(BaseModel):
    """Tek bir hafıza kaydı."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    konu: str
    bilgi: str
    oda: str = "genel"
    agent_id: str = "user"           # Kim yazdı: "user", "antigravity", "continue"
    importance: float = 7.0          # 1-10 arası önem skoru
    access_count: int = 0            # Kaç kez erişildi
    created_at: str = Field(default_factory=lambda: datetime.now().astimezone().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().astimezone().isoformat())
    tags: list[str] = Field(default_factory=list)
    archived: bool = False

    def decay_score(self) -> float:
        """Zaman geçtikçe önem skoru düşer, ama erişim artırır."""
        from datetime import datetime
        now = datetime.now().astimezone()
        created = datetime.fromisoformat(self.created_at)
        if created.tzinfo is None:
            created = created.astimezone() # Fallback for old naive records
        days = (now - created).days
        decayed = self.importance * (0.99 ** days) + (self.access_count * 0.5)
        return min(10.0, decayed)


class Entity(BaseModel):
    """Knowledge Graph'taki bir varlık (kişi, cihaz, kavram...)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    entity_type: str = "concept"     # "person", "device", "concept", "place", "tech"
    description: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now().astimezone().isoformat())


class Relation(BaseModel):
    """İki entity arasındaki ilişki."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_name: str
    relation: str                    # "KULLANIR", "ÇALIŞTIRIR", "BAĞLIDIR", "ÖĞRENMEK_İSTİYOR"
    target_name: str
    memory_id: str | None = None  # Hangi anıdan çıkarıldı
    created_at: str = Field(default_factory=lambda: datetime.now().astimezone().isoformat())


class UpsertDecision(BaseModel):
    """LLM'nin upsert kararı."""
    action: str                      # "create", "update", "merge", "skip"
    reason: str
    existing_id: str | None = None


class SearchResult(BaseModel):
    """Arama sonucu."""
    memory: Memory
    score: float
    rank: int
