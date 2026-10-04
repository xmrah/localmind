# 2. ChromaDB ve SQLite Bilgi Grafiğinin Birlikte Kullanılması

Tarih: 2026-05-03

## Durum
Kabul Edildi (Accepted)

## Bağlam
Gerçekten egemen ve zeki bir hafıza sistemi iki şeye ihtiyaç duyar: 
1. Bir sorguya kavramsal olarak benzeyen anıları bulmak için *semantik arama*.
2. İnsanlar, projeler ve kavramlar arasındaki kesin ilişkileri anlamak için *yapısal hafıza*.
Her şeyi düz metin (text chunk) olarak bir vektör veritabanına yığmak, kesin ilişkilerde halüsinasyonlara yol açar. Sadece Grafik Veritabanı kullanmak ise LLM'lerin bulanık eşleştirme (fuzzy semantic matching) gücünü yok eder.

## Karar
İkili veritabanı (hibrit) yaklaşımını benimsedik:
1. **ChromaDB:** Ham anı parçaları ("Çekmeceler") için kosinüs benzerliği (Cosine similarity) kullanan birincil semantik vektör deposu olarak görev yapar.
2. **SQLite (FTS5 & Graph):** Bilgi Grafiği (`graph.db`) olarak görev yapar. Çıkarılan varlıkları (entities), kesin ilişkileri (triples) depolar ve BM25 skorlamasını tamamlayıcı nitelikte kesin eşleşmeli tam metin araması (FTS5) sağlar.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **İki Dünyanın En İyisi:** ChromaDB'nin hızlı semantik benzerlik yeteneği ile SQLite'ın kesin ve deterministik grafik tarama gücü birleşti.
- **Tamamen Yerel:** Her iki veritabanı da ayrı bir arka plan servisi gerektirmeden dosya bazlı ve yerel olarak çalışır.
- **Hızlı Uyanış:** SQLite okumaları inanılmaz hızlıdır, D3.js tabanlı Dashboard v2'nin galaksi grafiğini milisaniyeler içinde çizmesine olanak tanır.

**Eksileri:**
- **Senkronizasyon Yükü:** SQLite FTS tablolarının ChromaDB kayıtlarıyla uyumlu kalması için kod içinde manuel senkronizasyon mantığı (`_sync_fts_if_needed`) gerektirir.
- **Çift Şema Yönetimi:** Herhangi bir yapısal değişiklikte birbirine benzemeyen iki farklı veritabanı paradigmasının güncellenmesi gerekir.
