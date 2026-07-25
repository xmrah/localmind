#!/usr/bin/env bash

# Hata ayıklama için tüm stderr çıktılarını log dosyasına yaz
exec 2> /home/xmrah/Projects/localmind/mcp_debug.log

# Localmind MCP Server — Antigravity/IDE entegrasyonu için
# nix print-dev-env KULLANILMIYOR — doğrudan LD_LIBRARY_PATH ile hızlı başlatma

cd /home/xmrah/Projects/localmind

# NixOS'ta gerekli C kütüphanelerini ayarla (ChromaDB için)
NIX_GCC_LIB=$(find /nix/store -maxdepth 1 -type d -name "*-gcc-*-lib" ! -name "*i686*" ! -name "*lib32*" | head -1)/lib
NIX_ZLIB=$(find /nix/store -maxdepth 1 -type d -name "*-zlib-*" ! -name "*src*" ! -name "*dev*" | head -1)/lib
export LD_LIBRARY_PATH="${NIX_GCC_LIB}:${NIX_ZLIB}"
export LC_ALL=en_US.UTF-8
export ANONYMIZED_TELEMETRY=False

# FastMCP loglarını sustur
export FASTMCP_LOG_LEVEL=ERROR
export LOG_LEVEL=ERROR

# MCP sunucusunu başlat (stdio)
exec .venv/bin/python server.py
