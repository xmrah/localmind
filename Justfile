# localmind - MCP Hafıza Sunucusu Yönetim Paneli
# Author: xmrah

# Varsayılan yardım menüsü
default:
    @just --list

# Tüm değişiklikleri Codeberg + GitHub'a gönder
sync message="update":
    git add .
    git commit -m "feat(localmind): {{message}} - $(date +'%Y-%m-%d %H:%M')" || echo "Değişiklik yok."
    git push

# MCP stdio sunucusunu başlat
start:
    ./run_mcp.sh

# Dashboard + REST API sunucusunu başlat
dashboard:
    python server_sse.py

# Servisleri yeniden başlat (systemd)
restart:
    sudo systemctl restart localmind localmind-mcp-sse

# Servis durumlarını kontrol et
status:
    systemctl status localmind localmind-mcp-sse

# Logları takip et
logs:
    journalctl -u localmind -f

# Wiki dokümantasyonunu Codeberg Wiki reposuna gönder
wiki-push:
    @bash -c 'T=$$(mktemp -d); git clone git@codeberg.org:xmrah/localmind.wiki.git "$$T" && cp -r wiki/* "$$T/" && cd "$$T" && git add . && (git commit -m "docs(wiki): sync wiki - $$(date +"%Y-%m-%d %H:%M")" || echo "Değişiklik yok") && git push origin main; rm -rf "$$T"'
