# 15. Zihin Sarayı 2026 Hibrit Arama, BM25-Vektör Havuz Füzyonu ve Alaka Eşiği Mimarisi

Tarih: 2026-10-10

## Durum
Kabul Edildi (Accepted)

## Bağlam
Localmind bir web arama motoru değil, bireysel bilişsel bellek ve Zihin Sarayı sistemidir. Kullanıcının sistem mimarisi, donanım notları, teknik terimleri, kod parçaları ve kişisel anılarını barındırır.

Eski arama altyapısında şu yapısal sorunlar tespit edilmiştir:
1. **Negatif Yüzde Gösterimi:** ChromaDB kosinüs mesafesi ($distance \in [0.0, 2.0]$) doğrudan `1.0 - distance` formülüyle skora dönüştürülüyordu. 1.0 üzerindeki mesafelerde skor %-23, %-37 gibi negatif değerler alarak arayüzde mantıksız bir görünüm oluşturuyordu.
2. **Kayıp Anahtar Kelime Adayları:** BM25 tam metin araması, bağımsız bir aday havuzu oluşturmak yerine yalnızca ChromaDB'den dönen ilk vektör sonuçları üzerinde süzgeç olarak çalıştırılıyordu. Bu durum, embedding modelinin (all-MiniLM-L6-v2) yabancı veya özel token olarak gördüğü teknik terimlerin (`enyxma`, `hyprland`, `sddm`) vektör havuzuna giremeyip tamamen kaybolmasına yol açıyordu.
3. **Zoraki Sonuç Doldurma (Eşik Eksikliği):** Veritabanında hiçbir karşılığı olmayan terimler (`xiaomi` gibi) aratıldığında dahi arama motoru eşik filtresi barındırmadığı için en az alakasız 8 anıyı zorla ekrana getiriyordu.
4. **Sıralama Uyuşmazlığı:** Arayüz kartları üzerinde bileşik hibrit skor yerine ham kosinüs mesafesi gösterildiğinden, sıralama ve yüzde değerleri çelişiyordu.

## Karar
2026 modern kişisel bilgi yönetim sistemleri (PKM / İkinci Beyin) standartlarına uygun olarak arama motoru sıfırdan revize edilmiştir:

### 1. Bağımsız İki Dal Aday Havuzu (Candidate Union)
- **1. Dal (Sözcüksel - SQLite FTS5 BM25):** Sorgu sözcükleri temizlenerek önek joker karakteri (`"terim"*`) ile aranır. Konu başlığı (5.0x), etiketler (3.0x) ve anı içeriği (1.0x) ağırlıklandırılarak sözcük frekans skoru hesaplanır.
- **2. Dal (Anlamsal - ChromaDB Vektör):** Anlamsal benzerlik için kosinüs mesafesi tavan sınırıyla (1.25) normalize edilerek $[0.0, 1.0]$ pozitif aralığına çekilir.
- **Havuz Birleşimi:** Aday listesi `set(bm25) | set(vector)` formülüyle bağımsız olarak birleştirilir. Böylece tam sözcük eşleşmeleri vektör uzayında geri düşse bile asla kaybolmaz.

### 2. Başlık ve Etiket Önceliği (Title & Tag Boost)
Kullanıcı aradığı terimi anının konusu veya etiketinde doğrudan geçirmişse, bu kayıt temel sözcüksel benzerlikte en üst dilime yükseltilir.

### 3. Gürültü ve Alaka Eşiği (Relevance Floor)
Veritabanında bulunmayan veya alakasız sorgularda gürültü sunumunu engellemek amacıyla eşik kuralı uygulanır:
- Sözcüksel (BM25) eşleşme yoksa (`lex_score == 0.0`) ve anlamsal yakınlık gürültü tabanının altındaysa (`sem_score < 0.40`), kayıt elenir.
- Karşılığı olmayan aramalarda zoraki liste döndürülmez; arayüz temiz bir "Eşleşen anı bulunamadı" geri bildirimi verir.

### 4. Bilişsel Tazelik ve Erişim Bonusu
Bileşik skor; Ebbinghaus unutma eğrisi ($decay$) ve anının geçmiş ziyaret sıklığı ($access\_count$) ile hafifçe desteklenerek yaşayan bellek önceliği korunur.

### 5. Arayüz ve Sunum Standardı
Panel tarafında (`dashboard/main.js`) tüm skorlar `Math.round(score * 100)` üzerinden pozitif yüzde olarak sunulur. Boş arama sonuçları şık ve bilgilendirici bir uyarı kartı ile karşılanır.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- Özel teknik isimler, donanım terimleri ve kod sembolleri anında bulunur.
- Negatif skor saçmalığı tamamen ortadan kaldırılmıştır.
- Veritabanında olmayan kayıtlar için sıfır gürültü garantisi sağlanmıştır.
- Harici bir bağımlılık eklenmeden, mevcut SQLite FTS5 ve ChromaDB altyapısıyla en yüksek performans korunmuştur.

**Kısıtlar:**
- FTS5 sorguları için sorgu terimleri noktalama işaretlerinden arındırılarak güvenli kelime token'larına dönüştürülür.
