#!/usr/bin/env bash

# Localmind MCP SSE Server — Open WebUI için
cd /home/xmrah/Projects/localmind

# NixOS'ta gerekli C kütüphanelerini ayarla (ChromaDB için)
NIX_GCC_LIB=$(find /nix/store -maxdepth 1 -type d -name "*-gcc-*-lib" ! -name "*i686*" ! -name "*lib32*" | head -1)/lib
NIX_ZLIB=$(find /nix/store -maxdepth 1 -type d -name "*-zlib-*" ! -name "*src*" ! -name "*dev*" | head -1)/lib
export LD_LIBRARY_PATH="${NIX_GCC_LIB}:${NIX_ZLIB}"
export LC_ALL=en_US.UTF-8
export ANONYMIZED_TELEMETRY=False

# SSE sunucusunu başlat (8001 portu)
exec .venv/bin/python server_http.py
