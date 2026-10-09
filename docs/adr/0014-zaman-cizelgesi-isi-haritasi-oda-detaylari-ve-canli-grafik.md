# 14. Zihin Sarayı Faz 2: Odalar V2, Katkı Isı Haritası, D3 Organik Canlılık ve Akıllı Analitik İçgörüleri

Tarih: 2026-10-09

## Durum
Kabul Edildi (Accepted)

## Bağlam
Localmind v2 paneli Tier 0/1 modernizasyonu (Lucide SVG sprite, Shimmer iskeletleri, ⌘K komut paleti) sonrasında çok daha hızlı ve modern bir arayüze kavuşmuştu. Ancak kullanıcı deneyimi ve zihinsel saray metaforu açısından incelendiğinde bazı sekmelerin statik ("donuk") kaldığı ve potansiyelini tam yansıtmadığı gözlemlendi:

1. **Odalar Sekmesi Sığlığı:** Odalar sekmesindeki kartlar sadece isim, anı sayısı ve renk çizgisinden ibaretti. Zihin Sarayı'nın alt hiyerarşisi olan kanatlar (wings), dolaplar (closets), odanın en güncel düşüncesi/anısı ve tazelik durumu (aktif, taze, uyuyan) görünmüyordu.
2. **Zaman Çizelgesi Eksikliği:** Zaman çizelgesi sadece düz bir dikey listeden ibaretti. Kullanıcının hafıza geçmişini, tutarlılığını ve anı yoğunluğunu GitHub tarzı bir ısı haritasıyla tek bakışta görmesi ve belirli bir güne tıklayarak anında filtrelemesi mümkün değildi.
3. **D3 Bilgi Grafiğinin Statik Başlangıcı:** Bilgi grafiği Obsidian estetiğinde tasarlanmış olmasına rağmen, ilk açıldığında simülasyon sakinleşince taş gibi donup kalıyor; kullanıcı fareyle bir düğümü sürüklemeden önce hiçbir mikro hareket veya canlılık hissi sunmuyordu.
4. **Analitikte Eylem Eksikliği (Prescriptive vs Descriptive):** Analitik sekmesi sadece sayısal grafikler (pasta, histogram, unutma eğrisi) sunuyor; kullanıcıya "şimdi ne yapmalısın?" sorusunun cevabını verecek eyleme dönüştürülebilir tavsiyeler (Actionable Insights) üretmiyordu.
5. **Genel Bakış Donukluğu:** Genel Bakış açıldığında veya yeni anı eklendiğinde sayaçlar ani ve statik olarak değişiyor, yerel sinir ağı bağlantısının canlı nabzını hissettirmiyordu.

## Karar
Önem sırasına göre 5 faz halinde aşağıdaki mimari ve arayüz geliştirmeleri uygulanmıştır:

### Faz 1: Odalar V2 (Zihin Sarayı Mekan Zenginliği)
- `buildRooms()` fonksiyonu genişletilerek her oda için alt mekanlar (kanat sayısı, dolap sayısı), en sık kullanılan ilk 3 etiket, tazelik durumu (`aktif`: <7 gün, `taze`: 7-30 gün, `uyuyan`: >30 gün) ve son kaydedilen anının başlığı derlendi.
- Oda kartları zenginleştirildi:
  - Üstte büyük Lucide ikonu, anı sayısı, ortalama önem puanı ve dinamik durum rozeti.
  - Odanın anı kapasitesini yansıtan orantılı ilerleme çubuğu.
  - "Son Düşünce" alıntılama kutusu (`.room-latest-box`).
  - Kanat ve dolap çipleri (`.badge.wing`, `.badge.closet`) ve son aktivite zamanı.
  - Odanın öne çıkan etiketleri.

