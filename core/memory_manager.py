"""
Localmind v2 — Memory Manager
Projenin kalbi. Tüm hafıza işlemleri buradan geçer.
Mem0 tarzı akıllı upsert + Letta tarzı entity grafiği.
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional
import chromadb
from chromadb.config import Settings

from .models import Memory, Entity, Relation
from .intelligence import (
    classify_room, decide_upsert, extract_entities,
    generate_tags, is_ollama_available
)

log = logging.getLogger("localmind.memory")

DB_PATH = "/home/xmrah/Projects/localmind/chroma_db"
GRAPH_DB_PATH = "/home/xmrah/Projects/localmind/graph.db"
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
        log.info(f"MemoryManager hazır. {self.collection.count()} anı yüklü.")

    def _init_graph_db(self):
        """Entity-relation veritabanını başlat."""
        conn = sqlite3.connect(GRAPH_DB_PATH)
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
        """)
        conn.commit()
        conn.close()

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
                agent_id=meta.get("agent_id", "user"),
                importance=float(meta.get("importance", 7.0)),
                access_count=int(meta.get("access_count", 0)),
                created_at=meta.get("created_at", datetime.now().isoformat()),
                updated_at=meta.get("updated_at", datetime.now().isoformat()),
                tags=json.loads(meta.get("tags", "[]")),
                archived=meta.get("archived", "false") == "true"
            ))
        return memories

    def get_stats(self) -> dict:
        """Oda bazlı istatistikler. Entity odası dahil edilmez."""
        memories = self.get_all_memories()
        stats: dict = {}
        for m in memories:
            oda = m.oda.lower()
            if oda == "entity":  # Entity grafik düğümleri istatistiğe dahil olmaz
                continue
            stats[oda] = stats.get(oda, 0) + 1
        stats["total"] = len(memories)
        return stats

    def get_room_memories(self, oda: str) -> list[Memory]:
        """Belirli bir odanın anılarını döndür."""
        all_m = self.get_all_memories()
        return [m for m in all_m if m.oda.lower() == oda.lower()]

    def search(self, query: str, n: int = 5, oda: Optional[str] = None) -> list[dict]:
        """Semantik arama. Cosine benzerliği + importance decay skoruna göre sırala."""
        total = self.collection.count()
        if total == 0:
            return []

        where_filter = {"oda": oda} if oda else None
        n_query = min(n * 2, total)

        # n_results, filtrelenmiş koleksiyondaki eleman sayısını aşabilir; küçülterek yeniden dene
        for attempt_n in [n_query, n, 1]:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=attempt_n,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"]
                )
                break
            except Exception as e:
                if attempt_n == 1:
                    log.error(f"Arama hatası: {e}")
                    return []

        items = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            # Cosine space: distance = 1 - cosine_similarity → score = 1 - distance
            score = 1.0 - distance

            # Negatif cosine benzerliği olan (tamamen ilgisiz) sonuçları filtrele
            if score < 0.0:
                continue

            if meta.get("archived", "false") == "true":
                continue

            # Erişim sayısını artır
            self._increment_access(doc_id, meta)

            items.append({
                "id": doc_id,
                "konu": meta.get("konu", ""),
                "content": results["documents"][0][i],
                "oda": meta.get("oda", "genel"),
                "score": round(score, 3),
                "importance": float(meta.get("importance", 7.0)),
                "access_count": int(meta.get("access_count", 0)),
                "created_at": meta.get("created_at", datetime.now().isoformat()),
                "tags": json.loads(meta.get("tags", "[]")),
            })

        # Cosine benzerliği (%60) + importance decay (%40) hibrit sıralama
        def _decay_score(item: dict) -> float:
            try:
                days = (datetime.now() - datetime.fromisoformat(item["created_at"])).days
            except Exception:
                days = 0
            decayed = item["importance"] * (0.99 ** days) + (item["access_count"] * 0.5)
            return min(10.0, decayed)

        items.sort(
            key=lambda x: x["score"] * 0.6 + (_decay_score(x) / 10) * 0.4,
            reverse=True
        )
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
        oda: Optional[str] = None,
        agent_id: str = "user",
        importance: float = 7.0
    ) -> dict:
        """
        Akıllı hafıza ekleme:
        1. Oda otomatik sınıflandırma (Ollama)
        2. Benzer anı var mı? (ChromaDB)
        3. Upsert kararı (Ollama)
        4. Entity çıkarımı (Ollama)
        5. Kaydet veya güncelle
        """
        ollama_ok = await is_ollama_available()

        # 1. Oda sınıflandırma
        if not oda or oda == "genel":
            if ollama_ok:
                oda = await classify_room(konu, bilgi)
                log.info(f"Otomatik sınıflandırma: {oda}")
            else:
                oda = "genel"

        # 2. Benzer anı ara
        similar = self.search(f"{konu} {bilgi}", n=3, oda=oda)

        # 3. Upsert kararı
        decision = {"action": "create", "existing_id": None, "reason": "Ollama yok"}
        if ollama_ok and similar:
            decision = await decide_upsert(konu, bilgi, similar)
            log.info(f"Upsert kararı: {decision['action']} — {decision['reason']}")

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

        now = datetime.now().isoformat()
        meta = {
            "konu": konu,
            "oda": oda,
            "agent_id": agent_id,
            "importance": str(importance),
            "access_count": "0",
            "created_at": now,
            "updated_at": now,
            "tags": json.dumps(tags, ensure_ascii=False),
            "archived": "false"
        }

        if decision["action"] == "update" and decision["existing_id"]:
            # Mevcut anıyı güncelle
            existing_id = decision["existing_id"]
            try:
                existing = self.collection.get(ids=[existing_id], include=["metadatas"])
                existing_meta = existing["metadatas"][0] if existing["metadatas"] else {}
                meta["created_at"] = existing_meta.get("created_at", now)
                meta["access_count"] = existing_meta.get("access_count", "0")
                meta["importance"] = str(max(
                    float(existing_meta.get("importance", 7.0)),
                    importance
                ))
            except Exception:
                pass

            self.collection.update(
                ids=[existing_id],
                documents=[bilgi],
                metadatas=[meta]
            )
            # Doğru ID ile entity ilişkilerini kaydet
            if relations:
                self._save_relations(relations, memory_id=existing_id)
            return {
                "status": "updated",
                "id": existing_id,
                "oda": oda,
                "tags": tags,
                "relations": len(relations),
                "message": f"✅ [{oda.upper()}] '{konu}' güncellendi"
            }
        else:
            # Yeni anı oluştur
            import uuid
            new_id = str(uuid.uuid4())
            self.collection.add(
                ids=[new_id],
                documents=[bilgi],
                metadatas=[meta]
            )
            # Doğru ID ile entity ilişkilerini kaydet
            if relations:
                self._save_relations(relations, memory_id=new_id)
            return {
                "status": "created",
                "id": new_id,
                "oda": oda,
                "tags": tags,
                "relations": len(relations),
                "message": f"✅ [{oda.upper()}] '{konu}' hafızaya işlendi"
            }

    # ─────────────────────────────────────────────────────
    # GRAPH İŞLEMLERİ
    # ─────────────────────────────────────────────────────

    def _save_relations(self, relations: list[dict], memory_id: Optional[str] = None):
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
        """D3.js için tam grafik verisi (ChromaDB + SQLite entity bağları)."""
        memories = self.get_all_memories()

        # ChromaDB düğümleri
        nodes = [{"id": m.id, "label": m.konu, "oda": m.oda, "content": m.bilgi,
                  "importance": m.importance, "type": "memory"} for m in memories]

        # Vektör benzerlik bağları
        links = []
        if len(memories) > 1:
            try:
                results = self.collection.query(
                    query_texts=[m.bilgi for m in memories[:20]],
                    n_results=min(4, len(memories)),
                    include=["distances"]
                )
                seen = set()
                for i, query_ids in enumerate(results["ids"]):
                    src_id = memories[i].id
                    for j, tgt_id in enumerate(query_ids):
                        if tgt_id == src_id:
                            continue
                        pair = tuple(sorted([src_id, tgt_id]))
                        if pair in seen:
                            continue
                        seen.add(pair)
                        dist = results["distances"][i][j]
                        sim = 1.0 - dist
                        if sim > 0.35:
                            links.append({"source": src_id, "target": tgt_id,
                                          "value": round(sim, 2), "type": "semantic"})
            except Exception as e:
                log.warning(f"Graph link hesaplama hatası: {e}")

        # SQLite entity bağları
        try:
            conn = sqlite3.connect(GRAPH_DB_PATH)
            entity_rels = conn.execute(
                "SELECT source_name, relation, target_name, memory_id FROM relations LIMIT 100"
            ).fetchall()
            conn.close()

            # Entity düğümlerini ekle (memory ID'si olmayanlar için)
            memory_ids = {m.id for m in memories}
            entity_nodes = {}
            for src, rel, tgt, mem_id in entity_rels:
                for name in [src, tgt]:
                    if name not in entity_nodes:
                        entity_nodes[name] = {
                            "id": f"entity_{name}",
                            "label": name,
                            "oda": "entity",
                            "content": name,
                            "importance": 5.0,
                            "type": "entity"
                        }
                links.append({
                    "source": f"entity_{src}" if mem_id not in memory_ids else (mem_id or f"entity_{src}"),
                    "target": f"entity_{tgt}",
                    "value": 0.8,
                    "type": "entity",
                    "label": rel
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
            return True
        except Exception as e:
            log.error(f"Arşivleme hatası: {e}")
            return False

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
