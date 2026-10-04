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

[![FastMCP](https://img.shields.io/badge/FastMCP-v3.0+-blue?style=flat-square)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square)](https://www.python.org/)
[![NixOS](https://img.shields.io/badge/NixOS-Supported-5277C3?style=flat-square&logo=NixOS)](https://nixos.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](#lisans)

</div>

Localmind, yazdığınız notları sadece depolayan aptal bir veritabanı değildir. Arka planda **Ollama** ile çalışan, bilgileri anlayan, birbiriyle ilişkilendiren ve ihtiyaç anında bağlamıyla birlikte doğrudan yapay zeka modelinize (LLM) sunan **durumsuz (stateless) bir Zihin Sarayıdır.**

Hiçbir veri internete çıkmaz. Bulut yok, abonelik yok. Tamamen yerel, tamamen sizin.

---

## 🚀 Temel Felsefe & Özellikler

* **Veri Egemenliği (Sovereignty):** Sistem tamamen kapalı devredir. Tüm verileriniz makinenizde, sizin kontrolünüz altındadır.
* **Semantik Vektör Arama (ChromaDB):** Geleneksel regex veya kelime eşleşmesi yerine, cümlenin "anlamını" arar. 
* **Otonom Knowledge Graph (SQLite):** Eklenen her bilgi parçacığından `Kişi`, `Kavram`, `Teknoloji` gibi varlıkları (Entity) ve aralarındaki ilişkileri otomatik olarak çıkarır.
* **Ebbinghaus Unutma Eğrisi:** Sisteme entegre edilen zaman aşımı skoru sayesinde, uzun süre erişilmeyen önemsiz bilgiler zamanla geriye düşerken, sık erişilen kritik notlar her zaman canlı kalır.
* **Otomatik Sınıflandırma:** Notlarınız arka planda analiz edilerek en uygun odalara (`mimari`, `güvenlik`, `donanım`, `kişisel` vb.) otomatik yerleştirilir.

---

## 🧠 MCP Araçları (Tools)

Localmind, FastMCP mimarisi üzerinden LLM'inize şu otonom yetenekleri kazandırır:

| Araç Adı | Açıklama |
| :--- | :--- |
| `hafizaya_yaz` | Bilgiyi akıllıca kaydeder, varlık çıkarımı yapar ve sınıflandırır. |
| `hafizada_ara` | Zihin sarayında semantik benzerliğe göre arama yapar. |
| `hafizayi_unut` | Bir anıyı arşivler (aktif görünümden kaldırır, veri kaybı olmadan saklar). |
| `grafik_sorgula` | Bir kavramın veya kişinin Knowledge Graph üzerindeki bağlantı ağını çizer. |
| `oturum_ozetle` | Uzun sohbetleri analiz edip yapılandırılmış kalıcı anılara dönüştürür. |
| `hatirlat` | Uzun süredir bakılmayan ama "önemli" olarak işaretlenmiş anıları proaktif olarak hatırlatır. |
| `gecmise_bak` | Son N gün içinde öğrenilen veya kaydedilen tüm bilgileri listeler. |
| `profil_goster` | Hangi konularda daha çok düşündüğünüzü (oda ve etiket dağılımı) analiz eder. |
| `oda_listele` | Tüm hafıza odalarını ve içerdikleri anı sayılarını listeler. |
| `hafizayi_aktar` | Tüm aktif hafızayı JSON formatında dışa aktarır (yedek/export). |

---

## 🏗️ Mimari Topoloji

Localmind, **Ekim 2026** standartlarına uygun Stateless FastMCP mimarisi ve yerel D3.js Dashboard v2 üzerine inşa edilmiştir.

```mermaid
graph TD
    %% İstemciler
    A1[Open-WebUI / Web] -->|HTTP / SSE :8001| B[FastMCP Router]
    A2[Continue / Antigravity / IDE] -->|Stdio| B
    
    %% Çekirdek
    B -->|Otonom Çağrılar| C{Memory Manager}
    G[Dashboard v2 :8000] -.->|REST API / SSE| C
    
    %% Veritabanları ve AI
    C -->|Semantik Vektörler| D[(ChromaDB)]
    C -->|Knowledge Graph| E[(SQLite)]
    C <-->|Embeddings & Sınıflandırma| F[Yerel Ollama]
```

---

## 🖥️ Dashboard v2 Özellikleri

`127.0.0.1:8000` üzerinde çalışan modern ve tamamen çevrimdışı web arayüzü:

* **Genel Bakış:** Canlı bellek nabzı, son anılar, sistem sağlık durumu ve hızlı kayıt.
* **Bilgi Grafiği:** Obsidian tarzı galaksi kümelenmesi (constellation clustering), semantik bağlar ve akıllı odak/hover efektleri.
* **Odalar (Memory Rooms):** Anıları konularına göre (`mimari`, `güvenlik`, `donanım`, `kişisel` vb.) filtreleme ve yönetme.
* **Zaman Çizelgesi:** Kronolojik anı akışı ve etkileşimli filtreleme.
* **Analitik:** Ebbinghaus unutma eğrisi, önem dağılımı ve etiket sıklığı grafikleri.
* **Hatırlatmalar:** Proaktif önem/yaş skoruna göre unutulmaya yüz tutmuş anılar.
* **Ağ İzolasyonu:** Yalnızca `127.0.0.1` (localhost) arayüzüne bağlıdır, dış ağlara kapalıdır.

---

## ⚙️ Kurulum & Çalıştırma

Proje temel olarak standart bir Python uygulamasıdır. Sisteminizde **Ollama**'nın çalışıyor olduğundan emin olun.

### 1. Ortam Hazırlığı
```bash
git clone https://codeberg.org/xmrah/localmind.git
cd localmind

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
*(NixOS kullanıcıları doğrudan `nix develop` ile izole ortama girebilirler.)*

### 2. İstemciye Göre Sunucuyu Başlatma
Localmind, kullanacağınız arayüze göre farklı transport katmanları sunar:

- **Open-WebUI için (HTTP MCP - 8001):**
  ```bash
  ./run_mcp_sse.sh
  ```
- **Continue / Antigravity / IDE için (Stdio MCP):**
  ```bash
  ./run_mcp.sh
  ```
- **Dashboard v2 Arayüzü için (8000):**
  ```bash
  just dashboard
  # veya: python server_sse.py
  ```
- **Systemd Servis Yönetimi:**
  ```bash
  just status   # Durumu gör
  just restart  # Servisleri yeniden başlat
  just logs     # Canlı log takibi
  ```

---

## 🔌 İstemci Entegrasyonları

### Open-WebUI
Yönetici paneli > Dış Araçlar (Bağlantılar) sekmesine gidin ve bağlantıyı şöyle yapılandırın:
- **Tür:** `MCP` (veya MCP Streamable HTTP)
- **URL:** `http://127.0.0.1:8001/mcp`
- **ID:** `localmind`
*(Yetki/Auth kısmını `Yok` veya boş bırakın, sistem tamamen yereldir.)*

### Continue
`~/.continue/config.json` dosyanıza şu bloğu ekleyin:
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

## 🛡️ Sovereign Geliştirici Notu

Bu sistem, verinin bulut şirketlerinin elinde oyuncak olmasına karşı bir duruştur. `core/memory_manager.py` içindeki tüm veritabanı I/O işlemleri `asyncio.to_thread` ile asenkronize edilmiş olup, yapay zeka modelinizin saniyede binlerce token üretirken bile arayüzü kilitlememesi sağlanmıştır. 

Kod yapısı olabildiğince şeffaf ve sadedir. Fork'layın, parçalayın, kendi zihin sarayınızı inşa edin.

## Lisans
MIT License.
