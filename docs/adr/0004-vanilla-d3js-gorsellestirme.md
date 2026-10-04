# 4. Vanilla D3.js İle Görselleştirme (React/Vue Yerine)

Tarih: 2026-05-03

## Durum
Kabul Edildi (Accepted)

## Bağlam
Zihin sarayının web arayüzünde (Dashboard v2) anıların ve kavramların (entities) birbirleriyle nasıl ilişkili olduğunu göstermek için güçlü bir grafik kütüphanesine ihtiyacımız vardı. Günümüzde Frontend dünyası React, Vue, Svelte gibi ağır framework'ler ve NPM bağımlılıkları etrafında dönüyor. Ancak biz; hafif, derleme (build) gerektirmeyen ve doğrudan tarayıcıda çalışan bir arayüz istiyorduk.

## Karar
Frontend framework'leri (React vb.) tamamen reddedilmiş, arayüz sadece HTML, ham (vanilla) JavaScript ve CSS kullanılarak yazılmıştır (`dashboard.eski` silinmiş ve güncel `dashboard/main.js` kurulmuştur). Bilgi grafiğini (constellation) çizmek için tek bağımlılık olarak doğrudan yerel `d3.v7.min.js` kullanılmıştır.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Derleme Süreci Yok (No Build Step):** Node.js, Webpack veya Vite kurmaya gerek kalmaz. Dosyayı düzenler, tarayıcıda F5 yaparsın ve anında çalışır.
- **İnanılmaz Hafiflik:** Toplam boyut birkaç yüz KB'ı geçmez, anında yüklenir.
- **Uzun Ömürlülük (Longevity):** Vanilla JS ve D3 kütüphanesi NPM paket cehennemine girmediği için 10 yıl sonra bile aynı kararlılıkla çalışmaya devam eder.

**Eksileri:**
- **State Yönetimi Zorluğu:** React'in sunduğu kolay state yönetimi (useState, useEffect) olmadığı için DOM manipülasyonları ve veri eşitlemeleri manuel olarak yazılmalıdır.
- **Zorlu D3.js Öğrenme Eğrisi:** D3.js'in simülasyon ve güç(force) fizik motorunu ham JavaScript ile kurmak karmaşık bir matematik gerektirir.
