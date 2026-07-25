"""
Localmind v2 — Merkezi Araç Katmanı (FastMCP)
Tüm 10 MCP aracı burada, Stateless mimariyle tanımlanmıştır.
"""
import asyncio
import json
import os
import sys

# Dinamik path çözümü (Hardcoded sys.path düzeltildi)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# C-Extensions fallback (NixOS için)
import ctypes

for lib in ["libstdc++.so.6", "libz.so.1"]:
    try: ctypes.CDLL(lib)
    except Exception: pass

from fastmcp import FastMCP
from pydantic import Field

# Core imports
from core.memory_manager import MemoryManager

# FastMCP Initialization
mcp = FastMCP("localmind-v2")

_manager = None
def get_manager() -> MemoryManager:
    global _manager
    if _manager is None:
        _manager = MemoryManager()
    return _manager


@mcp.tool()
async def hafizaya_yaz(
    konu: str = Field(..., description="Anının başlığı (kısa, açıklayıcı)"),
    bilgi: str = Field(..., description="Kaydedilecek bilginin tamamı"),
    oda: str | None = Field(None, description="Oda (opsiyonel, boş bırakılırsa otomatik belirlenir)", json_schema_extra={"enum": ["mimari", "guvenlik", "donanim", "ogrenme", "kisisel", "genel"]}),
    importance: float = Field(7.0, description="Önem skoru 1-10 (varsayılan: 7)"),
    agent_id: str = Field("user", description="Yazan ajan kimliği (opsiyonel, varsayılan: user)")
) -> str:
    """Bir bilgiyi Zihin Sarayı'na akıllıca kaydet. Otomatik sınıflandırma, upsert ve entity çıkarımı yapar."""
    mgr = get_manager()
    result = await mgr.add_memory(konu=konu, bilgi=bilgi, oda=oda, agent_id=agent_id, importance=importance)
    return result.get("message", json.dumps(result, ensure_ascii=False))


@mcp.tool()
async def hafizada_ara(
    sorgu: str = Field(..., description="Arama sorgusu"),
    sonuc_sayisi: int = Field(3, description="Kaç sonuç dönsün (varsayılan: 3)"),
    oda: str | None = Field(None, description="Belirli bir odada ara (opsiyonel)")
) -> str:
    """Zihin Sarayı'nda semantik arama yap. Öneme ve benzerliğe göre sıralı sonuçlar döner."""
    mgr = get_manager()
    results = await asyncio.to_thread(mgr.search, query=sorgu, n=sonuc_sayisi, oda=oda)
    if not results:
        return "Bu konuda hafızada kayıt bulunamadı."
    
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['konu']} ({r['oda']}) — Benzerlik: {r['score']:.2f} | ID: {r['id']}")
        lines.append(f"    {r['content'][:300]}")
        if r.get("tags"):
            lines.append(f"    Etiketler: {', '.join(r['tags'])}")
    return "\n".join(lines)


@mcp.tool()
async def hafizayi_unut(
    memory_id: str = Field(..., description="Arşivlenecek anının ID'si")
) -> str:
    """Bir anıyı arşivle (tamamen silmez, sadece aktif görünümden kaldırır)."""
    mgr = get_manager()
    ok = await asyncio.to_thread(mgr.archive_memory, memory_id=memory_id)
    return "✅ Anı arşivlendi." if ok else "❌ Anı bulunamadı."


@mcp.tool()
async def profil_goster() -> str:
    """Kullanıcının hafıza profilini göster: oda dağılımı, en çok kullanılan etiketler."""
    mgr = get_manager()
    profile = await asyncio.to_thread(mgr.get_user_profile)
    lines = [
        f"Toplam Anı: {profile['total_memories']}",
        f"En Aktif Oda: {profile['most_active_room']}",
        f"Oda Dağılımı: {json.dumps(profile['rooms'], ensure_ascii=False)}",
        f"Öne Çıkan Etiketler: {', '.join(profile['top_tags'][:5]) or 'henüz yok'}",
    ]
    return "\n".join(lines)


