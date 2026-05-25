"""
Localmind MCP SSE Server — Open WebUI entegrasyonu için.
server.py'daki araçları HTTP/SSE üzerinden sunar.
"""
import os, sys, asyncio, logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp import types

# Localmind ana dizinini path'e ekle
sys.path.insert(0, "/home/xmrah/Projects/localmind")

# MemoryManager'ı server.py ile aynı mantıkta yükle
_manager = None
def get_manager():
    global _manager
    if _manager is None:
        from core.memory_manager import MemoryManager
        _manager = MemoryManager()
    return _manager

# MCP Server Tanımı
app_mcp = Server("localmind-sse")

@app_mcp.list_tools()
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
                    "importance": {"type": "number", "description": "Önem skoru 1-10 (varsayılan: 7)"},
                    "agent_id": {"type": "string", "description": "Yazan ajan kimliği (opsiyonel, varsayılan: user)"}
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
                    "sonuc_sayisi": {"type": "integer", "description": "Kaç sonuç dönsün (varsayılan: 3)"},
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
        ),
        types.Tool(
            name="grafik_sorgula",
            description="Bir varlığın (kişi, kavram, teknoloji) knowledge graph bağlantılarını sorgula.",
            inputSchema={
                "type": "object",
                "properties": {
                    "varlik": {"type": "string", "description": "Sorgulanacak varlık adı"}
                },
                "required": ["varlik"]
            }
        )
    ]

@app_mcp.call_tool()
async def call_tool(name: str, arguments: dict):
    import json
    mgr = get_manager()

    if name == "hafizaya_yaz":
        result = await mgr.add_memory(
            konu=arguments["konu"],
            bilgi=arguments["bilgi"],
            oda=arguments.get("oda"),
            agent_id=arguments.get("agent_id", "user"),
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
            lines.append(f"[{i}] {r['konu']} ({r['oda']}) — Benzerlik: {r['score']:.2f} | ID: {r['id']}")
            lines.append(f"    {r['content'][:300]}")
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
            f"Toplam Anı: {profile['total_memories']}",
            f"En Aktif Oda: {profile['most_active_room']}",
            f"Oda Dağılımı: {json.dumps(profile['rooms'], ensure_ascii=False)}",
            f"Öne Çıkan Etiketler: {', '.join(profile['top_tags'][:5]) or 'henüz yok'}",
        ]
        return [types.TextContent(type="text", text="\n".join(lines))]

    elif name == "oda_listele":
        stats = mgr.get_stats()
        lines = [f"{k}: {v} anı" for k, v in stats.items() if k != "total"]
        lines.append(f"\nToplam: {stats.get('total', 0)} anı")
        return [types.TextContent(type="text", text="\n".join(lines))]

    elif name == "grafik_sorgula":
        data = mgr.search_graph(arguments["varlik"])
        lines = [f"'{data['entity']}' için Knowledge Graph:"]
        if data["eslesen_varliklar"]:
            lines.append(f"\nEşleşen varlıklar: {', '.join(v['ad'] for v in data['eslesen_varliklar'])}")
        if data["cikis_iliskileri"]:
            lines.append("\nBağlantılar (çıkış):")
            for rel in data["cikis_iliskileri"]:
                lines.append(f"  → [{rel['iliski']}] {rel['hedef']}")
        if data["giris_iliskileri"]:
            lines.append("\nBağlantılar (giriş):")
            for rel in data["giris_iliskileri"]:
                lines.append(f"  ← {rel['kaynak']} [{rel['iliski']}]")
        if not data["cikis_iliskileri"] and not data["giris_iliskileri"] and not data["eslesen_varliklar"]:
            lines.append("Bu varlık için graph kaydı bulunamadı.")
        return [types.TextContent(type="text", text="\n".join(lines))]

    raise ValueError(f"Bilinmeyen araç: {name}")

# FastAPI Wrapper
app = FastAPI()
sse = SseServerTransport("/messages")

@app.get("/sse")
async def handle_sse(request: Request):
    async with sse.connect_scope(request.scope, request.receive, request._send):
        await app_mcp.run(
            sse.read_socket,
            sse.write_socket,
            app_mcp.create_initialization_options()
        )

@app.post("/messages")
async def handle_messages(request: Request):
    await sse.handle_post_request(request.scope, request.receive, request._send)

if __name__ == "__main__":
    import uvicorn
    # 8001 portunda çalıştır (8000'de dashboard var)
    uvicorn.run(app, host="0.0.0.0", port=8001)
