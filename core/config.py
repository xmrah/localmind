"""
Localmind v2 — Merkezi Yapılandırma Yönetimi (Config Engine)
Ayarlar config.json dosyasında kalıcı olarak saklanır ve çalışma anında dinamik okunur.
"""
import json
import logging
import os
from typing import Any

log = logging.getLogger("localmind.config")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

DEFAULT_CONFIG: dict[str, Any] = {
    "fast_model": "qwen2.5-coder:7b",
    "smart_model": "huihui_ai/gemma-4-abliterated:26b",
    "conv_model": "huihui_ai/Qwen3.6-abliterated:27b",
    "decay_factor": 0.99,
    "ollama_base": "http://localhost:11434",
    "auto_archive_conflicts": True
}


def get_config() -> dict[str, Any]:
    """Mevcut yapılandırmayı oku. Dosya yoksa varsayılanı oluşturup kaydet."""
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Eksik alanlar varsa varsayılanla tamamla
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception as e:
        log.warning(f"Config okuma hatası, varsayılan kullanılıyor: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(new_cfg: dict[str, Any]) -> dict[str, Any]:
    """Yeni ayarları config.json dosyasına atomik ve kalıcı olarak yaz."""
    current = get_config() if os.path.exists(CONFIG_PATH) else DEFAULT_CONFIG.copy()
    current.update(new_cfg)

    # Değer kontrolleri
    if "decay_factor" in current:
        try:
            current["decay_factor"] = max(0.80, min(1.0, float(current["decay_factor"])))
        except (ValueError, TypeError):
            current["decay_factor"] = 0.99

    try:
        temp_path = f"{CONFIG_PATH}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, CONFIG_PATH)
        log.info(f"Yapılandırma güncellendi: {current}")
        return current
    except Exception as e:
        log.error(f"Config kaydetme hatası: {e}")
        raise
