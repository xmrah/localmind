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

# Logları takip et
logs:
    journalctl -u localmind -f
