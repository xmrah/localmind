#!/usr/bin/env bash

# Localmind MCP Server — Antigravity/IDE entegrasyonu için
# nix print-dev-env KULLANILMIYOR — doğrudan LD_LIBRARY_PATH ile hızlı başlatma

cd /home/xmrah/Projects/localmind

# NixOS'ta gerekli C kütüphanelerini ayarla (ChromaDB için)
NIX_GCC_LIB=$(echo /nix/store/*-gcc-*-lib/lib | tr ' ' '\n' | head -1)
NIX_ZLIB=$(echo /nix/store/*-zlib-*/lib | tr ' ' '\n' | grep -v src | head -1)
export LD_LIBRARY_PATH="${NIX_GCC_LIB}:${NIX_ZLIB}"
export LC_ALL=en_US.UTF-8
export ANONYMIZED_TELEMETRY=False

# FastMCP loglarını sustur
export FASTMCP_LOG_LEVEL=ERROR
export LOG_LEVEL=ERROR

# MCP sunucusunu başlat (stdio)
exec .venv/bin/python server.py
