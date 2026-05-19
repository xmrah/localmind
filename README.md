# 🧠 Localmind v2 — Zihin Sarayı

**"Dijital İkinci Beyin — Tamamen Yerel, Tamamen Senin"**

Localmind, bilgilerin sadece depolanmadığı, aynı zamanda **anlamlandırıldığı**, **sınıflandırıldığı**, **ilişkilendirildiği** ve gerçek zamanlı olarak izlenebildiği bir **AI destekli Dijital Hafıza Yönetim Sistemi**dir.

Tüm veriler yerel makinenizde kalır. İnternet'e bir byte bile çıkmaz.

---

## 🚀 Temel Özellikler

### Semantik Hafıza
Bilgiler düz metin olarak değil, **vektör temsilcileri (embedding)** olarak saklanır. Arama yaparken kelime eşleşmesi değil, **anlam benzerliği** kullanılır. "GPU sorunları" diye ararsanız "ekran kartı problemleri" başlığındaki anıları da bulur.

### Akıllı Upsert (Tekrar Algılama)
Her yeni bilgi eklenirken Ollama, mevcut anılarla karşılaştırma yapar ve üç karardan birini verir:
- **`create`** — Tamamen yeni bilgi, kaydet
- **`update`** — Mevcut bir anının güncellemesi, eskisini güncelle
- **`skip`** — Zaten biliyor, eklemeye gerek yok

### Knowledge Graph (Bilgi Ağı)
Her anıdan **varlıklar (entity)** ve aralarındaki **ilişkiler (relation)** otomatik olarak çıkarılır ve SQLite tabanlı bir grafik veritabanında (`graph.db`) saklanır. Örnek:
```
xmrah | KULLANIR | NixOS
NixOS | KURULU_OLDUĞU | AMD Ryzen 5 7500F
POCO X6 Pro | ÇALIŞTIRIR | Android 16
```

### Otomatik Sınıflandırma
Eklenen her bilgi, Ollama tarafından analiz edilerek 6 odadan birine atanır:
`mimari` · `guvenlik` · `donanim` · `ogrenme` · `kisisel` · `genel`

Ollama erişilemezse kural tabanlı (keyword) fallback devreye girer.

### Otomatik Etiketleme
Her anıya Ollama üzerinden 3-5 adet bağlamsal etiket (Türkçe/İngilizce) otomatik üretilir.

### Zaman Aşımı Skoru (Importance Decay)
Ebbinghaus unutma eğrisinden esinlenerek:
- Eski anıların önemi zamanla düşer (`0.99^gün`)
- Her erişimde önem skoru `+0.5` artarak "hatırlanan" anılar güçlenir
- Arama sonuçları bu hibrit skora göre sıralanır (`%60 benzerlik + %40 önem`)

### Canlı Nabız (Live Pulse)
SSE (Server-Sent Events) ile dashboard hiçbir yenileme gerektirmeden anlık veri akışı alır.

### MCP Entegrasyonu (Model Context Protocol)
İki farklı MCP sunucusu ile AI araçlarına doğrudan bağlanır:
- **stdio** — Antigravity IDE ve VSCodium Continue eklentisi (`server.py`)
- **HTTP/SSE** — Open WebUI (`mcp_sse_server.py`)

