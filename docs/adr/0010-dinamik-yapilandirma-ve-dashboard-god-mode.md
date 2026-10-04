# 10. Dinamik Yapılandırma Motoru ve Dashboard God-Mode Yönetim Mimarisi

Tarih: 2026-10-04

## Durum
Kabul Edildi (Accepted)

## Bağlam
Localmind v2 ilk aşamada yalnızca LLM ajanlarının MCP araçları üzerinden veri yazabildiği, web arayüzünün (Dashboard) ise sadece pasif ve salt-okunur (read-only) bir izleme ekranı olarak kaldığı bir mimariyle tasarlanmıştı. 

Bu durum şu kritik mimari eksiklikleri doğurdu:
1. **Statik Bağımlılık:** Kullanılacak Ollama modelleri (`core/intelligence.py`) ve Ebbinghaus çürüme katsayısı (`dashboard/main.js`) kaynak koda gömülüydü; değiştirmek için dosya manipülasyonu gerekiyordu.
2. **Kullanıcı Yetkisizliği (Lack of Sovereignty):** Kullanıcı web arayüzünden hatalı bir anıyı kalıcı olarak silemiyor, arşivlenen kayıtları göremiyor/geri alamıyor ve geçmişe dönük (custom timestamp) tarih damgasıyla anı ekleyemiyordu.
3. **Kör Noktalar:** MemPalace metadata hiyerarşisi (Kanat ve Dolap) veritabanında saklansa bile arayüzde gösterilmediği için kullanıcı verinin kaydedilip kaydedilmediğini teyit edemiyordu.

## Karar
Sistemi "Ajan Odaklı Pasif Bellek"ten "Kullanıcı Egemen Tam Yönetim (God-Mode)" mimarisine taşıdık:

1. **Merkezi Yapılandırma Motoru (`core/config.py` & `config.json`):**
   - Modeller (`fast_model`, `smart_model`, `conv_model`), çürüme katsayısı (`decay_factor`) ve çakışma politikası (`auto_archive_conflicts`) atomik JSON dosyasında kalıcılaştırıldı.
   - Tüm zeka ve çürüme fonksiyonları çalışma anında güncel config'i dinamik olarak okuyacak şekilde refactor edildi.

2. **Genişletilmiş REST API (`server_sse.py`):**
   - Yapılandırma yönetimi: `GET /api/settings`, `POST /api/settings`
   - Canlı Model Testi: `POST /api/settings/test-model` (Ollama'ya ping atarak gecikme/çalışırlık doğrulaması)
   - Yaşam Döngüsü & Veri Yönetimi: `DELETE /api/memory/{id}`, `POST /api/memory/archive`, `POST /api/memory/unarchive`, `GET /api/memory/archived`
   - MemPalace zengin veri rotası: `/api/memories`

3. **Dinamik Dashboard Yönetim Paneli (`dashboard/main.js` & `style.css`):**
   - **Ayarlar Sekmesi:** Statik metinler kaldırıldı. Ollama'da kurulu modeller dinamik dropdown ile listelendi, her model için anlık latency testi eklendi, Ebbinghaus decay için canlı simülasyon slider'ı entegre edildi.
   - **MemPalace Görselleştirmesi:** Anı kartlarına `🪽 [Kanat]` ve `🗄️ [Dolap]` rozetleri, detay modalına hiyerarşik `🏛️ Zihin Sarayı: Oda › Kanat › Dolap` konum çubuğu eklendi.
   - **Zaman Yolculuğu (Custom Timestamp):** Gelişmiş akordeon form ile geçmiş tarih damgasıyla anı kaydetme ve Zaman Çizelgesi'nde "Tümü" aralığıyla kronolojik görselleştirme sağlandı.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Tam Egemenlik:** Kullanıcı terminale girmeden veya ajan çağırmadan tüm hafızayı tarayıcı üzerinden yönetebilir, düzenleyebilir ve silebilir.
- **Canlı Adaptasyon:** Yeni bir Ollama modeli indirildiğinde kod değiştirmeden arayüzden seçilebilir ve tek tıkla test edilebilir.
- **Sıfır İllüzyon:** Arayüzdeki her ayar, buton ve veri alanı doğrudan veritabanı ve sunucu durumuna etki eder.

**Eksileri:**
- **Ek Konfigürasyon Dosyası:** `config.json` dosyasının taşınabilirlik ve yedekleme süreçlerinde (`git` ve `export`) dikkatle yönetilmesi gerekir.
