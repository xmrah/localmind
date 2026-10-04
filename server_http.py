"""
Localmind v2 — SSE (Open-WebUI) Entrypoint
İş mantığı (tools.py) üzerinden çalışır. Stateless MCP uyumlu.
"""
from tools import mcp

if __name__ == "__main__":
    # FastMCP'nin yeni stateless (durumsuz) taşıyıcısı
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
