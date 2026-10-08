# 13. Tier 0 ve Tier 1 UX/UI Modernizasyonu: Lucide SVG Sprite, Shimmer İskeletler, ⌘K Komut Paleti ve View Transitions

Tarih: 2026-10-09

## Durum
Kabul Edildi (Accepted)

## Bağlam
Localmind v2 paneli fonksiyonel olarak güçlü ve stabil çalışmasına karşın, kullanıcı deneyimi açısından "prototip / hobi projesi" hissi veren bazı görsel ve mimari eksiklikler barındırmaktaydı:

1. **İkon ve Marka Algısı:** Arayüz genelinde (menü, kartlar, butonlar, modallar) emoji karakterleri (🧠, 🏠, 🕸️, 📚, ⚡, 🛡️, vb.) kullanılmaktaydı. Linux / Hyprland ortamlarında emoji fontlarının (Noto, Twemoji) platformlar arası farklı ve uyumsuz render edilmesi kurumsal masaüstü ciddiyetini düşürmekteydi.
2. **Yükleme Durumları (Perceived Latency):** Ekranlar yüklenirken ilkel CSS spinner ve düz metinler gösterilmekte, içerik geldiğinde ani sıçramalar (layout shift) yaşanmaktaydı.
3. **Klavye Odaklı Gezinme:** Hyprland ve döşemeli pencere yöneticisi kullanan klavye odaklı kullanıcılar için hızlı erişim sağlayacak modern bir komut paleti (Command Palette) bulunmamaktaydı.
4. **Görünüm Geçişleri:** Sekmeler arası geçişler ani DOM değişimleriyle gerçekleşiyor, modern tarayıcıların sunduğu akıcı geçiş hissi eksik kalıyordu.
5. **Egemenlik ve Sıfır-Build Kısıtı:** Projenin NixOS / tmpfs ve bağımsız çalışma felsefesi gereği, `npm`, `node_modules` veya harici CDN bağımlılığı eklenmeden saf Vanilla JS ve CSS standartlarıyla bu modernizasyonun yapılması şarttı.

## Karar
Genspark AI mimari spesifikasyonu ve yerel gereksinimler sentezlenerek aşağıdaki Tier 0 (Hızlı Kazanımlar) ve Tier 1 (İmza Özellikler) katmanları uygulanmıştır:

1. **Yerel Lucide SVG İkon Motoru (`dashboard/icons.js` - Yeni):**
   - 119 adet Lucide SVG ikonu yerel bir JavaScript dosyasında tek bir gizli `<symbol>` sprite havuzuna gömüldü.
   - Sıfır ağ isteği (CDN yok), sıfır build pipeline.
   - Her ikon kullanımı yalnızca ~60 baytlık `<use href="#lm-i-...">` referansıyla render edilerek DOM performansı maksimize edildi.
   - Tüm menü, başlık, buton, oda ve modal emojileri vektörel SVG ikonlarla değiştirildi.

2. **Shimmer İskelet Yükleyiciler (Skeleton Loaders - `style.css` & `main.js`):**
   - Spinner'lar yerine Linear/Vercel standardında parıldayan `@keyframes sk-shimmer` CSS iskeletleri (`skelPanel`, `.skel-page`, `.sk`) entegre edildi.
   - `prefers-reduced-motion: reduce` altında animasyonlar otomatik durdurularak erişilebilirlik sağlandı.

3. **⌘K / Ctrl+K Komut Paleti (`index.html`, `main.js`, `style.css`):**
   - Masaüstü reflekslerine uygun, modal bazlı komut paleti inşa edildi.
   - `Ctrl+K` veya `Cmd+K` ile açılma, ok tuşlarıyla gezinme, `Enter` ile çalıştırma, `Esc` ile kapatma.
   - **Canlı Semantik Arama:** 2+ karakter girildiğinde `/api/search` üzerinden semantik arama yaparak sonuçları eşleşme yüzdesiyle sunar.
   - **Hızlı Navigasyon:** 8 görünüme ve dinamik odalara tek tuşla geçiş.
   - **Aksiyonlar:** "Yeni Anı Ekle" modalını açma ve "Koyu/Açık Tema" değiştirme.

4. **View Transitions API Entegrasyonu (`main.js` & `style.css`):**
   - `router()` fonksiyonu `withTransition()` adaptörü ile sarıldı.
   - Tarayıcı destekliyorsa (`document.startViewTransition`) yumuşak sinematik geçiş sağlandı; desteklemiyorsa düz render davranışına düşen progressive enhancement modeli uygulandı.
   - Hızlı ardışık tıklamalara karşı yarış durumu (race condition) koruması (`routeToken`) eklendi.

5. **Görsel Cila (Tier 0 Polish):**
   - Tabular sayılar (`font-variant-numeric: tabular-nums`) eklenerek sayaç değişimlerinde sütun titremeleri engellendi.
   - Tutarlı odak halkaları (`:focus-visible`) ve seçim rengi (`::selection`) tanımlandı.

6. **Mevcut Yeteneklerin Korunması & Mühürleme:**
   - ADR-0011 (0-MB VRAM hızlı modal ve altyazı senkronizasyonu) ve ADR-0012 (aktif/arşiv sayaç tutarlılığı, tembel grafik ve kod kopyalama butonları) özellikleri eksiksiz korundu.
   - Projenin çalışan hali `/home/xmrah/Projects/localmind-backup-2026-10-09-stable` konumuna kopyalandı ve `v2.0.1-stable` git etiketiyle mühürlendi.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Masaüstü/Pro Düzey Algı:** Emojilerden arınmış, net vektörel ikonlar ve cam efektli komut paleti paneli Obsidian/Linear seviyesine çıkardı.
- **Düşük Algılanan Gecikme:** Shimmer iskeletleri sayesinde sayfa açılışları ve sekme geçişleri anlık hissettiriyor.
- **Klavye Verimliliği:** `Ctrl+K`, `/`, `N` ve `Esc` kısayollarıyla panel fareden bağımsız tam klavye ile yönetilebilir hale geldi.
- **Sıfır Bağımlılık & Sıfır Entropi:** Proje tek bir npm paketi veya harici dosya almadan, FastAPI üzerinden saf statik dosyalarla servis edilmeye devam ediyor.
