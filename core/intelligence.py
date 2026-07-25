"""
Localmind v2 — Intelligence Layer
Ollama LLM ile akıllı karar alma: sınıflandırma, entity çıkarımı, upsert kararı.
"""
import logging

import httpx

log = logging.getLogger("localmind.intelligence")

OLLAMA_BASE = "http://localhost:11434"

# Hız için küçük model, kalite için büyük model
FAST_MODEL  = "qwen2.5-coder:7b-instruct-q6_K"   # Sınıflandırma, upsert kararı
SMART_MODEL = "gemma4:26b"                         # Entity çıkarımı — 26B MoE'nin derin anlam gücü
CONV_MODEL  = "local/qwen3-14b:latest"             # Konuşma özetleme — Türkçe multilingual


async def _ollama_generate(prompt: str, model: str = FAST_MODEL) -> str:
    """Ollama'ya istek gönder, saf metin döndür."""
    try:
        if model == SMART_MODEL:
            timeout = 120.0
        elif model == CONV_MODEL:
            timeout = 90.0
        else:
            timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
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
    Döndürür: {"action": "create|update|skip", "existing_id": str|None, "conflict_ids": list[str], "reason": str}
    """
    if not existing_memories:
        return {"action": "create", "existing_id": None, "conflict_ids": [], "reason": "Benzer anı yok"}

    # Tüm benzer anıları listeye al
    existing_list = "\n".join([
        f"[{i+1}] ID:{m.get('id','')} Konu:{m.get('konu','')} Bilgi:{m.get('bilgi', m.get('content',''))[:150]}"
        for i, m in enumerate(existing_memories)
    ])

    prompt = f"""Yeni bilgiyi mevcut anılarla karşılaştır.

MEVCUT ANILAR:
{existing_list}

YENİ BİLGİ:
Konu: {new_konu}
Bilgi: {new_bilgi[:300]}

Görev:
1. Ne yapılmalı? (update/create/skip)
   - update: Yeni bilgi en yakın anıyı güncelliyor
   - create: Yeni ve farklı bir bilgi
   - skip: Zaten var olan bilgi
2. Hangi anılar artık geçersiz/çelişiyor? (varsa numaralarını yaz, yoksa hiçbiri)

Format (sadece bu iki satırı yaz):
KARAR: update|create|skip [güncelliyorsa: ID:...]
ÇAKIŞAN: 1,2 | hiçbiri"""

    result = await _ollama_generate(prompt, FAST_MODEL)
    action = "create"
    existing_id = None
    conflict_ids = []

    for line in result.strip().split("\n"):
        line = line.strip()
        if line.upper().startswith("KARAR:"):
            parts = line[6:].strip().split()
            if parts:
                action = parts[0].lower()
                if action not in {"update", "create", "skip"}:
                    action = "create"
                # ID: varsa çıkar
                for p in parts[1:]:
                    if p.upper().startswith("ID:"):
                        existing_id = p[3:].strip()
        elif line.upper().startswith("ÇAKIŞAN:") or line.upper().startswith("CAKISAN:"):
            val = line.split(":", 1)[1].strip().lower()
            if val != "hiçbiri" and val != "hicbiri" and val:
                nums = [v.strip() for v in val.split(",") if v.strip().isdigit()]
                for n in nums:
                    idx = int(n) - 1
                    if 0 <= idx < len(existing_memories):
                        cid = existing_memories[idx].get("id")
                        if cid:
                            conflict_ids.append(cid)

    # update ise ve ID bulunamadıysa en yakını kullan
    if action == "update" and not existing_id:
        existing_id = existing_memories[0].get("id")

    # update edilen anı conflict listesinde olmamalı
    if existing_id and existing_id in conflict_ids:
        conflict_ids.remove(existing_id)

    return {
        "action": action,
        "existing_id": existing_id if action == "update" else None,
        "conflict_ids": conflict_ids,
        "reason": f"LLM kararı: {action}"
    }


async def summarize_conversation(conversation: str) -> list[dict]:
    """
    Bir konuşma metninden kalıcı öğrenilecek bilgileri çıkar.
    Döndürür: [{"konu": str, "bilgi": str, "importance": float}]
    """
    prompt = f"""Aşağıdaki konuşmadan kalıcı olarak hatırlanması gereken bilgileri çıkar.
Geçici sorular, selamlaşmalar ve sohbet akışını YAZMA.
Sadece öğrenilen gerçekler, tercihler, kararlar ve önemli bağlamı yaz.

Her bilgi için şu formatı kullan:
KONU: <kısa başlık (max 8 kelime)>
BİLGİ: <öğrenilen bilgi>
ÖNEM: <1-10>
---

Konuşma:
{conversation[:3000]}

Çıkarılan bilgiler:"""

    result = await _ollama_generate(prompt, CONV_MODEL)
    facts = []
    current: dict = {}

    for line in result.strip().split("\n"):
        line = line.strip()
        if line.upper().startswith("KONU:"):
            current["konu"] = line[5:].strip()
        elif line.upper().startswith("BİLGİ:") or line.upper().startswith("BILGI:"):
            current["bilgi"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("ÖNEM:") or line.upper().startswith("ONEM:"):
            try:
                current["importance"] = float(line.split(":", 1)[1].strip().split()[0])
            except Exception:
                current["importance"] = 7.0
        elif line == "---":
            if "konu" in current and "bilgi" in current:
                facts.append({
                    "konu": current["konu"],
                    "bilgi": current["bilgi"],
                    "importance": current.get("importance", 7.0)
                })
            current = {}

    if "konu" in current and "bilgi" in current:
        facts.append({
            "konu": current["konu"],
            "bilgi": current["bilgi"],
            "importance": current.get("importance", 7.0)
        })

    return facts[:10]


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
