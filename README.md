<div align="center">

```text
  _                     _           _           _ 
 | |                   | |         (_)         | |
 | |     ___   ___ __ _| |_ __ ___  _ _ __   __| |
 | |    / _ \ / __/ _` | | '_ ` _ \| | '_ \ / _` |
 | |___| (_) | (_| (_| | | | | | | | | | | | (_| |
 \_____/\___/ \___\__,_|_|_| |_| |_|_|_| |_|\__,_|
```

**Sovereign Digital Memory & Knowledge Graph for Local LLMs**  
*Yapay Zeka Ajanları ve Kullanıcı Egemenliği İçin Yerel, Çevrimdışı ve Dinamik Zihin Sarayı*

[![FastMCP](https://img.shields.io/badge/FastMCP-v3.0+-blue?style=flat-square)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow?style=flat-square)](https://www.python.org/)
[![NixOS](https://img.shields.io/badge/NixOS-Flakes-5277C3?style=flat-square&logo=NixOS)](https://nixos.org/)
[![Architecture](https://img.shields.io/badge/Architecture-MemPalace%20%2B%20WAL-purple?style=flat-square)](#-mempalace-metadata-hiyerarşisi)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](#lisans)

</div>

Localmind, tuttuğunuz notları yalnızca depolayan pasif bir veritabanı değildir. Arka planda yerel **Ollama** modelleriyle çalışan, bilgileri anlayan, varlık-ilişki ağını (Knowledge Graph) çıkaran, **MemPalace** hiyerarşisiyle düzenleyen ve ihtiyaç anında bağlamıyla birlikte doğrudan yapay zeka modelinize (LLM) veya web konsolunuza sunan **durumsuz (stateless) ve egemen bir Zihin Sarayıdır.**

Hiçbir veri internete veya buluta sızmaz. API anahtarı, telemetri veya abonelik yoktur. **Tamamen yerel, tamamen sizin.**

---

## 🚀 Öne Çıkan Yetenekler

* **🛡️ Veri Egemenliği (Sovereignty):** Kapalı devre mimari. Bellek veritabanı, vektör indeksleri ve grafik ilişkileri yerel diskinizde saklanır.
* **🏛️ MemPalace Hiyerarşisi:** Anılar düz bir vektör havuzuna yığılmaz; **Kanat (Wing)**, **Oda (Room)** ve **Dolap (Closet)** koordinatlarıyla yapılandırılır.
* **⚙️ Dinamik Yapılandırma Motoru (Config Engine):** Kaynak kodları düzenlemeye gerek kalmadan `config.json` ve UI üzerinden modelleri anında değiştirme, canlı test etme (`⚡ Test`) ve parametreleri güncelleme.
* **👑 Dashboard God-Mode:** Web arayüzü yalnızca bir izleme ekranı değildir; geçmişe dönük anı ekleme, kalıcı silme, arşivleme ve geri alma yetkilerine sahip tam bir yönetim konsoludur.
* **🔍 Hibrit Semantik Arama:** Cosine vektör benzerliği (%50) + SQLite BM25 anahtar kelime araması (%30) + Ebbinghaus çürüme puanı (%20) hibrit skorlaması.
* **🕸️ Otonom Bilgi Grafiği (Knowledge Graph):** Metinlerden otomatik çıkarılan `Kişi`, `Cihaz`, `Kavram` ve `Teknoloji` varlıkları ile D3.js tabanlı galaksi görselleştirmesi.
* **📉 Ebbinghaus Bellek Çürümesi (Decay):** Unutulmaya yüz tutmuş bilgileri zamanla geri plana iten, sık erişilen ve yüksek önem puanına sahip anıları her zaman canlı tutan matematiksel model.

---

## 🏛️ MemPalace Metadata Hiyerarşisi

Localmind, antik **Loci Yöntemi**'ni (Method of Loci) ChromaDB metadata filtreleme şemasına entegre eder:

```text
Zihin Sarayı (Mind Palace)
 └── 🪽 Kanat (Wing)     → En üst bağlam / Proje / Ekosistem (örn: "NixOS", "Ağ & Güvenlik", "Frontend")
      └── 🚪 Oda (Room)     → Fonksiyonel Kategori (örn: "mimari", "guvenlik", "donanim", "ogrenme")
           └── 🗄️ Dolap (Closet) → Spesifik Konu İpliği / Bileşen (örn: "Flake", "FastMCP", "Hyprland")
                └── 📄 Çekmece (Memory) → Atomik Bilgi / Not / Karar Metni
```

* **Cerrahi Filtreleme:** Ajanlar ve kullanıcılar binlerce anıyı taramak yerine doğrudan belirli bir kanat veya dolap içine nokta atışı sorgu yapabilir.
* **Geriye Dönük Uyumluluk:** Eski kayıtlar varsayılan olarak `genel` kanat ve dolabına atanır, sistemde sıfır veri kaybı yaşanır.

---

## 🏗️ Mimari Topoloji

Localmind; eşzamanlı MCP istemcileri, yüksek hızlı yerel vektör motoru, WAL modunda çalışan ilişkisel grafik ve D3.js yönetim panelinden oluşur:

```mermaid
graph TD
    subgraph İstemciler (Clients)
        C1[Open-WebUI / Web Arayüzü] -->|HTTP / SSE :8001| R1[FastMCP Streamable Router]
        C2[Continue / Antigravity / IDE] -->|Stdio IPC| R2[FastMCP Stdio Server]
        C3[Yönetim Konsolu / Dashboard] -->|REST API & SSE :8000| S1[FastAPI Server]
    end

    subgraph Çekirdek Motor (Core Engine)
        R1 & R2 & S1 --> MM[MemoryManager]
        CFG[(config.json)] <-->|Dinamik Parametreler| MM
        MM <--> INT[Intelligence Layer]
    end

    subgraph Depolama & Yerel Zeka
        MM -->|Vektörler & Metadata| VDB[(ChromaDB : zihin_sarayi)]
        MM -->|Varlıklar & WAL Grafiği| GDB[(SQLite : graph.db)]
        INT <-->|Sınıflandırma, Upsert, Varlık Çıkarımı| OLLAMA[Yerel Ollama :11434]
    end
```

---

## 🖥️ Dashboard v2 (God-Mode Yönetim Konsolu)

`http://127.0.0.1:8000` adresinde çalışan çevrimdışı web arayüzü aşağıdaki panelleri sunar:

| Panel | İkon | Açıklama |
| :--- | :---: | :--- |
| **Genel Bakış** | 🏠 | Canlı SSE nabzı, sistem sağlık durumu, hızlı anı girişi ve son aktiviteler. |
| **Bilgi Grafiği** | 🕸️ | D3.js ile varlık ve bellek galaksisi, semantik kuvvet yönlendirmeli (force-directed) kümeleme. |
| **Odalar** | 🗂️ | Konu odalarına göre filtrelenmiş kartlar, anlık semantik oda içi arama motoru. |
| **Zaman Çizelgesi**| 🕰️ | Kronolojik anı akışı. Özel tarih filtreleri (7 gün, 30 gün, 90 gün, Tümü) ve aktivite grafiği. |
| **Analitik** | 📊 | Ebbinghaus saçılım diyagramı, oda dağılımı donutu, etiket frekansı ve önem histogramı. |
| **Hatırlatmalar** | 🔔 | Ebbinghaus eğrisine göre unutulmaya yüz tutmuş yüksek öncelikli anıların proaktif listesi. |
| **Arşiv** | 📦 | Aktif görünümden kaldırılmış anıların listesi; tek tıkla **Geri Al** veya **Kalıcı Sil**. |
| **Ayarlar** | ⚙️ | Kurulu Ollama modellerini keşfetme, canlı gecikme testi (`⚡ Test`), decay slider'ı ve dinamik kayıt. |

---

## 🧠 FastMCP Araçları (Tools)

Localmind, yapay zeka ajanlarınıza (Claude, DeepSeek, Qwen vb.) aşağıdaki otonom yetenekleri kazandırır:

| Araç Adı | Açıklama |
| :--- | :--- |
| `hafizaya_yaz` | Bilgiyi kanat, dolap ve önem derecesiyle kaydeder; Ollama ile oda sınıflandırması ve varlık çıkarımı yapar. |
| `hafizada_ara` | Zihin sarayında vektör + BM25 + decay hibrit semantik araması gerçekleştirir. |
| `hafizayi_unut` | Bir anıyı kalıcı olarak silmeden arşivler (aktif görünümden kaldırır). |
| `grafik_sorgula` | Bir kavramın veya kişinin Knowledge Graph üzerindeki bağlantı ağını çeker. |
| `oturum_ozetle` | Uzun sohbet oturumlarını analiz edip kalıcı yapılandırılmış anılara dönüştürür. |
| `hatirlat` | Unutulmaya başlayan kritik bilgileri proaktif olarak ajana sunar. |
| `gecmise_bak` | Belirli bir gün aralığında kaydedilmiş tüm bilgileri listeler. |
| `profil_goster` | Kullanıcının ilgi alanlarını, oda ve etiket dağılımını analiz eder. |
| `oda_listele` | Mevcut tüm odaları ve anı yoğunluklarını listeler. |
| `hafizayi_aktar` | Tüm aktif hafızayı JSON formatında dışa aktarır (yedekleme). |

---

## 🌐 REST API Özeti (`server_sse.py`)

Dashboard ve harici otomasyonlar için sunulan yerel REST API rotaları:

```text
GET    /api/health              → Sistem durumu, anı sayısı ve Ollama erişilebilirliği
GET    /api/stats               → Oda bazlı istatistikler
GET    /api/rooms               → Tüm odalar ve anı sayıları
GET    /api/room/{oda}          → Belirli bir odadaki anılar (Kanat & Dolap dahil)
GET    /api/memories            → Tüm aktif anılar (zengin metadata ile)
GET    /api/graph               → D3.js için grafik düğümleri ve benzerlik bağları
GET    /api/search?q=...        → Hibrit semantik arama
POST   /api/memory              → Yeni anı ekleme (Ollama otomatik upsert & varlık çıkarımı)
POST   /api/memory/archive      → Anıyı arşive taşıma
GET    /api/memory/archived     → Arşivlenmiş anıları listeleme
POST   /api/memory/unarchive    → Anıyı arşivden çıkarma
DELETE /api/memory/{id}         → Anıyı ChromaDB ve SQLite'tan kalıcı olarak silme
GET    /api/settings            → Mevcut config ve kurulu Ollama modelleri listesi
POST   /api/settings            → Modelleri ve decay katsayısını kalıcı güncelleme
POST   /api/settings/test-model → Seçilen modeli anlık ping/test etme
GET    /api/events              → Sunucu canlı nabız SSE akışı (Server-Sent Events)
```

---

## 🛠️ Kurulum & Çalıştırma

### Gereksinimler
- Python 3.11+
- Yerel [Ollama](https://ollama.com) sunucusu (`http://localhost:11434`)
- C kütüphaneleri (`libstdc++.so.6`, `libz.so.1`) — *(NixOS'ta otomatik çözülür)*

### 1. Depoyu Klonlama & Ortam
```bash
git clone https://codeberg.org/xmrah/localmind.git
cd localmind

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Başlatma Seçenekleri

Localmind, kullanım senaryonuza göre bağımsız giriş noktaları sunar:

```bash
# 1. Dashboard v2 Web Konsolu (:8000)
just dashboard
# veya: python server_sse.py

# 2. Open-WebUI İçin HTTP MCP Köprüsü (:8001)
./run_mcp_sse.sh
# veya: python server_http.py

# 3. IDE / Continue / Antigravity İçin Stdio MCP
./run_mcp.sh

# 4. Systemd Servis Yönetimi (NixOS / Linux)
just status     # Servislerin durumunu göster
just restart    # localmind ve localmind-mcp-sse servislerini yeniden başlat
just logs       # Canlı log akışı
```

---

## 🔌 İstemci Entegrasyonları

### Open-WebUI Entegrasyonu
1. Yönetici Paneli > **Ayarlar** > **Dış Araçlar (Bağlantılar)** sekmesine gidin.
2. Yeni bağlantı ekleyin:
   - **Tür:** `MCP` (Streamable HTTP)
   - **URL:** `http://127.0.0.1:8001/mcp`
   - **ID:** `localmind`
   - **Kimlik Doğrulama:** Yok (Boş bırakın)

### Continue / VSCode Entegrasyonu
`~/.continue/config.json` dosyanızdaki `mcpServers` listesine ekleyin:
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

## 📜 Mimari Karar Kayıtları (ADR)

Projenin evrimi ve alınan tüm temel mühendislik kararları `docs/adr/` dizininde kayıt altındadır:

| No | Karar Başlığı | Tarih | Durum |
| :---: | :--- | :---: | :---: |
| **0001** | [NixOS Flakes İle Tekrarlanabilir Geliştirme Ortamı](docs/adr/0001-nixos-flakes-ortami.md) | 2026-05-01 | Kabul Edildi |
| **0002** | [ChromaDB ve SQLite Bilgi Grafiğinin Birlikte Kullanılması](docs/adr/0002-chromadb-ve-sqlite-hibrit-yapi.md) | 2026-05-03 | Kabul Edildi |
| **0003** | [Ebbinghaus Unutma Eğrisinin (Decay) Uygulanması](docs/adr/0003-ebbinghaus-unutma-egrisi.md) | 2026-05-03 | Kabul Edildi |
| **0004** | [Vanilla D3.js İle Görselleştirme (React/Vue Yerine)](docs/adr/0004-vanilla-d3js-gorsellestirme.md) | 2026-05-03 | Kabul Edildi |
| **0005** | [Zeka Katmanı İçin Yerel Ollama Kullanımı](docs/adr/0005-yerel-ollama-zeka-katmani.md) | 2026-05-10 | Kabul Edildi |
| **0006** | [Langchain Reddi ve Doğrudan Ollama API Kullanımı](docs/adr/0006-langchain-kutuphanesi-reddi.md) | 2026-05-10 | Kabul Edildi |
| **0007** | [Durumsuz (Stateless) FastMCP Mimarisinin Benimsenmesi](docs/adr/0007-durumsuz-fastmcp-mimarisi.md) | 2026-07-25 | Kabul Edildi |
| **0008** | [Metadata Üzerinden MemPalace Hiyerarşisinin Benimsenmesi](docs/adr/0008-mempalace-metadata-hiyerarsisi.md) | 2026-10-04 | Kabul Edildi |
| **0009** | [Eşzamanlılık İçin SQLite WAL Modu Kullanımı](docs/adr/0009-eski-okumalar-icin-sqlite-wal.md) | 2026-10-04 | Kabul Edildi |
| **0010** | [Dinamik Yapılandırma Motoru ve Dashboard God-Mode Mimarisi](docs/adr/0010-dinamik-yapilandirma-ve-dashboard-god-mode.md) | 2026-10-04 | Kabul Edildi |

---

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakabilirsiniz.
