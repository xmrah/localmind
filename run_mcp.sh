#!/usr/bin/env bash

# NixOS ortamında IDE'nin (Antigravity) eksik C++ kütüphanelerini (libstdc++)
# bulabilmesi için özel olarak hazırlanmış köprü betiğidir.

cd /home/xmrah/Projects/xPalace

# 1. Nix Flake ortam değişkenlerini (LD_LIBRARY_PATH dahil) sisteme yükle
eval "$(nix print-dev-env .)"

# 2. Python sanal ortamını (.venv) aktif et
source .venv/bin/activate

# 3. FastMCP sunucusunu başlat
exec python server.py
