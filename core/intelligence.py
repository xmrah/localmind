"""
Localmind v2 — Intelligence Layer
Ollama LLM ile akıllı karar alma: sınıflandırma, entity çıkarımı, upsert kararı.
"""
import json
import httpx
import logging
from typing import Optional

log = logging.getLogger("localmind.intelligence")

OLLAMA_BASE = "http://localhost:11434"

# Hız için küçük model, kalite için büyük model
FAST_MODEL  = "qwen2.5-coder:7b-instruct-q6_K"   # Sınıflandırma, upsert kararı
SMART_MODEL = "qwen2.5-coder:7b-instruct-q6_K"   # Entity çıkarımı (şimdilik aynı, ileride qwen3-14b)


async def _ollama_generate(prompt: str, model: str = FAST_MODEL) -> str:
    """Ollama'ya istek gönder, saf metin döndür."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}}
            )
            res.raise_for_status()
            return res.json().get("response", "").strip()
    except Exception as e:
        log.warning(f"Ollama bağlantı hatası ({model}): {e}")
        return ""


async def classify_room(konu: str, bilgi: str) -> str:
    """
    Verilen bilginin hangi odaya ait olduğuna karar ver.
    Ollama başarısız olursa kural tabanlı fallback devreye girer.
    """
    prompt = f"""Sen bir bilgi sınıflandırma asistanısın. Aşağıdaki bilgiyi tek bir kategori ismiyle sınıflandır.

Kategoriler:
- mimari: sistem tasarımı, altyapı, yazılım mimarisi, NixOS, sunucu yapılandırması
- guvenlik: güvenlik, şifreleme, VPN, Tailscale, gizlilik politikaları
- donanim: bilgisayar, telefon, GPU, CPU, ekran, fiziksel cihazlar
- ogrenme: öğrenme hedefleri, kurslar, kitaplar, yeni kavramlar
- kisisel: kişisel tercihler, rutinler, hedefler, alışkanlıklar
- genel: yukarıdakilere uymayan her şey

Konu: {konu}
Bilgi: {bilgi[:200]}

Sadece kategori adını yaz, başka hiçbir şey yazma:"""

    result = await _ollama_generate(prompt, FAST_MODEL)
    result = result.lower().strip().split()[0] if result else ""

    # Geçerli bir kategori mi?
    valid = {"mimari", "guvenlik", "donanim", "ogrenme", "kisisel", "genel"}
    if result in valid:
        return result

    # Fallback: anahtar kelime tabanlı
    text = (konu + " " + bilgi).lower()
    if any(k in text for k in ["nix", "server", "api", "docker", "mimari", "architecture"]):
        return "mimari"
    if any(k in text for k in ["güvenlik", "security", "vpn", "tailscale", "şifre"]):
        return "guvenlik"
    if any(k in text for k in ["telefon", "phone", "gpu", "cpu", "ram", "ekran", "cihaz", "poco", "android"]):
        return "donanim"
    if any(k in text for k in ["öğren", "learn", "kurs", "kitap", "hedef"]):
        return "ogrenme"
    return "genel"


async def decide_upsert(new_konu: str, new_bilgi: str, existing_memories: list[dict]) -> dict:
    """
    Yeni bilgi mevcut anılarla çelişiyor mu, tamamlıyor mu, yoksa tamamen yeni mi?
    Döndürür: {"action": "create|update|skip", "existing_id": str|None, "reason": str}
    """
    if not existing_memories:
        return {"action": "create", "existing_id": None, "reason": "Benzer anı yok"}

    # En yakın anıyı al
    closest = existing_memories[0]
    prompt = f"""İki bilgiyi karşılaştır ve ne yapılması gerektiğine karar ver.

MEVCUT ANI:
Konu: {closest.get('konu', '')}
Bilgi: {closest.get('bilgi', closest.get('content', ''))[:300]}

YENİ BİLGİ:
Konu: {new_konu}
Bilgi: {new_bilgi[:300]}

Seçenekler:
- "update": Yeni bilgi eskisini güncelliyor veya tamamlıyor (aynı konuda daha güncel bilgi)
- "create": Tamamen farklı bir konu, yeni kayıt oluştur
- "skip": Neredeyse aynı bilgi, eklemeye gerek yok

Sadece seçenek adını yaz (update/create/skip):"""

    result = await _ollama_generate(prompt, FAST_MODEL)
    action = result.lower().strip().split()[0] if result else "create"

    if action not in {"update", "create", "skip"}:
        action = "create"

    return {
        "action": action,
        "existing_id": closest.get("id") if action == "update" else None,
        "reason": f"LLM kararı: {action}"
    }


async def extract_entities(konu: str, bilgi: str) -> list[dict]:
    """
    Metinden entity'leri ve ilişkileri çıkar.
    Döndürür: [{"source": str, "relation": str, "target": str}]
    """
    prompt = f"""Aşağıdaki metinden varlıklar ve aralarındaki ilişkileri çıkar.

Metin: "{konu}: {bilgi[:400]}"

Her satıra bir ilişki yaz, format: VARLIK1 | İLİŞKİ | VARLIK2
Örnek:
xmrah | KULLANIR | NixOS
POCO X6 Pro | ÇALIŞTIRIR | Android 16
NixOS | KURULU_OLDUĞU | AMD Ryzen 5 7500F

Sadece kesin ilişkileri yaz, tahmin etme. Eğer ilişki yoksa boş bırak:"""

    result = await _ollama_generate(prompt, SMART_MODEL)
    relations = []

    for line in result.strip().split("\n"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 3 and all(parts):
            relations.append({
                "source": parts[0],
                "relation": parts[1],
                "target": parts[2]
            })

    return relations[:10]  # Max 10 ilişki


async def generate_tags(konu: str, bilgi: str) -> list[str]:
    """Anı için otomatik etiket oluştur."""
    prompt = f"""Aşağıdaki bilgi için 3-5 adet kısa etiket üret. Küçük harf, Türkçe veya İngilizce.

Konu: {konu}
Bilgi: {bilgi[:200]}

Sadece etiketleri virgülle ayırarak yaz:"""

    result = await _ollama_generate(prompt, FAST_MODEL)
    if not result:
        return []
    return [t.strip().lower() for t in result.split(",") if t.strip()][:5]


async def is_ollama_available() -> bool:
    """Ollama servisinin çalışıp çalışmadığını kontrol et."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"{OLLAMA_BASE}/api/tags")
            return res.status_code == 200
    except Exception:
        return False