@mcp.tool()
async def oda_listele() -> str:
    """Tüm hafıza odalarını ve içerdikleri anı sayısını listele."""
    mgr = get_manager()
    stats = await asyncio.to_thread(mgr.get_stats)
    lines = [f"{k}: {v} anı" for k, v in stats.items() if k != "total"]
    lines.append(f"\nToplam: {stats.get('total', 0)} anı")
    return "\n".join(lines)


@mcp.tool()
async def grafik_sorgula(
    varlik: str = Field(..., description="Sorgulanacak varlık adı")
) -> str:
    """Bir varlığın (kişi, kavram, teknoloji) knowledge graph bağlantılarını sorgula. Örnek: 'NixOS', 'xmrah', 'Hyprland'."""
    mgr = get_manager()
    data = await asyncio.to_thread(mgr.search_graph, entity_name=varlik)
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
    return "\n".join(lines)


@mcp.tool()
async def hafizayi_aktar() -> str:
    """Tüm aktif anıları JSON dosyasına kaydet (yedek/export). Dosya yolunu döndürür."""
    mgr = get_manager()
    path = await asyncio.to_thread(mgr.export_to_file)
    with open(path, encoding="utf-8") as f:
        count = len(json.load(f))
    return f"{count} anı dışa aktarıldı: {path}"


@mcp.tool()
async def oturum_ozetle(
    konusma: str = Field(..., description="Özetlenecek konuşma veya metin"),
    agent_id: str = Field("user", description="Yazan ajan kimliği (opsiyonel, varsayılan: user)")
) -> str:
    """Bir konuşma veya metin bloğundan önemli bilgileri çıkar ve hafızaya kaydet. Oturum biterken öğrenilenleri kalıcı hale getirmek için kullan."""
    mgr = get_manager()
    result = await mgr.summarize_and_save(conversation=konusma, agent_id=agent_id)
    lines = [result["message"]]
    if result["facts"]:
        lines.append("\nKaydedilen bilgiler:")
        for f in result["facts"]:
            lines.append(f"  - {f}")
    return "\n".join(lines)


@mcp.tool()
async def gecmise_bak(
    gun: int = Field(7, description="Kaç gün geriye bakılsın (varsayılan: 7)")
) -> str:
    """Son N günde hafızaya eklenen anıları listele. 'Bu hafta ne öğrendim?' veya 'Son 30 günde neler kaydetmişim?' sorularına cevap verir."""
    mgr = get_manager()
    memories = await asyncio.to_thread(mgr.get_memories_by_date, days=gun)
    if not memories:
        return f"Son {gun} günde eklenen anı bulunamadı."
    lines = [f"Son {gun} günde eklenen {len(memories)} anı:"]
    for m in memories:
        lines.append(f"\n[{m.oda.upper()}] {m.konu} (önem: {m.importance:.0f}/10)")
        lines.append(f"  {m.bilgi[:200]}")
        if m.tags:
            lines.append(f"  Etiketler: {', '.join(m.tags)}")
    return "\n".join(lines)


@mcp.tool()
async def hatirlat(
    adet: int = Field(5, description="Kaç hatırlatma dönsün (varsayılan: 5)")
) -> str:
    """Önemli ama uzun süredir hatırlatılmamış anıları göster. Öğrenme, görev ve karar takibi için proaktif hatırlatma."""
    mgr = get_manager()
    reminders = await asyncio.to_thread(mgr.get_reminders, n=adet)
    if not reminders:
        return "Hatırlatılacak anı bulunamadı."
    lines = ["Hatırlatılması gereken anılar (önem x unutulma):"]
    for r in reminders:
        lines.append(f"\n[{r['oda'].upper()}] {r['konu']} — {r['days_ago']} gün önce eklendi")
        lines.append(f"  {r['bilgi'][:200]}")
    return "\n".join(lines)
