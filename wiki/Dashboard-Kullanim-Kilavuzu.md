# Dashboard Kullanım Kılavuzu

Localmind web yönetim paneli `http://127.0.0.1:8000` adresinde çalışan, derleme adımı gerektirmeyen bir web uygulamasıdır.

---

## Klavye ile Gezinme ve Komut Paleti

* `Ctrl+K`: Komut paletini açar.
* Canlı arama: 2 karakterden itibaren BM25 ve vektör hibrit arama motoruyla, başlık önceliği ve alaka eşiği filtresiyle doğrulanmış anıları listeler. Eşleşmeyen aramalarda gürültü göstermez.
* Sayfa geçişleri: Ok tuşları ve Enter ile istenilen sekmeye geçiş yapılır.
* `Esc`: Açık modal veya panelleri kapatır.
* `N`: Yeni anı ekleme penceresini açar.

---

## Paneller ve İşlevleri

### Genel Bakış
* Canlı sistem durumu ve kayıtlı anı sayıları.
* Sayfa açıldığında değerleri akıcı biçimde sayan sayaç animasyonları.
* Hızlı anı ekleme butonu.
* Son eklenen ve en çok bağlantılı kayıtlar.

### Bilgi Grafiği
* D3.js ile varlık ve anı ağının görselleştirilmesi.
* Çok bağlantılı ve yüksek öneme sahip düğümlerde nabız aurası.
* Seçilen veya üzerine gelinen anılarda hareketli bağlantı akış çizgileri.
* Taş gibi donmayı engelleyen sürekli hafif süzülme hareketi.
* Tekerlek ile yakınlaştırma ve sürükleyerek taşıma.

### Odalar
* Tematik odalara göre ayrılmış anı kartları.
* Alt kanat ve dolap sayıları.
* Tazelik göstergesi: Aktif, Taze, Uyuyan.
* Odaya eklenen en son anının başlık önizlemesi.

### Zaman Çizelgesi
* 140 günlük GitHub tarzı katkı ısı haritası.
* Isı haritasında herhangi bir güne tıklayarak doğrudan o tarihteki anıları listeleme.
* Filtreyi sıfırlama seçeneği.
* 90 günlük günlük aktivite alan eğrisi.

### Analitik
* Paslanan anılar: 30 günden eski, önemi yüksek kayıtlar ve hatırlatıcıya yönlendirme.
* Öksüz anılar: Henüz başka bir kayıtla bağlanmamış anılar ve grafikte bulma seçeneği.
* Odak ağırlığı: Belleğin en çok hangi odada yoğunlaştığının analizi.
* Ebbinghaus unutma eğrisi grafiği ve önem dağılımı histogramı.

### Hatırlatmalar
* Canlılık skoru düşen ancak önemi yüksek anıların proaktif listesi.

### Arşiv
* Arşivlenmiş kayıtların yönetimi.
* Tek tıkla geri alma veya kalıcı olarak silme.

### Ayarlar
* Sistemdeki Ollama modellerinin listesi.
* Modelleri anlık yanıt süresiyle test etme.
* Unutma katsayısını kaydırma çubuğu ile belirleme.
* Değişiklikleri kaydetme.
