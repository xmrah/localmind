# 🧠 Localmind v2 — Zihin Sarayı

**"Dijital İkinci Beyin — Tamamen Yerel, Tamamen Senin"**

Localmind, bilgilerin sadece depolanmadığı, aynı zamanda **anlamlandırıldığı**, **sınıflandırıldığı**, **ilişkilendirildiği** ve gerçek zamanlı olarak izlenebildiği, **FastMCP destekli Dijital Hafıza Yönetim Sistemi**dir. 

Tüm veriler yerel makinenizde kalır. İnternet'e bir byte bile çıkmaz. **Temmuz 2026 standartlarına uygun Stateless (Durumsuz) mimari** üzerine inşa edilmiştir.

---

## 🚀 Öne Çıkan Özellikler

### ⚡ Stateless MCP (Model Context Protocol) Mimarisi
Eski stateful mimarilerden farklı olarak Localmind, **FastMCP** kullanarak tamamen durumsuz çalışır:
- **`server.py` (Stdio):** Antigravity IDE, Claude Desktop ve VSCodium Continue entegrasyonu.
- **`server_http.py` (Streamable-HTTP):** Open-WebUI gibi modern yapay zeka istemcileri için güvenli, yüksek performanslı HTTP transport arayüzü.

### 🧠 Semantik Hafıza ve Akıllı Upsert
Bilgiler düz metin olarak değil, vektör temsilcileri (embedding) olarak saklanır. Arama yaparken kelime eşleşmesi değil, **anlam benzerliği** kullanılır.
Her yeni bilgi eklenirken Ollama mevcut anılarla karşılaştırma yapar: `create` (yeni), `update` (güncelle) veya `skip` (zaten biliyor) kararı verir.

### 🕸️ Knowledge Graph (Bilgi Ağı)
Her anıdan **varlıklar (entity)** ve aralarındaki **ilişkiler (relation)** otomatik olarak çıkarılır ve SQLite tabanlı bir grafik veritabanında saklanır. 

### 🏷️ Otomatik Sınıflandırma ve Etiketleme
Eklenen her bilgi, Ollama tarafından analiz edilerek 6 odadan birine atanır (`mimari`, `guvenlik`, `donanim`, `ogrenme`, `kisisel`, `genel`) ve bağlamsal etiketler üretilir.

### ⏳ Zaman Aşımı Skoru (Ebbinghaus Decay)
Eski anıların önemi zamanla düşer, ancak her erişimde önem skoru artarak "hatırlanan" anılar güçlenir. Arama sonuçları hibrit bir skorla (%60 benzerlik + %40 önem) sıralanır.

### 📊 Dashboard (6 Sayfa)
Vanilla JS ve D3.js ile geliştirilen modern, Glassmorphism temalı kontrol paneli üzerinden Timeline, Analytics ve Canlı Zihin Haritası (Graph) görüntülenebilir.

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji | Açıklama |
| :--- | :--- | :--- |
| **MCP Engine** | [FastMCP](https://github.com/jlowin/fastmcp) | Stateless arayüz, Pydantic şema doğrulaması |
| **AI Engine** | [Ollama](https://github.com/ollama/ollama) | Yerel LLM işlemleri ve Sınıflandırma |
| **Vektör DB** | [ChromaDB](https://www.trychroma.com/) | Kosinüs benzerliği tabanlı semantik arama |
| **Graph DB** | SQLite | Entity-Relation ağı |
| **Ortam** | [Nix Flakes](https://nixos.org/) | İzole, bağımlılık krizlerinden arındırılmış geliştirme ortamı |

---

## 🏗️ Mimari Yapı

```text
.
├── core/                    # Sistemin beyni
│   ├── intelligence.py      # Ollama etkileşimleri (upsert, sınıflandırma, entity)
│   ├── memory_manager.py    # ChromaDB + SQLite yönetimi, async.to_thread I/O
│   └── models.py            # Pydantic veri şemaları
│
├── dashboard/               # Glassmorphism HTML/JS/CSS paneli
├── tools.py                 # (YENİ) Tüm FastMCP tool'larının DRY merkez üssü
│
├── server.py                # MCP Stdio sunucusu (IDE'ler için)
├── server_http.py           # (YENİ) MCP Streamable-HTTP sunucusu (Open-WebUI için)
├── server_sse.py            # Dashboard REST API + SSE
│
├── requirements.txt         # Sabitlenmiş bağımlılıklar
└── flake.nix                # NixOS geliştirme ortamı
```

---

## 🔧 MCP Araçları (Tools)

Localmind, istemcilere şu otonom araçları sunar:
- `hafizaya_yaz`: Bilgiyi akıllıca kaydet (upsert + entity çıkarımı)
- `hafizada_ara`: Semantik arama yap
- `hafizayi_aktar`: Tüm anıları listele
- `hafizayi_unut`: Anıyı arşivle
- `oturum_ozetle`: Sohbeti analiz edip anılara dönüştür
- `gecmise_bak`: Son N günde eklenen anıları listele
- `hatirlat`: Uzun süre erişilmemiş önemli anıları hatırlat
- `grafik_sorgula`: Bir anının bağlantılı düğümlerini sorgula
- `oda_listele`: Odaları ve doluluk oranlarını listele
- `profil_goster`: Kullanıcı hafıza profilini göster

---

## ⚙️ Kurulum ve Çalıştırma

### 1. NixOS Ortamını Hazırlama
```bash
git clone https://codeberg.org/xmrah/localmind.git
cd localmind
nix develop
```

### 2. Bağımlılıkları Kurma
```bash
# Artık requirements.txt kullanılarak tutarlı bir ortam sağlanır
pip install -r requirements.txt
```

### 3. Servisleri Başlatma
```bash
# IDE Entegrasyonu için (Stdio)
./run_mcp.sh

# Open-WebUI Entegrasyonu için (Streamable-HTTP / Port 8001)
./run_mcp_sse.sh

# Dashboard REST API'sini başlatmak için (Port 8000)
python server_sse.py
```

### 4. IDE (Continue / Antigravity) Entegrasyonu
`~/.continue/config.json` içine ekleyin:
```json
{
  "mcpServers": [
    {
      "name": "localmind",
      "command": "bash",
      "args": ["/home/xmrah/Projects/localmind/run_mcp.sh"]
    }
  ]
}
```

---

## 🏠 NixOS Entegrasyonu (ai-toggle)
Sovereign bir yapı olan NixOS sisteminde Localmind otomatik olarak yönetilir. `systemd` servisleri:
- `localmind.service` → Dashboard REST API
- `localmind-mcp-sse.service` → MCP HTTP Köprüsü (`server_http.py`)
- Tüm zincir `ai-toggle start` ile ayağa kalkar, `ai-toggle stop` ile güvenle uykuya dalar.

---

## 📝 Lisans
Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır. Tamamen yerel, tamamen özgür.
