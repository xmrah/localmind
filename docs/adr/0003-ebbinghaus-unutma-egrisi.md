# 3. Ebbinghaus Unutma Eğrisinin (Decay) Uygulanması

Tarih: 2026-05-03

## Durum
Kabul Edildi (Accepted)

## Bağlam
Sıradan veritabanları veriyi kaydettikleri ilk günkü gibi aynı önem seviyesinde tutarlar. Ancak biyolojik bir zihin böyle çalışmaz; kullanılmayan bilgi zamanla solar (unutulur), yeniden erişilen bilgi ise tekrar canlanır. Localmind'ın "Biyolojik Hafıza Simülatörü" olabilmesi için, anıların arama sonuçlarındaki veya galaksi haritasındaki (Dashboard) görünürlüklerinin zamanla solmasını matematiksel olarak modellememiz gerekiyordu.

## Karar
Sisteme Ebbinghaus Unutma Eğrisi tabanlı bir "Decay (Çürüme/Solma)" mekanizması eklenmiştir. `dashboard/main.js` içinde yer alan `DECAY = 0.99` sabiti ve `liveness(m)` fonksiyonu (`importance * Math.pow(DECAY, daysOld)`) sayesinde anıların güncel canlılığı (liveness) hesaplanır. Eski anılar zaman geçtikçe haritada küçülür ve solar. Ancak `access_count` (erişim sayısı) arttıkça bu solma tersine çevrilir.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Doğal Zihin Taklidi:** Önemli ama çok eski bir bilgi, sürekli kullanılan güncel bir bilginin önüne geçemez. Tam bir organik hafıza gibi davranır.
- **Görsel Temizlik:** Dashboard üzerindeki galaksi grafiğinde çöp veya unutulmuş bilgiler görsel olarak geri plana itilir, bilişsel yük (cognitive load) azalır.

**Eksileri:**
- **Matematiksel Maliyet:** Her arama veya görselleştirme işlemi sırasında güncel zamana göre yeniden matematiksel hesaplama (üslü sayılar) yapılması gerekir.
