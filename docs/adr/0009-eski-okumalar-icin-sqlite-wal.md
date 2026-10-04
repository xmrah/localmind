# 9. Eşzamanlılık İçin SQLite WAL Modu Kullanımı

Tarih: 2026-10-04

## Durum
Kabul Edildi (Accepted)

## Bağlam
D3.js bilgi grafiğini çizmek için veritabanını sürekli okuyan Dashboard v2'nin devreye girmesi ve birden fazla ajanın FastMCP üzerinden aynı anda hafızaya yazma ihtimali doğduğunda `database is locked` (veritabanı kilitli) hataları almaya başladık. Varsayılan SQLite geri alma günlüğü (rollback journal), yazma işlemleri sırasında tüm veritabanını katı bir şekilde kilitler ve okumaları engeller.

## Karar
SQLite grafik veritabanında (`graph.db`) eşzamanlılığı artırmak için `PRAGMA journal_mode=WAL;` komutuyla **WAL (Write-Ahead Logging)** modunu etkinleştirdik. Buna ek olarak; FTS5 senkronizasyonu ve arama sorguları gibi yoğun okuma yapan tüm fonksiyonları `?mode=ro` (read-only / salt-okunur) parametresi kullanarak veritabanına bağlanacak şekilde güncelledik.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Eşzamanlı Erişim:** Okuyanlar yazanları engellemez; yazanlar da okuyanları engellemez. Bir ajan devasa boyutta bir hafıza kaydı yaparken, Dashboard takılmadan grafiği çizmeye devam edebilir.
- **Performans:** WAL modu, karma (okuma/yazma) yükü altında çalışan sistemler için genellikle çok daha yüksek performans sunar.

**Eksileri:**
- **Dosya Kalabalığı:** Ana `.db` dosyasının yanında `-wal` ve `-shm` adında ek dosyalar yaratır. Bu dosyaların sürüm kontrolünde yoksayılması (`.gitignore`) ve yedekleme (export) işlemlerinde dikkatli yönetilmesi gerekir.
- **Ağ Dosya Sistemleri:** WAL modu NFS gibi ağ dosya sistemlerinde iyi çalışmaz. Ancak `localmind` tamamen yerel ve hava boşluklu (air-gapped) depolama için tasarlandığından bu bizim için bir sorun teşkil etmez.
