"""
Localmind - Hafıza Düzenleme, Çöp Temizleme ve Loci Hiyerarşi İyileştirme Betiği
"""
import os
import json
import sqlite3
from core.memory_manager import MemoryManager, GRAPH_DB_PATH

def run_cleanup():
    mm = MemoryManager()
    total_before = mm.collection.count()
    print(f"Başlangıç toplam kayıt: {total_before}")
    
    # ----------------------------------------------------
    # 1. Çöp ve Test Kayıtlarını Silme
    # ----------------------------------------------------
    to_delete = [
        "a79014f8",  # test anı 1 (vs vs vs...)
        "15bd0f24",  # İlk Test Anısı (fastmcp test)
        "e19def09",  # Flake Lock Deduplication (mükerrer kopya)
    ]
    
    deleted_count = 0
    for mid in to_delete:
        if mm.delete_memory(mid):
            deleted_count += 1
            print(f"Silindi: {mid}")
            
    print(f"Toplam silinen çöp kayıt: {deleted_count}")
    
    # ----------------------------------------------------
    # 2. Xmarchy Odası ve Kalıntılarının Arşivlenmesi
    # ----------------------------------------------------
    data = mm.collection.get(include=["metadatas", "documents"])
    archived_xmarchy = 0
    
    for i, mid in enumerate(data["ids"]):
        meta = data["metadatas"][i]
        konu = meta.get("konu", "").lower()
        oda = meta.get("oda", "").lower()
        is_archived = meta.get("archived", "false") == "true"
        
        is_xmarchy = (oda == "xmarchy" or "xmarchy" in konu or "omarchy" in konu)
        
        if is_xmarchy and not is_archived:
            if mm.archive_memory(mid):
                archived_xmarchy += 1
                print(f"Arşivlendi (Xmarchy): [{mid[:8]}] {meta.get('konu')}")
                
    print(f"Arşivlenen Xmarchy kayıt sayısı: {archived_xmarchy}")
    
    # ----------------------------------------------------
    # 3. Loci Hiyerarşisi (Kanat ve Dolap) Düzenlemesi
    # ----------------------------------------------------
    # Yeniden tüm kayıtları çekip kanat/dolap güncelleyelim
    data = mm.collection.get(include=["metadatas", "documents"])
    updated_meta_count = 0
    
    for i, mid in enumerate(data["ids"]):
        meta = data["metadatas"][i]
        konu = meta.get("konu", "").lower()
        oda = meta.get("oda", "").lower()
        kanat = meta.get("kanat", "genel")
        dolap = meta.get("dolap", "genel")
        
        # Ajan kuralı kontrolü: kullanıcı "ajan kuralları kalsın" dedi
        if "parantez içi" in konu or "kodlama_kurallari" in dolap:
            new_kanat = "ajan"
            new_dolap = "kodlama_kurallari"
        elif oda == "xmarchy" or "xmarchy" in konu:
            new_kanat = "xmarchy"
            new_dolap = "arsiv"
        elif kanat not in ["genel", "", None]:
            # Zaten özel bir kanadı var (örn: enyxma, labs)
            new_kanat = kanat
            new_dolap = dolap if dolap not in ["genel", "", None] else "sistem"
        elif "localmind" in konu or "fastmcp" in konu:
            new_kanat = "localmind"
            new_dolap = "dashboard" if "dashboard" in konu else "cekirdek"
        elif any(k in konu for k in ["astro", "cloudflare pages", "hostinger", "xmrah.com", "pagefind"]):
            new_kanat = "xmrah.com"
            new_dolap = "web"
        elif any(k in konu for k in ["hyprland", "uwsm", "quickshell", "swaync", "cliphist", "matugen"]):
            new_kanat = "nixos-hyprland-lua"
            if "quickshell" in konu:
                new_dolap = "quickshell"
            elif "uwsm" in konu:
                new_dolap = "uwsm"
            else:
                new_dolap = "wm"
        elif any(k in konu for k in ["rdr2", "felsefe", "gelecek planları"]):
            new_kanat = "kisisel"
            new_dolap = "oyun" if "rdr2" in konu else "felsefe"
        elif any(k in konu for k in ["oturum_ozetle", "iş akışları"]):
            new_kanat = "ajan"
            new_dolap = "is_akislari"
        else:
            # Standart nixos-config
            new_kanat = "nixos-config"
            if oda == "guvenlik" or any(k in konu for k in ["audit", "firejail", "sops", "guvenlik", "cve", "izin", "hardening"]):
                new_dolap = "guvenlik"
            elif oda == "donanim" or any(k in konu for k in ["gpu", "vram", "ddc", "bluetooth", "donanım", "hardware"]):
                new_dolap = "donanim"
            elif any(k in konu for k in ["tailscale", "byedpi", "wifi", "iwd", "ağ", "internet", "ttl"]):
                new_dolap = "ag"
            elif any(k in konu for k in ["ollama", "searxng", "portainer", "docker", "ai stack"]):
                new_dolap = "servisler"
            elif any(k in konu for k in ["chromium", "chrome", "tarayıcı"]):
                new_dolap = "tarayici"
            elif any(k in konu for k in ["flake", "mkoutofstoresymlink", "justfile", "ssot"]):
                new_dolap = "flake"
            else:
                new_dolap = "sistem"
                
        # Değişiklik varsa güncelle
        if meta.get("kanat") != new_kanat or meta.get("dolap") != new_dolap:
            meta["kanat"] = new_kanat
            meta["dolap"] = new_dolap
            mm.collection.update(ids=[mid], metadatas=[meta])
            updated_meta_count += 1

    print(f"Kanat ve dolap hiyerarşisi güncellenen anı sayısı: {updated_meta_count}")
    
    # ----------------------------------------------------
    # Son Durum Özeti
    # ----------------------------------------------------
    counts = mm.get_memory_counts()
    print(f"\nİşlem Sonrası:")
    print(f"Toplam Anı: {mm.collection.count()}")
    print(f"Aktif: {counts['active']}, Arşiv: {counts['archived']}")

if __name__ == "__main__":
    run_cleanup()
