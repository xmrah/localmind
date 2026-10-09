# FastMCP Araçları Referansı

Localmind tarafından dışa aktarılan FastMCP araçlarının tam listesi ve parametreleri:

---

## 1. `hafizaya_yaz`
Bir bilgiyi Zihin Sarayı'na kaydeder.

* `konu` (zorunlu): Anının kısa ve açıklayıcı başlığı.
* `bilgi` (zorunlu): Metnin tamamı, kodlar veya kararlar.
* `oda`: Hedef oda adı (mimari, guvenlik, donanim, ogrenme, kisisel, genel). Boş bırakılırsa yapay zeka belirler.
* `kanat`: Üst bağlam veya proje adı. Varsayılan: `genel`.
* `dolap`: Alt konu başlığı. Varsayılan: `genel`.
* `importance`: 1 ile 10 arasında önem skoru. Varsayılan: `7`.
* `use_ai`: True ise Ollama ile analiz eder; False ise 0 MB VRAM ile doğrudan yazar.

---

## 2. `hafizada_ara`
Zihin sarayında hibrit arama yapar.

* `sorgu` (zorunlu): Aranacak anahtar kelimeler veya anlamsal cümle.
* `oda`: Belirli bir oda içinde filtreleme yapmak için oda adı.
* `n`: Getirilecek maksimum sonuç sayısı. Varsayılan: `5`.

---

## 3. `hafizayi_unut`
Bir anıyı aktif görünümden arşive taşır.

* `hafiza_id` (zorunlu): Arşivlenecek anının kimliği.

---

## 4. `grafik_sorgula`
Knowledge Graph üzerindeki bağlantıları sorgular.

* `varlik_adi` (zorunlu): İlişkileri aranacak kavram, kişi veya teknoloji.

---

## 5. `oturum_ozetle`
Konuşma metnini yapılandırılmış kalıcı anılara dönüştürür.

* `oturum_metni` (zorunlu): Özetlenecek diyalog içeriği.

---

## 6. `hatirlat`
Unutulmaya başlayan önemli kayıtları listeler.

* `n`: Getirilecek kayıt sayısı. Varsayılan: `5`.

---

## 7. `gecmise_bak`
Belirli bir zaman dilimindeki anıları listeler.

* `gun`: Kaç gün geriye gidileceği. Varsayılan: `7`.
* `oda`: Filtrelenecek oda.

---

## 8. `profil_goster`
Kullanıcının ilgi alanlarını, oda ve etiket dağılımını analiz eder.

---

## 9. `oda_listele`
Mevcut odaları ve anı yoğunluklarını listeler.

---

## 10. `hafizayi_aktar`
Tüm aktif belleği JSON formatında dışa aktarır.
