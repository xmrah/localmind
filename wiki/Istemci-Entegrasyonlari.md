# İstemci Entegrasyonları Rehberi

Localmind, Model Context Protocol standardı üzerinden farklı yapay zeka arayüzleri ve geliştirme ortamları ile çalışır.

---

## 1. Antigravity IDE, Claude Desktop ve Continue

Bu istemciler standart girdi ve çıktı üzerinden haberleşir.

Yapılandırma dosyasındaki sunucu listesine ekleyin:

```json
{
  "mcpServers": {
    "localmind": {
      "command": "/bin/bash",
      "args": ["/home/KULLANICI/Projects/localmind/run_mcp.sh"]
    }
  }
}
```

---

## 2. Open-WebUI Entegrasyonu

Open-WebUI, HTTP üzerinden Server-Sent Events protokolüyle bağlantı kurar.

1. `localmind-mcp-sse.service` servisinin veya `python server_http.py` sürecinin çalıştığından emin olun.
2. Open-WebUI arayüzünde Yönetici Paneli > Ayarlar > Dış Araçlar sekmesini açın.
3. Yeni bağlantı ekleyin:
   * **Tür:** Streamable HTTP
   * **URL:** `http://127.0.0.1:8001/mcp`
   * **ID:** `localmind`
   * **Yetkilendirme:** Boş bırakın.

---

## 3. REST API Entegrasyonu

Dashboard sunucusu harici scriptler ve otomasyonlar için yerel REST uç noktaları sunar:

* `GET /api/memories`: Aktif anıların tam listesi.
* `GET /api/search?q=sorgu`: Hibrit anlamsal arama.
* `POST /api/memory`: Yeni anı ekleme.
* `POST /api/memory/archive`: Anı arşivleme.
* `DELETE /api/memory/{id}`: Anıyı kalıcı olarak silme.
* `GET /api/graph`: Bilgi grafiği düğüm ve bağlantı verileri.
