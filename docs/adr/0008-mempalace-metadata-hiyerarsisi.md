# 8. Metadata Üzerinden MemPalace Hiyerarşisinin Benimsenmesi

Tarih: 2026-10-04

## Durum
Kabul Edildi (Accepted)

## Bağlam
Hafıza sistemi büyüdükçe, tüm anıları düz bir vektör veritabanına yığmak arama kalitesini bozmaya başlar. "MemPalace" projesi, yapay zeka ajanları için Loci Yöntemi'ni (Method of Loci) popüler hale getirdi: hafızayı Kanatlar (Varlıklar/Projeler), Odalar (Zaman/Oturum), Dolaplar (Konu İplikleri) ve Çekmeceler (Kelimesi Kelimesine Anılar) olarak kategorize etmek. Tüm ChromaDB altyapımızı yıkmadan bu verimli okuma hiyerarşisini uygulamamız gerekiyordu.

## Karar
Her hiyerarşi katmanı için ayrı koleksiyonlar (collection) veya fiziksel tablolar açmak yerine; Kanat, Oda, Dolap ve Çekmece mimarisini doğrudan **ChromaDB metadata şeması** içine gömdük:
- `kanat` (Wing)
- `oda` (Room)
- `dolap` (Closet)

FastMCP `hafizaya_yaz` aracını, yapay zekanın (LLM) otonom olarak bu parametreleri seçip doldurabilmesi için güncelledik.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Sıfır Kırılma (Backward Compatibility):** Eski `localmind` anıları (varsayılan olarak `genel` değerini aldıkları için) hatasız çalışmaya devam eder.
- **Token Tasarrufu:** Ajanların, ChromaDB `where` filtrelerini kullanarak gereksiz binlerce vektörü atlayıp doğrudan spesifik bir `kanat` veya `dolap` içinde cerrahi aramalar yapmasına imkan tanır.
- **Mimari Temizlik:** Veritabanı katmanını dümdüz tutarken, hiyerarşi yükünü metadata filtreleme motoruna devreder.

**Eksileri:**
- **Ajanın Omuzlarındaki Yük:** Sistemin düzenli çalışması, yapay zeka ajanının `hafizaya_yaz` aracını çağırırken bağlamdan doğru kanat ve dolap etiketini çıkarma zekasına (reasoning) emanet edilmiştir.
