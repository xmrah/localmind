"""
Localmind v2 — stdio (Claude Desktop / Antigravity / Continue) Entrypoint
İş mantığı (tools.py) üzerinden çalışır. Stateless MCP uyumlu.
"""
from tools import mcp

if __name__ == "__main__":
    mcp.run()
