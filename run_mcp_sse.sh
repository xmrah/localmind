#!/usr/bin/env bash

# Localmind MCP SSE Server — Open WebUI için
cd /home/xmrah/Projects/localmind

# NixOS'ta gerekli C kütüphanelerini ayarla (ChromaDB için)
NIX_GCC_LIB=$(echo /nix/store/*-gcc-*-lib/lib | tr ' ' '\n' | head -1)
NIX_ZLIB=$(echo /nix/store/*-zlib-*/lib | tr ' ' '\n' | grep -v src | head -1)
export LD_LIBRARY_PATH="${NIX_GCC_LIB}:${NIX_ZLIB}"
export LC_ALL=en_US.UTF-8
export ANONYMIZED_TELEMETRY=False

# SSE sunucusunu başlat (8001 portu)
exec .venv/bin/python mcp_sse_server.py
