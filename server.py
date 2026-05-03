"""
Localmind v2 — MCP Server (stdio)
Claude Desktop, Antigravity ve diğer MCP client'lar bu sunucuya bağlanır.
Yeni MemoryManager üzerinden çalışır — akıllı upsert, otomatik sınıflandırma.
"""
import sys, os, asyncio, json, logging

sys.path.insert(0, "/home/xmrah/Projects/localmind")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import ctypes
for lib in ["libstdc++.so.6", "libz.so.1"]:
    try: ctypes.CDLL(lib)
    except Exception: pass

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("localmind.mcp")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# MemoryManager — lazy yükle
_manager = None

def get_manager():
    global _manager
    if _manager is None:
        from core.memory_manager import MemoryManager
        _manager = MemoryManager()
    return _manager


app = Server("localmind-v2")


@app.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="hafizaya_yaz",
            description="Bir bilgiyi Zihin Sarayı'na akıllıca kaydet. Otomatik sınıflandırma, upsert ve entity çıkarımı yapar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "konu": {"type": "string", "description": "Anının başlığı (kısa, açıklayıcı)"},
                    "bilgi": {"type": "string", "description": "Kaydedilecek bilginin tamamı"},
                    "oda": {"type": "string", "description": "Oda (opsiyonel, boş bırakılırsa otomatik belirlenir)",
                            "enum": ["mimari", "guvenlik", "donanim", "ogrenme", "kisisel", "genel"]},
                    "importance": {"type": "number", "description": "Önem skoru 1-10 (varsayılan: 7)", "default": 7}
                },
                "required": ["konu", "bilgi"]
            }
        ),
        types.Tool(
            name="hafizada_ara",
            description="Zihin Sarayı'nda semantik arama yap. Öneme ve benzerliğe göre sıralı sonuçlar döner.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sorgu": {"type": "string", "description": "Arama sorgusu"},
                    "sonuc_sayisi": {"type": "integer", "description": "Kaç sonuç dönsün (varsayılan: 3)", "default": 3},
                    "oda": {"type": "string", "description": "Belirli bir odada ara (opsiyonel)"}
                },
                "required": ["sorgu"]
            }
        ),
        types.Tool(
            name="hafizayi_unut",
            description="Bir anıyı arşivle (tamamen silmez, sadece aktif görünümden kaldırır).",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "Arşivlenecek anının ID'si"}
                },
                "required": ["memory_id"]
            }
        ),
        types.Tool(
            name="profil_goster",
            description="Kullanıcının hafıza profilini göster: oda dağılımı, en çok kullanılan etiketler.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="oda_listele",
            description="Tüm hafıza odalarını ve içerdikleri anı sayısını listele.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    mgr = get_manager()

    if name == "hafizaya_yaz":
        result = await mgr.add_memory(
            konu=arguments["konu"],
            bilgi=arguments["bilgi"],
            oda=arguments.get("oda"),
            agent_id="antigravity",
            importance=float(arguments.get("importance", 7.0))
        )
        return [types.TextContent(type="text", text=result.get("message", json.dumps(result, ensure_ascii=False)))]

    elif name == "hafizada_ara":
        results = mgr.search(
            query=arguments["sorgu"],
            n=int(arguments.get("sonuc_sayisi", 3)),
            oda=arguments.get("oda")
        )
        if not results:
            return [types.TextContent(type="text", text="Bu konuda hafızada kayıt bulunamadı.")]
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] 📍 {r['konu']} ({r['oda']}) — Benzerlik: {r['score']:.2f}")
            lines.append(f"    {r['content'][:200]}...")
            if r.get("tags"):
                lines.append(f"    Etiketler: {', '.join(r['tags'])}")
        return [types.TextContent(type="text", text="\n".join(lines))]

    elif name == "hafizayi_unut":
        ok = mgr.archive_memory(arguments["memory_id"])
        msg = "✅ Anı arşivlendi." if ok else "❌ Anı bulunamadı."
        return [types.TextContent(type="text", text=msg)]

    elif name == "profil_goster":
        profile = mgr.get_user_profile()
        lines = [
            f"🧠 Toplam Anı: {profile['total_memories']}",
            f"🏆 En Aktif Oda: {profile['most_active_room']}",
            f"📂 Oda Dağılımı: {json.dumps(profile['rooms'], ensure_ascii=False)}",
            f"🏷️ Öne Çıkan Etiketler: {', '.join(profile['top_tags'][:5]) or 'henüz yok'}",
        ]
        return [types.TextContent(type="text", text="\n".join(lines))]

    elif name == "oda_listele":
        stats = mgr.get_stats()
        lines = [f"📁 {k}: {v} anı" for k, v in stats.items() if k != "total"]
        lines.append(f"\nToplam: {stats.get('total', 0)} anı")
        return [types.TextContent(type="text", text="\n".join(lines))]

    raise ValueError(f"Bilinmeyen araç: {name}")


async def main():
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
