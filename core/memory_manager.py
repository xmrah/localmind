"""
Localmind v2 — Memory Manager
Projenin kalbi. Tüm hafıza işlemleri buradan geçer.
Mem0 tarzı akıllı upsert + Letta tarzı entity grafiği.
"""
import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime

import chromadb
from chromadb.config import Settings

from .intelligence import (
    classify_room,
    decide_upsert,
    extract_entities,
    generate_tags,
    is_ollama_available,
    summarize_conversation,
)
from .models import Memory

log = logging.getLogger("localmind.memory")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
GRAPH_DB_PATH = os.path.join(PROJECT_ROOT, "graph.db")
COLLECTION = "zihin_sarayi"


class MemoryManager:
    """
    Localmind v2'nin merkezi hafıza yöneticisi.
    - Akıllı upsert (yaz, güncelle veya geç)
    - Otomatik oda sınıflandırma
    - Entity-relation grafiği
    - Importance decay
    """

    def __init__(self):
        # ChromaDB bağlantısı
        self.chroma = chromadb.PersistentClient(
            path=DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"}  # Cosine similarity daha iyi
        )

        # SQLite graph veritabanı
        self._init_graph_db()
        # FTS5 ilk senkronizasyon
        self._sync_fts_if_needed()
        log.info(f"MemoryManager hazır. {self.collection.count()} anı yüklü.")

    def _init_graph_db(self):
        """Entity-relation ve FTS5 veritabanını başlat."""
        conn = sqlite3.connect(GRAPH_DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                entity_type TEXT DEFAULT 'concept',
                description TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS relations (
                id TEXT PRIMARY KEY,
                source_name TEXT NOT NULL,
                relation TEXT NOT NULL,
                target_name TEXT NOT NULL,
                memory_id TEXT,
                created_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_name);
            CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_name);
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                memory_id UNINDEXED,
                konu,
                content,
                tags,
                tokenize='unicode61'
            );
        """)
        conn.commit()
        conn.close()

    def _sync_fts_if_needed(self):
        """FTS5 tablosu ChromaDB'den geride kalmışsa senkronize et."""
        # Graph DB'yi read-only modda açarak kilitlemeleri önle
        uri_path = f"file:{GRAPH_DB_PATH}?mode=ro"
        conn = sqlite3.connect(uri_path, uri=True)
        fts_count = conn.execute("SELECT COUNT(*) FROM memories_fts").fetchone()[0]
        conn.close()
        
        try:
            unarchived = self.collection.get(where={"archived": "false"}, include=[])
            unarchived_count = len(unarchived.get("ids", []))
        except Exception:
            unarchived_count = self.collection.count()
            
        if fts_count >= unarchived_count:
            return
        log.info(f"FTS5 senkronizasyon: {fts_count}/{unarchived_count}")
        data = self.collection.get(include=["documents", "metadatas"])
        conn = sqlite3.connect(GRAPH_DB_PATH)
        for i, mem_id in enumerate(data["ids"]):
            meta = data["metadatas"][i]
            if meta.get("archived", "false") == "true":
                continue
            exists = conn.execute(
                "SELECT 1 FROM memories_fts WHERE memory_id=?", (mem_id,)
            ).fetchone()
            if not exists:
                tags_str = " ".join(json.loads(meta.get("tags", "[]")))
                conn.execute(
                    "INSERT INTO memories_fts(memory_id, konu, content, tags) VALUES(?,?,?,?)",
                    (mem_id, meta.get("konu", ""), data["documents"][i], tags_str)
                )
        conn.commit()
        conn.close()
        log.info("FTS5 senkronizasyon tamamlandı.")

    def _fts_upsert(self, memory_id: str, konu: str, content: str, tags: list):
        """FTS5 tablosuna ekle veya güncelle."""
        try:
            tags_str = " ".join(tags) if tags else ""
            conn = sqlite3.connect(GRAPH_DB_PATH)
            conn.execute("DELETE FROM memories_fts WHERE memory_id=?", (memory_id,))
            conn.execute(
                "INSERT INTO memories_fts(memory_id, konu, content, tags) VALUES(?,?,?,?)",
                (memory_id, konu, content, tags_str)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.warning(f"FTS upsert hatası: {e}")

    def _bm25_search(self, query: str, limit: int = 30) -> dict[str, float]:
        """SQLite FTS5 BM25 keyword arama. {memory_id: 0.0 - 1.0 skor} döndürür."""
        import re
        clean = re.sub(r'[^\w\s]', ' ', query, flags=re.UNICODE).strip()
        words = [w for w in clean.split() if len(w) >= 2]
        if not words:
            return {}
        fts_query = " OR ".join(f'"{w}"*' for w in words[:10])
        try:
            uri_path = f"file:{GRAPH_DB_PATH}?mode=ro"
            conn = sqlite3.connect(uri_path, uri=True)
            # FTS5 bm25 ağırlıkları: konu=5.0, content=1.0, tags=3.0
            rows = conn.execute(
                "SELECT memory_id, bm25(memories_fts, 5.0, 1.0, 3.0) as rank FROM memories_fts WHERE memories_fts MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, limit)
            ).fetchall()
            conn.close()
        except Exception as e:
            log.warning(f"BM25 arama hatası: {e}")
            return {}
        if not rows:
            return {}
        # FTS5 bm25 rank negatif; en negatif = en iyi eşleşme
        # Sıralı yumuşak ölçekleme: en iyi 1.0, en dip 0.45
        ranks = [r for _, r in rows]
        min_r, max_r = min(ranks), max(ranks)
        spread = max_r - min_r
        scores = {}
        for mid, r in rows:
            if spread == 0:
                scores[mid] = 1.0
            else:
                scores[mid] = round(1.0 - (0.55 * ((r - min_r) / spread)), 3)
        return scores

    # ─────────────────────────────────────────────────────
    # TEMEL OKUMA İŞLEMLERİ
    # ─────────────────────────────────────────────────────

    def get_all_memories(self, include_archived: bool = False) -> list[Memory]:
        """Tüm anıları döndür."""
        data = self.collection.get(include=["documents", "metadatas"])
        memories = []
        for i, doc_id in enumerate(data["ids"]):
            meta = data["metadatas"][i]
            if not include_archived and meta.get("archived", "false") == "true":
                continue
            memories.append(Memory(
                id=doc_id,
                konu=meta.get("konu", ""),
                bilgi=data["documents"][i],
                oda=meta.get("oda", "genel"),
                kanat=meta.get("kanat", "genel"),
                dolap=meta.get("dolap", "genel"),
                agent_id=meta.get("agent_id", "user"),
                importance=float(meta.get("importance", 7.0)),
                access_count=int(meta.get("access_count", 0)),
                created_at=meta.get("created_at") or meta.get("updated_at") or datetime.now().astimezone().isoformat(),
                updated_at=meta.get("updated_at") or datetime.now().astimezone().isoformat(),
                tags=json.loads(meta.get("tags", "[]")),
                archived=meta.get("archived", "false") == "true"
            ))
        return memories

    def get_memory_counts(self) -> dict:
        """Aktif, arşivli ve toplam anı sayılarını hızlıca döndürür."""
        try:
            data = self.collection.get(include=["metadatas"])
            archived = sum(1 for m in data.get("metadatas", []) if m.get("archived", "false") == "true")
            total = len(data.get("ids", []))
            active = total - archived
            return {"active": active, "archived": archived, "total": total}
        except Exception:
            c = self.collection.count()
            return {"active": c, "archived": 0, "total": c}

    def get_stats(self) -> dict:
        """Oda bazlı istatistikler."""
        memories = self.get_all_memories()
        stats: dict = {}
        for m in memories:
            oda = m.oda.lower()
            stats[oda] = stats.get(oda, 0) + 1
        stats["total"] = len(memories)
        return stats

    def get_room_memories(self, oda: str) -> list[Memory]:
        """Belirli bir odanın anılarını döndür."""
        try:
            data = self.collection.get(where={"oda": oda}, include=["documents", "metadatas"])
        except Exception:
            # Fallback if where filter fails
            all_m = self.get_all_memories()
            return [m for m in all_m if m.oda.lower() == oda.lower()]
            
        memories = []
        for i, doc_id in enumerate(data.get("ids", [])):
            meta = data["metadatas"][i]
            if meta.get("archived", "false") == "true":
                continue
            memories.append(Memory(
                id=doc_id,
                konu=meta.get("konu", ""),
                bilgi=data["documents"][i],
                oda=meta.get("oda", "genel"),
                kanat=meta.get("kanat", "genel"),
                dolap=meta.get("dolap", "genel"),
                agent_id=meta.get("agent_id", "user"),
                importance=float(meta.get("importance", 7.0)),
                access_count=int(meta.get("access_count", 0)),
                created_at=meta.get("created_at", "1970-01-01T00:00:00+00:00"),
                updated_at=meta.get("updated_at", "1970-01-01T00:00:00+00:00"),
                tags=json.loads(meta.get("tags", "[]")),
                archived=False
            ))
        return memories

    def search(self, query: str, n: int = 8, oda: str | None = None) -> list[dict]:
        """
        2026 Bireysel Zihin Sarayı Hibrit Arama (RRF + BM25 + Vektör + Eşik Filtresi).
        - Tam metin (FTS5) ve vektör adaylarını birleştirir (kayıp önler).
        - Başlık ve etiket eşleşmelerine öncelik verir.
        - Alakasız gürültüyü eşik filtresiyle eler (zorla doldurma yapmaz).
        - Her zaman pozitif %0 - %100 normalize güven skoru üretir.
        """
        query_clean = query.strip()
        if not query_clean:
            return []

        all_memories_map = {m.id: m for m in self.get_all_memories(include_archived=False)}
        if not all_memories_map:
            return []

        import re
        q_words = [w.lower() for w in re.sub(r'[^\w\s]', ' ', query_clean, flags=re.UNICODE).split() if len(w) >= 2]
        q_lower = query_clean.lower()

        # 1. Dal: SQLite FTS5 BM25 Arama (Kelime ve başlık eşleşmesi)
        bm25_scores = self._bm25_search(query_clean, limit=max(n * 4, 30))

        # 2. Dal: ChromaDB Vektör Sorgusu (Anlamsal yakınlık)
        where_filter = {"oda": oda} if oda else None
        vector_sims = {}
        try:
            vec_limit = min(max(n * 4, 30), self.collection.count())
            results = self.collection.query(
                query_texts=[query_clean],
                n_results=vec_limit,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            if results and results.get("ids") and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    dist = results["distances"][0][i]
                    # Cosine distance: 0.0 (özdeş) .. 1.25 (gürültü)
                    if dist <= 0.0:
                        sim = 1.0
                    elif dist >= 1.25:
                        sim = 0.0
                    else:
                        sim = max(0.0, 1.0 - (dist / 1.25))
                    vector_sims[doc_id] = round(sim, 3)
        except Exception as e:
            log.warning(f"Vektör arama hatası: {e}")

        # 3. İki bağımsız arama havuzunun birleşimi (Candidate Union)
        candidate_ids = set(bm25_scores.keys()) | set(vector_sims.keys())
        if not candidate_ids:
            return []

        from .config import get_config
        decay_factor = float(get_config().get("decay_factor", 0.05))

        items = []
        for doc_id in candidate_ids:
            m = all_memories_map.get(doc_id)
            if not m or m.archived:
                continue
            if oda and m.oda.lower() != oda.lower():
                continue

            lex_score = bm25_scores.get(doc_id, 0.0)
            sem_score = vector_sims.get(doc_id, 0.0)

            title_lower = m.konu.lower()
            tag_list = [t.lower() for t in (m.tags or [])]

            # Başlık ve etiket önceliği (Title & Tag Boost)
            if q_lower in title_lower:
                lex_score = max(lex_score, 0.95)
            elif any(w in title_lower or w in tag_list for w in q_words):
                lex_score = max(lex_score, 0.80)

            # Eşik Değeri (Relevance Floor):
            # Kelime eşleşmesi YOKSA ve anlamsal benzerlik gürültü seviyesindeyse elenir
            if lex_score == 0.0 and sem_score < 0.40:
                continue

            # Hibrit Füzyon Skoru:
            if lex_score > 0.0 and sem_score > 0.0:
                base_score = (lex_score * 0.65) + (sem_score * 0.35)
            elif lex_score > 0.0:
                base_score = lex_score * 0.90
            else:
                base_score = sem_score * 0.80

            # Ebbinghaus tazelik ve erişim bonusu (%5 hafif çarpan)
            try:
                days = (datetime.now() - datetime.fromisoformat(m.created_at)).days
            except Exception:
                days = 0
            decay_mult = (1.0 - decay_factor) ** min(days, 365)
            access_boost = min(1.0, m.access_count * 0.1)
            recency_bonus = (decay_mult * 0.03) + (access_boost * 0.02)

            final_score = min(1.0, max(0.05, base_score + recency_bonus))

            items.append({
                "id": doc_id,
                "konu": m.konu,
                "content": m.bilgi,
                "oda": m.oda,
                "kanat": m.kanat,
                "dolap": m.dolap,
                "score": round(final_score, 2),
                "importance": m.importance,
                "access_count": m.access_count,
                "created_at": m.created_at,
                "tags": m.tags or []
            })

        # Skora göre büyükten küçüğe kesin sıralama
        items.sort(key=lambda x: x["score"], reverse=True)

        # En üstteki sonuçların erişim sayacını artır
        for it in items[:n]:
            self._increment_access(it["id"], {"access_count": it["access_count"]})

        return items[:n]

    def _increment_access(self, doc_id: str, meta: dict):
        """Erişim sayacını artır (background'da yapılır)."""
        try:
            new_count = int(meta.get("access_count", 0)) + 1
            self.collection.update(
                ids=[doc_id],
                metadatas=[{**meta, "access_count": str(new_count)}]
            )
        except Exception:
            pass

    # ─────────────────────────────────────────────────────
    # AKILLI YAZMA — UPSERT
    # ─────────────────────────────────────────────────────

    async def add_memory(
        self,
        konu: str,
        bilgi: str,
        oda: str | None = None,
        kanat: str = "genel",
        dolap: str = "genel",
        agent_id: str = "user",
        importance: float = 7.0,
        created_at: str | None = None,
        use_ai: bool = True
    ) -> dict:
        """
        Hafıza ekleme:
        - use_ai=False ise: Doğrudan / Anında Manuel Kayıt (0 MB VRAM, ~5ms)
        - use_ai=True ise: Akıllı mod (Ollama sınıflandırma, upsert ve entity çıkarımı)
        """
        if not use_ai:
            # Doğrudan / Hızlı Manuel Kayıt: LLM hiç çağrılmaz, VRAM tüketimi sıfır (0 MB)
            if not oda:
                oda = "genel"
            now = created_at if created_at else datetime.now().isoformat()
            meta = {
                "konu": konu,
                "oda": oda,
                "kanat": kanat,
                "dolap": dolap,
                "agent_id": agent_id,
                "importance": str(importance),
                "access_count": "0",
                "created_at": now,
                "updated_at": datetime.now().isoformat(),
                "tags": json.dumps([], ensure_ascii=False),
                "archived": "false"
            }
            import uuid
            new_id = str(uuid.uuid4())
            await asyncio.to_thread(self.collection.add,
                ids=[new_id],
                documents=[bilgi],
                metadatas=[meta]
            )
            await asyncio.to_thread(self._fts_upsert, new_id, konu, bilgi, [])
            log.info(f"⚡ [MANUEL] '{konu}' 0 MB VRAM ile anında kaydedildi.")
            return {
                "status": "created",
                "id": new_id,
                "oda": oda,
                "kanat": kanat,
                "dolap": dolap,
                "created_at": now,
                "tags": [],
                "relations": 0,
                "message": f"⚡ [{oda.upper()}] '{konu}' anında hafızaya işlendi (0 MB VRAM)"
            }

        ollama_ok = await is_ollama_available()

        # 1. Oda sınıflandırma
        if not oda or oda == "genel":
            if ollama_ok:
                oda = await classify_room(konu, bilgi)
                log.info(f"Otomatik sınıflandırma: {oda}")
            else:
                oda = "genel"

        # 2. Benzer anı ara
        similar = await asyncio.to_thread(self.search, f"{konu} {bilgi}", 3, oda)

        # 3. Upsert kararı
        decision = {"action": "create", "existing_id": None, "conflict_ids": [], "reason": "Ollama yok"}
        if ollama_ok and similar:
            decision = await decide_upsert(konu, bilgi, similar)
            log.info(f"Upsert kararı: {decision['action']} — {decision['reason']}")
            # Çakışan anıları otomatik arşivle (config izin veriyorsa)
            from .config import get_config
            cfg = get_config()
            if cfg.get("auto_archive_conflicts", True):
                for cid in decision.get("conflict_ids", []):
                    if await asyncio.to_thread(self.archive_memory, cid):
                        log.info(f"Çakışan anı arşivlendi: {cid}")

        # 4. Tag üretimi
        tags = []
        if ollama_ok:
            try:
                tags = await generate_tags(konu, bilgi)
            except Exception:
                pass

        # 5. Entity çıkarımı — sadece veriyi al, kaydetme henüz (doğru ID sonra belirleniyor)
        relations = []
        if ollama_ok:
            try:
                relations = await extract_entities(konu, bilgi)
            except Exception as e:
                log.warning(f"Entity çıkarımı başarısız: {e}")

        # 6. Kaydet veya güncelle
        if decision["action"] == "skip":
            return {"status": "skipped", "reason": decision["reason"], "oda": oda}

        now = created_at if created_at else datetime.now().isoformat()
        meta = {
            "konu": konu,
            "oda": oda,
            "kanat": kanat,
            "dolap": dolap,
            "agent_id": agent_id,
            "importance": str(importance),
            "access_count": "0",
            "created_at": now,
            "updated_at": datetime.now().isoformat(),
            "tags": json.dumps(tags, ensure_ascii=False),
            "archived": "false"
        }

        if decision["action"] == "update" and decision["existing_id"]:
            # Mevcut anıyı güncelle
            existing_id = decision["existing_id"]
            try:
                existing = await asyncio.to_thread(self.collection.get, ids=[existing_id], include=["metadatas"])
                existing_meta = existing["metadatas"][0] if existing["metadatas"] else {}
                meta["created_at"] = created_at if created_at else existing_meta.get("created_at", "1970-01-01T00:00:00+00:00")
                meta["access_count"] = existing_meta.get("access_count", "0")
                meta["importance"] = str(max(
                    float(existing_meta.get("importance", 7.0)),
                    importance
                ))
            except Exception:
                pass

            await asyncio.to_thread(self.collection.upsert,
                ids=[existing_id],
                documents=[bilgi],
                metadatas=[meta]
            )
            # FTS5 güncelle
            await asyncio.to_thread(self._fts_upsert, existing_id, konu, bilgi, tags)
            # Doğru ID ile entity ilişkilerini kaydet
            if relations:
                await asyncio.to_thread(self._save_relations, relations, existing_id)
            return {
                "status": "updated",
                "id": existing_id,
                "oda": oda,
                "kanat": kanat,
                "dolap": dolap,
                "created_at": meta["created_at"],
                "tags": tags,
                "relations": len(relations),
                "message": f"✅ [{oda.upper()}] '{konu}' güncellendi"
            }
        else:
            # Yeni anı oluştur
            import uuid
            new_id = str(uuid.uuid4())
            await asyncio.to_thread(self.collection.add,
                ids=[new_id],
                documents=[bilgi],
                metadatas=[meta]
            )
            # FTS5 ekle
            await asyncio.to_thread(self._fts_upsert, new_id, konu, bilgi, tags)
            # Doğru ID ile entity ilişkilerini kaydet
            if relations:
                await asyncio.to_thread(self._save_relations, relations, new_id)
            return {
                "status": "created",
                "id": new_id,
                "oda": oda,
                "kanat": kanat,
                "dolap": dolap,
                "created_at": now,
                "tags": tags,
                "relations": len(relations),
                "message": f"✅ [{oda.upper()}] '{konu}' hafızaya işlendi"
            }

    # ─────────────────────────────────────────────────────
    # GRAPH İŞLEMLERİ
    # ─────────────────────────────────────────────────────

    def _save_relations(self, relations: list[dict], memory_id: str | None = None):
        """Entity ilişkilerini SQLite'a kaydet."""
        conn = sqlite3.connect(GRAPH_DB_PATH)
        now = datetime.now().isoformat()
        import uuid
        for rel in relations:
            source = rel.get("source", "").strip()
            relation = rel.get("relation", "").strip()
            target = rel.get("target", "").strip()
            if not (source and relation and target):
                continue
            # Upsert entity'ler
            for name in [source, target]:
                conn.execute(
                    "INSERT OR IGNORE INTO entities (id, name, created_at) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), name, now)
                )
            # İlişki ekle (aynı üçlü varsa tekrar ekleme)
            existing = conn.execute(
                "SELECT id FROM relations WHERE source_name=? AND relation=? AND target_name=?",
                (source, relation, target)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO relations (id, source_name, relation, target_name, memory_id, created_at) VALUES (?,?,?,?,?,?)",
                    (str(uuid.uuid4()), source, relation, target, memory_id, now)
                )
        conn.commit()
        conn.close()

    def get_graph_data(self) -> dict:
        """D3.js için tam grafik verisi (ChromaDB vektör benzerlikleri + SQLite entity bağları)."""
        memories = self.get_all_memories()

        # ChromaDB düğümleri
        nodes = [{"id": m.id, "label": m.konu, "oda": m.oda, "kanat": m.kanat, "dolap": m.dolap, "content": m.bilgi,
                  "importance": m.importance, "tags": m.tags,
                  "created_at": m.created_at, "type": "memory"} for m in memories]

        # Vektör benzerlik bağları (Tüm aktif anılar için precomputed embedding matrisi ile)
        links = []
        if len(memories) > 1:
            raw = None
            try:
                raw = self.collection.get(
                    where={"archived": "false"},
                    include=["embeddings"]
                )
            except Exception as e:
                log.warning(f"Chroma link get hatası, koleksiyon yenileniyor: {e}")
                try:
                    # Harici süreç yazımlarında Chroma segment önbelleğini tazelemek için koleksiyonu yeniden al
                    self.collection = self.client.get_collection(COLLECTION)
                    raw = self.collection.get(
                        where={"archived": "false"},
                        include=["embeddings"]
                    )
                except Exception as e2:
                    log.warning(f"Koleksiyon filtresiz çekiliyor: {e2}")
                    try:
                        raw = self.collection.get(include=["embeddings", "metadatas"])
                    except Exception as e3:
                        log.error(f"Chroma embedding alınamadı: {e3}")

            if raw:
                try:
                    raw_ids = raw.get("ids", [])
                    raw_embs = raw.get("embeddings")
                    metas = raw.get("metadatas")

                    # Eğer filtresiz fallback kullanıldıysa, arşivlenenleri filtrele
                    if metas is not None and len(metas) == len(raw_ids):
                        active_indices = [
                            idx for idx, m in enumerate(metas)
                            if (m or {}).get("archived", "false") != "true"
                        ]
                        raw_ids = [raw_ids[idx] for idx in active_indices]
                        if raw_embs is not None:
                            raw_embs = [raw_embs[idx] for idx in active_indices]

                    if raw_embs is not None and len(raw_embs) > 1:
                        import numpy as np
                        embs = np.array(raw_embs, dtype=np.float32)
                        norms = np.linalg.norm(embs, axis=1, keepdims=True)
                        norms[norms == 0] = 1.0
                        norm_embs = embs / norms
                        sim_matrix = np.dot(norm_embs, norm_embs.T)
                        np.fill_diagonal(sim_matrix, 0)

                        seen = set()
                        memory_id_set = {m.id for m in memories}

                        for i, src_id in enumerate(raw_ids):
                            if src_id not in memory_id_set:
                                continue
                            top_indices = np.argsort(sim_matrix[i])[-2:]

                            # En iyi 1. komşu (>= 0.50)
                            best_j = top_indices[-1]
                            sim_best = float(sim_matrix[i, best_j])
                            if sim_best >= 0.50:
                                tgt_id = raw_ids[best_j]
                                if tgt_id in memory_id_set and tgt_id != src_id:
                                    pair = tuple(sorted([src_id, tgt_id]))
                                    if pair not in seen:
                                        seen.add(pair)
                                        links.append({
                                            "source": src_id,
                                            "target": tgt_id,
                                            "value": round(sim_best, 2),
                                            "type": "semantic"
                                        })

                            # 2. komşu (sadece çok yüksek anlamsal yakınlık varsa >= 0.58)
                            if len(top_indices) > 1:
                                sec_j = top_indices[-2]
                                sim_sec = float(sim_matrix[i, sec_j])
                                if sim_sec >= 0.58:
                                    tgt_id = raw_ids[sec_j]
                                    if tgt_id in memory_id_set and tgt_id != src_id:
                                        pair = tuple(sorted([src_id, tgt_id]))
                                        if pair not in seen:
                                            seen.add(pair)
                                            links.append({
                                                "source": src_id,
                                                "target": tgt_id,
                                                "value": round(sim_sec, 2),
                                                "type": "semantic"
                                            })
                except Exception as calc_err:
                    log.warning(f"Graph matris hesaplama hatası: {calc_err}")

        # SQLite entity bağları
        try:
            conn = sqlite3.connect(GRAPH_DB_PATH)
            entity_rels = conn.execute(
                "SELECT source_name, relation, target_name, memory_id FROM relations LIMIT 100"
            ).fetchall()
            conn.close()

            memory_ids = {m.id for m in memories}
            entity_nodes = {}
            bad_entities = {
                "yok", "-", "--", "none", "null", "6 sayfa",
                "home", "settings", "timeline", "graph", "analytics",
                "memory rooms", "arama", "istatistik", "son anılar"
            }

            for src, rel, tgt, mem_id in entity_rels:
                s = src.strip()
                t = tgt.strip()
                r = rel.strip()
                if not s or not t or len(s) < 2 or len(t) < 2 or len(s) > 30 or len(t) > 30:
                    continue
                if s.lower() in bad_entities or t.lower() in bad_entities:
                    continue

                for name in [s, t]:
                    eid = f"entity_{name}"
                    if eid not in entity_nodes:
                        entity_nodes[eid] = {
                            "id": eid,
                            "label": name,
                            "oda": "entity",
                            "content": name,
                            "importance": 5.0,
                            "type": "entity"
                        }

                # Entity -> Entity ilişkisi
                links.append({
                    "source": f"entity_{s}",
                    "target": f"entity_{t}",
                    "value": 0.8,
                    "type": "entity",
                    "label": r
                })

                # Eğer anı ile ilişkiliyse köprü at
                if mem_id and mem_id in memory_ids:
                    links.append({
                        "source": mem_id,
                        "target": f"entity_{s}",
                        "value": 0.6,
                        "type": "entity",
                        "label": "içerir"
                    })

            nodes.extend(entity_nodes.values())
        except Exception as e:
            log.warning(f"Entity graph hatası: {e}")

        return {"nodes": nodes, "links": links}

    def search_graph(self, entity_name: str) -> dict:
        """Entity adına göre knowledge graph'ı sorgula."""
        conn = sqlite3.connect(GRAPH_DB_PATH)
        pattern = f"%{entity_name}%"
        as_source = conn.execute(
            "SELECT relation, target_name FROM relations WHERE source_name LIKE ? LIMIT 25",
            (pattern,)
        ).fetchall()
        as_target = conn.execute(
            "SELECT source_name, relation FROM relations WHERE target_name LIKE ? LIMIT 25",
            (pattern,)
        ).fetchall()
        entities = conn.execute(
            "SELECT name, entity_type FROM entities WHERE name LIKE ? LIMIT 20",
            (pattern,)
        ).fetchall()
        conn.close()
        return {
            "entity": entity_name,
            "cikis_iliskileri": [{"iliski": r, "hedef": t} for r, t in as_source],
            "giris_iliskileri": [{"kaynak": s, "iliski": r} for s, r in as_target],
            "eslesen_varliklar": [{"ad": n, "tip": t} for n, t in entities],
        }

    def archive_memory(self, memory_id: str) -> bool:
        """Bir anıyı arşivle (sil değil, gizle)."""
        try:
            data = self.collection.get(ids=[memory_id], include=["metadatas"])
            if not data["ids"]:
                return False
            meta = data["metadatas"][0]
            meta["archived"] = "true"
            self.collection.update(ids=[memory_id], metadatas=[meta])
            # FTS5'ten de kaldır
            try:
                conn = sqlite3.connect(GRAPH_DB_PATH)
                conn.execute("DELETE FROM memories_fts WHERE memory_id=?", (memory_id,))
                conn.commit()
                conn.close()
            except Exception:
                pass
            return True
        except Exception as e:
            log.error(f"Arşivleme hatası: {e}")
            return False

    def unarchive_memory(self, memory_id: str) -> bool:
        """Arşivlenmiş anıyı geri al (unarchive)."""
        try:
            data = self.collection.get(ids=[memory_id], include=["metadatas"])
            if not data["ids"]:
                return False
            meta = data["metadatas"][0]
            meta["archived"] = "false"
            self.collection.update(ids=[memory_id], metadatas=[meta])
            return True
        except Exception as e:
            log.error(f"Arşivden çıkarma hatası: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """Bir anıyı kalıcı olarak SİL."""
        try:
            self.collection.delete(ids=[memory_id])
            try:
                conn = sqlite3.connect(GRAPH_DB_PATH)
                conn.execute("DELETE FROM memories_fts WHERE memory_id=?", (memory_id,))
                conn.commit()
                conn.close()
            except Exception:
                pass
            return True
        except Exception as e:
            log.error(f"Silme hatası: {e}")
            return False

    def get_archived_memories(self) -> list[Memory]:
        """Sadece arşivlenmiş anıları getir."""
        try:
            data = self.collection.get(where={"archived": "true"}, include=["documents", "metadatas"])
        except Exception:
            return []
        memories = []
        for i, doc_id in enumerate(data.get("ids", [])):
            meta = data["metadatas"][i]
            memories.append(Memory(
                id=doc_id,
                konu=meta.get("konu", ""),
                bilgi=data["documents"][i],
                oda=meta.get("oda", "genel"),
                kanat=meta.get("kanat", "genel"),
                dolap=meta.get("dolap", "genel"),
                agent_id=meta.get("agent_id", "user"),
                importance=float(meta.get("importance", 7.0)),
                access_count=int(meta.get("access_count", 0)),
                created_at=meta.get("created_at", "1970-01-01T00:00:00+00:00"),
                updated_at=meta.get("updated_at", "1970-01-01T00:00:00+00:00"),
                tags=json.loads(meta.get("tags", "[]")),
                archived=True
            ))
        return memories

    def get_user_profile(self) -> dict:
        """Tüm anılardan kullanıcı profili çıkar."""
        memories = self.get_all_memories()
        rooms = {}
        for m in memories:
            rooms[m.oda] = rooms.get(m.oda, 0) + 1

        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)

        tag_counts = {}
        for t in all_tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_memories": len(memories),
            "rooms": rooms,
            "top_tags": [t[0] for t in top_tags],
            "most_active_room": max(rooms, key=rooms.get) if rooms else "genel",
            "oldest_memory": min(memories, key=lambda m: m.created_at).created_at if memories else None,
        }

    def export_to_file(self, path: str | None = None) -> str:
        """Tüm aktif anıları JSON dosyasına kaydet, dosya yolunu döndür."""
        import os
        if path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"/home/xmrah/Projects/localmind/exports/memories_{ts}.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        memories = self.get_all_memories(include_archived=False)
        data = [
            {
                "konu": m.konu,
                "bilgi": m.bilgi,
                "oda": m.oda,
                "importance": m.importance,
                "tags": m.tags,
                "created_at": m.created_at,
                "agent_id": m.agent_id,
            }
            for m in memories
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    # ─────────────────────────────────────────────────────
    # KONUŞMA ÖZETLEMESİ
    # ─────────────────────────────────────────────────────

    async def summarize_and_save(self, conversation: str, agent_id: str = "user") -> dict:
        """
        Konuşma metninden önemli bilgileri çıkarıp hafızaya kaydeder.
        Döndürür: {"saved": int, "skipped": int, "facts": list[str]}
        """
        facts = await summarize_conversation(conversation)
        if not facts:
            return {"saved": 0, "skipped": 0, "facts": [], "message": "Kayda değer bilgi bulunamadı."}

        saved, skipped = 0, 0
        fact_summaries = []
        for f in facts:
            result = await self.add_memory(
                konu=f["konu"],
                bilgi=f["bilgi"],
                agent_id=agent_id,
                importance=float(f.get("importance", 7.0))
            )
            if result.get("status") == "skipped":
                skipped += 1
            else:
                saved += 1
                fact_summaries.append(f"[{result.get('oda','?').upper()}] {f['konu']}")

        return {
            "saved": saved,
            "skipped": skipped,
            "facts": fact_summaries,
            "message": f"{saved} bilgi hafızaya kaydedildi, {skipped} tekrar atlandı."
        }

    # ─────────────────────────────────────────────────────
    # ZAMANSAL SORGULAR
    # ─────────────────────────────────────────────────────

    def get_memories_by_date(self, days: int = 7) -> list[Memory]:
        """Son N günde eklenen anıları döndür, önem skoruna göre sıralı."""
        cutoff = datetime.now().timestamp() - (days * 86400)
        memories = self.get_all_memories()
        recent = []
        for m in memories:
            try:
                ts = datetime.fromisoformat(m.created_at).timestamp()
                if ts >= cutoff:
                    recent.append(m)
            except Exception:
                pass
        recent.sort(key=lambda m: m.importance, reverse=True)
        return recent

    # ─────────────────────────────────────────────────────
    # PROAKTİF HATIRLATMA
    # ─────────────────────────────────────────────────────

    def get_reminders(self, n: int = 5) -> list[dict]:
        """
        Önemli ama uzun süredir erişilmemiş anıları döndür.
        Ebbinghaus unutma eğrisine göre en çok 'unutulmaya yüz tutmuş' anılar önce gelir.
        """
        memories = self.get_all_memories()
        scored = []
        now = datetime.now()
        for m in memories:
            try:
                days = (now - datetime.fromisoformat(m.created_at)).days
            except Exception:
                days = 0
            # Yüksek önem + uzun süre erişilmemiş = hatırlatılmalı
            # decay ne kadar düşükse (unutulmuşsa) skor o kadar yüksek
            decayed = m.importance * (0.99 ** days) + (m.access_count * 0.5)
            forgotten_score = m.importance - min(decayed, m.importance)
            scored.append({
                "id": m.id,
                "konu": m.konu,
                "bilgi": m.bilgi,
                "oda": m.oda,
                "importance": m.importance,
                "days_ago": days,
                "forgotten_score": round(forgotten_score, 2),
                "tags": m.tags,
            })
        # En çok unutulmuş ve önemli olanlar önce
        scored.sort(key=lambda x: x["forgotten_score"], reverse=True)
        return scored[:n]
