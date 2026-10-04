# 1. NixOS Flakes İle Tekrarlanabilir Geliştirme Ortamı

Tarih: 2026-05-01

## Durum
Kabul Edildi (Accepted)

## Bağlam
ChromaDB ve SQLite gibi yerel veritabanları Python üzerinden çalışırken arka planda derlenmiş C kütüphanelerine (`libstdc++.so.6`, `libz.so.1`) ihtiyaç duyar. Standart Linux dağıtımlarında `pip install` yapmak bu yüzden sürekli C-Extension çökmelerine veya sistem kütüphanesi çakışmalarına (Dependency Hell) yol açar. Geliştirme ortamının hangi makinede çalıştırılırsa çalıştırılsın %100 aynı tepkiyi vermesi gerekiyordu.

## Karar
Sistemin geliştirme ortamını ve bağımlılık izolasyonunu sağlamak için **NixOS Flakes** (`flake.nix`) benimsenmiştir. Proje klasöründe çalıştırılan `run_mcp.sh` ve `run_mcp_sse.sh` betikleri, Nix'in izole deposundaki (`/nix/store`) doğru `gcc` ve `zlib` kütüphanelerini bularak `LD_LIBRARY_PATH` değişkenini dinamik olarak ezer.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Mutlak Tekrarlanabilirlik:** Proje 5 yıl sonra başka bir NixOS makinesinde açılsa bile kütüphane çakışması yaşanmaz, doğrudan hatasız ayağa kalkar.
- **Sistem İzolasyonu:** Proje için kurulan hiçbir kütüphane ana makinenin sistem dosyalarını kirletmez.

**Eksileri:**
- **Sadece NixOS Desteği:** Projenin bu şekilde pürüzsüz çalışması Nix paket yöneticisine sıkı sıkıya bağlıdır. Ubuntu veya Windows üzerinde ayağa kaldırmak isteyenler için ekstra Dockerize işlemi gerekebilir.
- **Nix Öğrenme Eğrisi:** `flake.nix` ve Bash betikleri içindeki Nix store path manipülasyonlarını anlamak yeni geliştiriciler için zorlayıcıdır.