### Obsidian-Style Graph View
D3.js ile oluşturulmuş interaktif bilgi ağı. Tıklanan anı parlar, ilgisiz düğümler silikleşir (Focus Mode). Hem semantik benzerlik bağları hem de entity ilişkileri tek grafikte görselleştirilir.

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
| :--- | :--- |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) (Python) |
| **AI Engine** | [Ollama](https://github.com/ollama/ollama) (Yerel LLM) |
| **Vektör DB** | [ChromaDB](https://www.trychroma.com/) (Cosine Similarity) |
| **Graph DB** | SQLite (Entity-Relation) |
| **Frontend** | Vanilla JS + D3.js, HTML5, CSS3 |
| **İletişim** | MCP (stdio + SSE), REST API, SSE |
| **Ortam** | [Nix Flakes](https://nixos.org/) |

---

## 🏗️ Proje Yapısı

```text
.
├── core/                    # Sistemin beyni
│   ├── intelligence.py      # Ollama etkileşimleri (sınıflandırma, upsert kararı, entity çıkarımı, etiketleme)
│   ├── memory_manager.py    # ChromaDB + SQLite yönetimi, akıllı upsert, graph, decay skoru
│   └── models.py            # Pydantic veri şemaları (Memory, Entity, Relation, SearchResult)
│
├── dashboard/               # Kullanıcı arayüzü
│   ├── index.html           # Ana panel
│   ├── main.js              # API, SSE ve D3.js Graph View etkileşimi
│   └── style.css            # Glassmorphism temalı modern tasarım
│
├── server.py                # MCP stdio sunucusu (Antigravity/Continue IDE entegrasyonu)
├── server_sse.py            # Ana HTTP API sunucusu (FastAPI + SSE + Dashboard)
├── mcp_sse_server.py        # MCP HTTP/SSE köprüsü (Open WebUI entegrasyonu)
│
├── run_mcp.sh               # stdio MCP sunucusunu başlatma scripti
├── run_mcp_sse.sh           # SSE MCP sunucusunu başlatma scripti
│
├── chroma_db/               # ChromaDB vektör veritabanı (kalıcı)
├── graph.db                 # SQLite entity-relation veritabanı
└── flake.nix                # Nix Flakes — izole geliştirme ortamı
```

---

## 🔌 API Referansı

### Durum ve İstatistik
| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Sistem durumu, Ollama bağlantısı ve toplam anı sayısı |
| `GET` | `/api/stats` | Oda bazlı istatistikler |
| `GET` | `/api/profile` | Kullanıcı profili: oda dağılımı, en aktif oda, öne çıkan etiketler |

### Hafıza İşlemleri
| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `POST` | `/api/memory` | Akıllı hafıza ekleme (otomatik sınıflandırma + upsert + entity çıkarımı + etiketleme) |
| `GET` | `/api/search?q=...&oda=...&n=5` | Semantik arama (importance decay skoru ile sıralı) |
| `POST` | `/api/memory/archive` | Anıyı arşivle (silmez, aktif görünümden kaldırır) |

### Oda ve Graph
| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/rooms` | Tüm odalar ve doluluk oranları |
| `GET` | `/api/room/{oda}` | Belirli bir odanın tüm anıları |
| `GET` | `/api/graph` | D3.js için tam grafik verisi (semantik bağlar + entity ilişkileri) |

### Canlı Akış
| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/events` | SSE üzerinden anlık nabız (5sn aralıkla toplam anı sayısı) |

### MCP Araçları (Tool Calling)
`server.py` (stdio) ve `mcp_sse_server.py` (HTTP/SSE) üzerinden sunulan araçlar:

| Araç | Açıklama |
| :--- | :--- |
| `hafizaya_yaz` | Bilgiyi akıllıca kaydet (upsert + sınıflandırma + entity çıkarımı) |
| `hafizada_ara` | Semantik arama yap |
| `hafizayi_unut` | Anıyı arşivle |
| `profil_goster` | Kullanıcı hafıza profilini göster |
| `oda_listele` | Tüm odaları ve anı sayılarını listele |

---

## ⚙️ Kurulum ve Çalıştırma

### Ön Gereksinimler
- **Ollama** kurulu ve çalışıyor olmalı
- **Nix** (opsiyonel ama NixOS'ta zorunlu)

### 1. Projeyi Klonla
```bash
# Codeberg
git clone https://codeberg.org/xmrah/localmind.git

# veya GitHub
git clone https://github.com/xmrah/localmind.git

cd localmind
```

### 2. Nix Ortamını Aç (NixOS)
```bash
nix develop   # flake.nix ile izole Python + C kütüphaneleri
pip install fastmcp chromadb httpx pydantic uvicorn
```

### 3. Dashboard + API Sunucusunu Başlat
```bash
./run_mcp_sse.sh         # Port 8001: MCP SSE (Open WebUI için)
# VEYA
python server_sse.py     # Port 8000: Dashboard + REST API + SSE
```

### 4. Kullanım
- **Dashboard:** [http://localhost:8000](http://localhost:8000)
- **MCP SSE (Open WebUI):** Port 8001 üzerinden bağlanır

### 5. IDE Entegrasyonu (Antigravity / VSCodium Continue)
`~/.continue/config.json` içinde:
```json
{
  "mcpServers": [
    {
      "name": "localmind",
      "command": "bash",
      "args": ["/path/to/localmind/run_mcp.sh"]
    }
  ]
}
```

---

## 🏠 NixOS Entegrasyonu

Localmind, NixOS üzerinde `systemd` servisi olarak 7/24 çalışır:
- `localmind.service` → Dashboard + API (port 8000)
- `localmind-mcp-sse.service` → MCP SSE köprüsü (port 8001)
- `ai-toggle start/stop` komutuyla tüm AI servisleriyle birlikte yönetilir

---

## 📝 Lisans
Bu proje kişisel kullanım ve geliştirme amaçlıdır.