### Faz 2: Zaman Çizelgesi Katkı Isı Haritası (Heatmap V2)
- Saf Vanilla JS ve SVG/CSS ile 20 haftalık (140 günlük) GitHub tarzı katkı takvimi grid'i (`heatmapHTML()`) geliştirildi.
- Hücreler kayıt yoğunluğuna göre 5 seviye renk tonuna (`hm-lvl-0` .. `hm-lvl-4`) sahip kılındı.
- **İki Yönlü İnteraktif Filtreleme:** Isı haritasında herhangi bir güne tıklandığında, altındaki dikey zaman çizelgesi anında o tarihe filtrelenir; filtre sıfırlama butonuyla tek tıkla geri dönülür.
- Sol tarafta ısı haritası, sağ tarafta 90 günlük dinamik alan grafiği (Area SVG) yan yana konumlandırıldı.

### Faz 3: D3 Bilgi Grafiği Organik Canlılığı (Cosmic Ambient Drift)
- Merkez düğümler (derece ≥ 3 veya önem ≥ 8) için sürekli nefes alan nabız halkası (`.hub-aura` + `@keyframes hub-pulse`) eklendi.
- Aktif veya üzerine gelinen düğümlerin bağlantı çizgilerine hareketli elektrik akışı efekti (`.link-flow` + `@keyframes link-flow` ve `stroke-dashoffset`) uygulandı.
- D3 simülasyonuna başlangıçta ve sürükleme sonrasında mikro hedef kuvvet (`alphaTarget(0.0035)`) verilerek grafiğin bir taş gibi donması engellendi; düğümler galaksideki yıldızlar gibi organik ve sakin biçimde hafifçe salınmaya devam eder.

### Faz 4: Eyleme Dönüştürülebilir Analitik İçgörüleri (Actionable Insights)
- Analitik motoru verileri otomatik tarayarak 3 kilit bilişsel içgörü kartı üretir:
  1. **Paslanan Anılar:** Önemi yüksek (≥8) ancak 30+ gündür ziyaret edilmemiş kritik bilgiler (tek tıkla Hatırlatıcı'ya yönlendirir).
  2. **Öksüz Anılar:** Bilgi grafiğinde henüz hiçbir varlığa veya anıya bağlanmamış izole düğümler (tek tıkla Grafiğe yönlendirir).
  3. **Odak Ağırlığı:** Zihin sarayının ağırlık merkezinin hangi temada toplandığı (yüzde oranı ve odaya hızlı geçiş butonu).

### Faz 5: Genel Bakış Canlılığı & Sayısal Sayım Animasyonu (Count-Up Micro-Animations)
- KPI kartlarına ve istatistik kutucuklarına hafif `requestAnimationFrame` tabanlı `animateCounters()` mekanizması entegre edildi (~420ms akıcı `easeOutExpo` geçişi).
- Sayfa ilk açıldığında veya yeni anı kaydedilip ekran tazelendiğinde sayılar sıfırdan hedefe akıcı biçimde sayarak canlılık hissi verir.
- Genel Bakış başlığına yeşil/turkuaz atan nabız LED'li canlı sistem rozeti (`.live-pill` + `.live-dot`) ve doğrudan "+ Yeni Anı" hızlı erişim butonu eklendi.
- Kart üzerine gelindiğinde (hover) kart yükselmesi ve kenar parıltısı eklendi.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Derinlik ve Yaşayan Sistem Hissi:** Zihin sarayı artık statik bir veritabanı görünümünden çıkıp nefes alan, zaman boyutunu sergileyen ve proaktif yönlendirme yapan bir bilişsel çalışma alanına dönüştü.
- **Kritik Hafıza Kaybını Önleme:** Paslanan ve öksüz anı içgörüleri sayesinde önemli bilgilerin unutulması engellenir.
- **Tıklanabilir Tarihsel Gezinme:** 140 günlük ısı haritası geçmiş çalışma ve öğrenme ritmini anında görünür kılar.
- **Sıfır Ekstra Bağımlılık:** Tüm bu yetenekler harici kütüphane eklenmeden, yalnızca mevcut D3 ve Vanilla JS/CSS yapısıyla sıfır VRAM tüketimiyle sağlandı.

**Kısıtlar & Dikkat Edilecekler:**
- Isı haritası son 140 günü kapsar; daha eski geçmiş anılar aralık seçici ("Tümü") üzerinden listelenir.
- Ambient drift için `alphaTarget(0.0035)` CPU tüketimini ihmal edilebilir seviyede (~%0.1) tutacak şekilde kalibre edilmiştir.
