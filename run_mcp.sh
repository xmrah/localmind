#!/usr/bin/env bash

# NixOS ortamında IDE'nin (Antigravity) eksik C++ kütüphanelerini (libstdc++)
# bulabilmesi için özel olarak hazırlanmış köprü betiğidir.

cd /home/xmrah/Projects/localmind

# 1. Nix Flake ortam değişkenlerini yükle (Uyarıları gizleyerek)
eval "$(nix print-dev-env . 2>/dev/null)"

# 2. Python sanal ortamını (.venv) aktif et
source .venv/bin/activate

# 3. FastMCP gereksiz loglarını/ASCII logolarını tamamen sustur
export FASTMCP_LOG_LEVEL=ERROR
export LOG_LEVEL=ERROR

# 3. FastMCP sunucusunu başlat
exec python server.py
