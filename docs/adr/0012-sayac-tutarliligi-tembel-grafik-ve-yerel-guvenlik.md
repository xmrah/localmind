# 12. Sayaç Tutarlılığı, Tembel Grafik Yükleme ve Yerel API Güvenliği

Tarih: 2026-10-08

## Durum
Kabul Edildi (Accepted)

## Bağlam
Localmind v2 mimarisinin kullanıcı deneyimi ve güvenlik odaklı detaylı incelemesinde (Genspark AI değerlendirmesi ve Gray-Hat tehdit modellemesi sentezi) şu kritik eksiklikler tespit edilmiştir:

1. **Sayaç Tutarsızlığı (Counter Desync):** Arşivlenen anılar veritabanından silinmeyip `archived="true"` olarak işaretlendiği için `collection.count()` hem aktif hem arşivli kayıtları döndürmektedir. Üst bardaki canlı nabız sayacı ve `/api/health` 118 gösterirken, pano kartları yalnızca aktif olan 106 anıyı saymakta ve kullanıcının gözünde sayısal tutarsızlık yaratmaktaydı.
2. **Gereksiz Hesaplama Yükü (Eager Graph Loading):** Dashboard ilk açıldığında `loadCore()` fonksiyonu doğrudan `/api/graph` çağrısı yapmaktaydı. `get_graph_data()` her istekte düğümler arası semantik mesafeleri sıfırdan hesapladığı için liste görünümlerinde (Genel Bakış, Odalar, Zaman Çizelgesi) gereksiz bir CPU ve gecikme maliyeti oluşturmaktaydı.
3. **Modal Başlığı & AI Toggle Çelişkisi:** Anı ekleme modalının başlığında statik olarak "Ollama ile otomatik sınıflandırma..." vaat edilirken, varsayılan anahtarın "0 MB VRAM / Hızlı Kayıt" olarak kapalı durması kullanıcı deneyiminde çelişki doğurmaktaydı.
4. **Yerel API ve Cross-Origin Güvenliği:** `127.0.0.1:8000` portundaki REST API üzerinde CORS kısıtlaması bulunmadığı için tarayıcıda gezilen kötü niyetli bir web sayfasının yerel ağ üzerinden hafıza verilerini okuma veya silme (drive-by exploit) riski bulunmaktaydı.
5. **Kod Okunabilirliği ve Kaynak Belirsizliği:** Anılardaki Bash komutları ve kod blokları düz metin olarak basılmakta; ayrıca anının bir AI ajanı tarafından mı yoksa kullanıcı tarafından mı eklendiği arayüzde ayırt edilememekteydi.

## Karar

Tespit edilen eksiklikler aşağıdaki mimari adımlarla giderilmiştir:

1. **Aktif / Arşivli Sayaç Ayrımı (`core/memory_manager.py` & `server_sse.py`):**
   - `MemoryManager` sınıfına `get_memory_counts()` metodu eklendi; ChromaDB metadatasından `active`, `archived` ve `total` ayrımı yapıldı.
   - `/api/health` ve SSE `/api/events` nabız akışı `active` sayısını varsayılan sayaç olarak benimseyerek kartlarla tam tutarlı hale getirildi.

2. **Tembel Grafik Yükleme (Lazy Graph Loading - `dashboard/main.js`):**
   - `loadCore()` fonksiyonu hafif ve doğrudan REST ucu olan `/api/memories` ile beslendi.
   - Ağır semantik ilişki matrisi hesaplayan `/api/graph` çağrısı `loadGraphData()` fonksiyonuna taşınarak yalnızca kullanıcı "Bilgi Grafiği" sekmesini açtığında tembel (on-demand) çalışacak şekilde izole edildi.

3. **Dinamik Modal Metni Senkronizasyonu (`dashboard/main.js`):**
   - Anı ekleme modal başlığına dinamik kimlik kazandırıldı (`addModalSubtitle`).
   - Anahtar kapalıyken *"Zihin Sarayı'na hızlı ve doğrudan kayıt (0 MB VRAM)"*, açıldığında ise *"Ollama ile otomatik sınıflandırma..."* metni dinamik olarak güncellenir.

4. **Yerel CORS ve Origin Kilidi (`server_sse.py`):**
   - FastAPI `CORSMiddleware` entegre edilerek yalnızca `localhost` ve `127.0.0.1` portlarına (8000 ve 8001) izin verildi. Harici web sitelerinin yerel hafıza motoruna erişimi engellendi.

5. **Kod Blokları Formatlayıcı & Provenance Rozetleri (`main.js` & `style.css`):**
   - Markdown kod blokları (```` ```...``` ```` ve ``` `kod` ```) için güvenli `formatBody()` fonksiyonu ve şık `.code-wrap` bileşeni eklendi; tek tıkla panoya kopyalama (`copySnippet`) butonu entegre edildi.
   - Anı kartlarına ve detay modalına `🤖 Ajan: <agent_id>` ve `👤 Kullanıcı` kaynak rozetleri yerleştirildi.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Kusursuz Veri Tutarlılığı:** Üst nabız sayacı ve ekran kartları her an birebir aynı aktif anı sayısını gösterir.
- **Hafif ve Işık Hızında Panel:** Liste ve pano görünümleri grafikten bağımsızlaştığı için panel anında açılır.
- **Sertleştirilmiş Güvenlik:** Yerel REST API'ye dış dünyadan gelebilecek cross-origin istekler engellendi.
- **Teknik İçerik UX'i:** Kodlar, Bash komutları ve scriptler artık kopyalanabilir ve okunaklı bir syntax formatındadır.
