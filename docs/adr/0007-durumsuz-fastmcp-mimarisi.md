# 7. Durumsuz (Stateless) FastMCP Mimarisinin Benimsenmesi

Tarih: 2026-07-25

## Durum
Kabul Edildi (Accepted)

## Bağlam
Hafıza sisteminin hem IDE içindeki yerel yapay zeka ajanları (Continue/Antigravity) hem de web arayüzleri (Open-WebUI) tarafından erişilebilir olması gerekiyordu. Başlangıçta bu iki farklı istemci için ayrı bağlantı durumları (state) yönetmek karmaşıktı ve sistem kilitlenmelerine yol açıyordu. Hafıza araçlarımızı farklı taşıma katmanları (transport layers) üzerinden sorunsuzca sunacak standart bir protokole ihtiyacımız vardı.

## Karar
Durumsuz (stateless) bir mimari ile **FastMCP** çatısını (framework) benimsedik. `hafizaya_yaz`, `grafik_sorgula` gibi tüm çekirdek hafıza araçlarını sadece bir kez `tools.py` içinde tanımladık. Daha sonra bu araçları iki farklı yoldan dışa açtık:
1. IDE entegrasyonu için `run_mcp.sh` (stdio).
2. Open-WebUI ve dış istemciler için 8001 portunda çalışan `server_http.py` (SSE - Server-Sent Events).

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Tek Doğru Kaynağı:** İş mantığı tamamen `tools.py` içinde merkezileşti ve ağ protokolünden soyutlandı.
- **Evrensel Uyumluluk:** Endüstri standardı olan MCP (Model Context Protocol) ile %100 uyumluluk.
- **Basitlik:** Karmaşık WebSocket oturumlarını veya yönlendirmeleri manuel yönetmeye gerek kalmadı.

**Eksileri:**
- **FastMCP Bağımlılığı:** Sisteme katı bir FastMCP Python kütüphanesi bağımlılığı eklendi.
- **Durumsuzluk Kısıtı:** Araç yürütme katmanında uzun ömürlü bağlantı oturumları tutulamıyor; gereken tüm bağlamın araç parametreleri üzerinden her defasında geçilmesi gerekiyor.
