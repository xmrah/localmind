# 11. Sıfır VRAM Manuel Anı Kaydı ve Ayrık Yapay Zeka Katmanı Mimarisi

Tarih: 2026-10-05

## Durum
Kabul Edildi (Accepted)

## Bağlam
Localmind'ın zeka katmanı (`core/intelligence.py`), hafızaya yeni bir bilgi eklenirken otomatik oda sınıflandırması (`classify_room`), benzerlik ve çakışma tespiti (`decide_upsert`), anahtar kelime üretimi (`generate_tags`) ve bilgi grafiği için varlık çıkarımı (`extract_entities`) adımlarını yürütür. Bu adımlarda `fast_model` (Qwen) ve özellikle `smart_model` (`huihui_ai/gemma-4-abliterated:26b` gibi ~18 GB VRAM tüketen büyük yerel modeller) devreye girer.

Ancak Dashboard üzerinden kullanıcının manuel olarak anı eklediği senaryolarda:
1. Kullanıcı başlığı, bilgiyi, odayı, kanadı, dolabı ve önem skorunu zaten kendisi belirler.
2. Bu basit ve doğrudan kayıt için 26 milyar parametreli bir modelin GPU VRAM'ine yüklenmesi gereksiz kaynak tüketimine, fan gürültüsüne, sistemde gecikmeye ve bellek israfına yol açar.
3. Basit bir komut veya not düşmek isteyen kullanıcı saniyelerce modelin VRAM'e oturmasını beklemek zorunda kalır.

## Karar
Manuel kayıt yolunu ağır yapay zeka model çağrılarından ayırarak "Sıfır VRAM / Anında Kayıt" mimarisine geçtik:

1. **Çekirdek Bellek Yöneticisi (`core/memory_manager.py`):**
   - `add_memory` fonksiyonuna `use_ai: bool = True` bayrağı eklendi.
   - `use_ai=False` olduğunda hiçbir Ollama modeli çağrılmaz. VRAM tüketimi 0 MB'dir. Kayıt doğrudan ChromaDB vektör tablosuna ve SQLite FTS5 tam metin indeksine 5-10 ms içerisinde atomik olarak yazılır.

2. **REST API Katmanı (`server_sse.py`):**
   - `AddMemoryRequest` veri modeline `use_ai: bool = False` parametresi eklendi. Dashboard'dan gelen manuel isteklerde varsayılan olarak sıfır VRAM modu geçerli kılındı.

3. **Dashboard Web Arayüzü (`dashboard/main.js`):**
   - "+ Yeni Anı Ekle" modalına zarif bir switch bileşeni eklendi: `🤖 Ollama AI Analizi` (varsayılan: Kapalı / Hızlı 0 MB VRAM).
   - Kullanıcı dilediğinde bu anahtarı açarak bilgi grafiği için derinlemesine varlık çıkarımı (Entity Extraction) modunu aktif hale getirebilir.
   - Buton metni duruma göre dinamik değişir ("Kaydediliyor..." vs "Ollama işliyor...").

4. **MCP Entegrasyonu (`tools.py`):**
   - `hafizaya_yaz` MCP fonksiyonuna `use_ai: bool` desteği getirilerek harici ajanların da ihtiyaç duyduklarında sıfır VRAM tüketimiyle hızlı hafıza yazabilmesi sağlandı.

5. **SQLite FTS5 Yazma Düzeltmesi:**
   - `_fts_upsert` ve senkronizasyon adımlarında read-only bağlantı açılmasından kaynaklanan FTS5 yazma hatası giderilerek tüm manuel ve akıllı kayıtların BM25 hibrit arama indeksine anında girmesi garanti altına alındı.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Işık Hızında Kayıt:** Dashboard'dan anı ekleme süresi saniyelerden ~10 milisaniyeye düştü.
- **Sıfır VRAM Tüketimi:** Kullanıcı not eklerken GPU belleği ve güç tüketimi sıfır seviyesinde kalır.
- **Seçim Özgürlüğü:** Bilgi grafiğinde düğüm ve ilişki çıkartmak isteyen kullanıcı tek bir toggle ile Ollama analizini açabilir.
- **Eksiksiz Semantik Arama:** Model yüklenmese dahi ChromaDB ve SQLite BM25 FTS5 indekslemesi eksiksiz çalıştığı için anı anında aranabilir durumdadır.

**Eksileri:**
- `use_ai=False` modunda kaydedilen anılarda bilgi grafiği (Knowledge Graph) için otomatik varlık ve ilişki çıkarımı yapılmaz. (İstenirse daha sonra veya kaydederken AI toggle açılarak yapılabilir).
