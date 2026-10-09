# Localmind Wiki

Localmind, yapay zeka ajanları ve kullanıcı egemenliği için tasarlanmış; tamamen yerel, çevrimdışı, durumsuz ve dinamik bir Zihin Sarayı sistemidir.

Notları ve anıları salt bir vektör listesine yığmak yerine, Loci Yöntemi ile yapılandırır, Ollama modelleriyle anlamsal varlık ağını çıkarır ve FastMCP protokolüyle doğrudan yapay zeka ajanlarına veya web paneline sunar.

---

## Neden Localmind?

* **Tam Veri Egemenliği:** Bilgiler üçüncü taraf sunuculara veya bulut altyapılarına gitmez. Telemetri ve veri toplama yoktur.
* **Açık Kaynak ve Sıfır Maliyet:** Abonelik veya kullanım ücreti içermez. Kendi donanımınızda çalışır.
* **Zihin Sarayı Hiyerarşisi:** Kanat, Oda ve Dolap koordinatlarıyla bilgileri kesin başlıklar altında sınıflandırır.
* **0 MB VRAM Hızlı Mod:** Hafıza eklerken büyük dil modellerini belleğe yüklemek gerekmez; 0 MB VRAM ile milisaniyeler içinde doğrudan kayıt yapılabilir.
* **Görsel Kontrol:** D3.js tabanlı canlı Bilgi Grafiği, 140 günlük Katkı Isı Haritası ve Ebbinghaus unutma eğrisi analitiği ile belleğin tam durumunu gösterir.

---

## Dokümantasyon Başlıkları

* [Kurulum ve Yapılandırma](Kurulum-ve-Yapilandirma): NixOS Flakes, standart Python ortamı ve systemd servisleri.
* [Zihin Sarayı Rehberi](Zihin-Sarayi-Rehberi): Loci mimarisi, Kanat, Oda ve Dolap düzeni, unutma eğrisi.
* [Dashboard Kılavuzu](Dashboard-Kullanim-Kilavuzu): Komut paleti, ısı haritası, D3.js grafiği ve analitik içgörüleri.
* [İstemci Entegrasyonları](Istemci-Entegrasyonlari): Antigravity IDE, Claude Desktop, Continue, Open-WebUI ve REST API.
* [FastMCP Araçları Referansı](MCP-Araclari-Referansi): Ajanların çağırdığı tüm MCP fonksiyonları ve parametreleri.

---

## Temel Altyapı

* **FastMCP:** Model Context Protocol standardında durumsuz köprü katmanı.
* **ChromaDB:** Yerel vektör indeksi ve kosinüs benzerlik motoru.
* **SQLite WAL:** FTS5 tam metin araması, varlık-ilişki tablosu ve metadata kaydı.
* **Hibrit Arama Motoru:** SQLite FTS5 (BM25) ve ChromaDB vektör aday havuzunu birleştiren, başlık öncelikli ve alaka eşikli füzyon mimarisi.
* **Ollama:** Dinamik olarak değiştirilebilen ve anlık test edilebilen yerel çıkarım modelleri.
* **Web Arayüzü:** Yapılandırma veya derleme aracı içermeyen, saf HTML5, CSS3, JavaScript ve D3.js v7 paneli.
