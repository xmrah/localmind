# Zihin Sarayı Rehberi

Localmind, antik Loci Yöntemi'ni modern bir yazılım mimarisine uyarlar.

---

## Koordinat Hiyerarşisi

Anılar düz bir vektör havuzunda kaybolmak yerine 3 kademeli koordinatlarla konumlandırılır:

```text
Zihin Sarayı
 └── Kanat     → En üst bağlam veya ana proje
      └── Oda     → Tematik konu kümesi
           └── Dolap → Spesifik bileşen veya başlık
                └── Anı   → Doğrudan not veya bilgi
```

### Örnek Koordinasyonlar

| Kanat | Oda | Dolap | İçerik |
| :--- | :--- | :--- | :--- |
| Sistem Mimarisi | mimari | NixOS Flake | Sistem yapılandırması ve disk bölüntüleri. |
| Siber Güvenlik | guvenlik | Firejail | Tarayıcı sıkılaştırma ve profil sandbox kuralları. |
| Masaüstü Ortamı | donanim | Bluetooth | Kulaklık eşleme ve ses kodek öncelikleri. |
| Yapay Zeka | ogrenme | FastMCP | Durumsuz MCP araç şablonları ve köprü ayarları. |

---

## Standart Odalar

Localmind varsayılan olarak 6 temel odaya sahiptir:

* **mimari:** Sistem topolojileri, mimari kararlar, altyapı şablonları.
* **guvenlik:** Şifreleme, güvenlik politikaları, anahtarlar, erişim kuralları.
* **donanim:** Çevre birimleri, işlemci ve grafik birimi ayarları, çekirdek optimizasyonları.
* **ogrenme:** Yeni teknolojiler, diller, kütüphane notları ve hedefler.
* **kisisel:** Bireysel tercihler, alışkanlıklar, hatırlatmalar.
* **genel:** Belirli bir temaya girmeyen genel notlar.

---

## Hızlı Mod ve Akıllı Mod

Localmind, anı kaydederken iki seçenek sunar:

### Hızlı Manuel Mod
* `use_ai=False` olarak çalışır.
* Model belleğe yüklenmez, 0 MB VRAM tüketir.
* Anı 5 ila 10 milisaniye içinde doğrudan ChromaDB ve SQLite veritabanına işlenir.

### Akıllı Mod
* `use_ai=True` olarak çalışır.
* Ollama modeli arka planda çalıştırılır.
* Metin analiz edilerek otomatik oda sınıflandırması yapılır.
* Metindeki kavram ve teknolojiler tespit edilerek Bilgi Grafiği'ne yeni ilişkiler eklenir.
* Önceki anılar taranarak çelişki veya güncelleme tespiti yapılır.

---

## Ebbinghaus Unutma Eğrisi

Localmind, anıların canlılığını zaman ve önem faktörüyle hesaplar:

Canlılık = Önem × (1 - Unutma Katsayısı) ^ Geçen Gün

* Yüksek önem puanına sahip ve sık erişilen kayıtlar bellekte her zaman önde kalır.
* Düşük öneme sahip ve uzun süre dokunulmayan bilgiler zamanla arka plana kayar ve aramalarda gereksiz yer kaplamaz.
* Unutulmaya yüz tutmuş kritik bilgiler, Hatırlatmalar panelinde listelenir.
