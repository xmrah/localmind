# 5. Zeka Katmanı İçin Yerel Ollama Kullanımı

Tarih: 2026-05-10

## Durum
Kabul Edildi (Accepted)

## Bağlam
Localmind hafıza sisteminin; kullanıcının ham girdilerinden varlıkları (entity) çıkarmak, etiket üretmek ve hafıza odalarını sınıflandırmak için bir yapay zeka (zeka katmanı) kullanması gerekiyordu. OpenAI veya Anthropic gibi bulut tabanlı API'lere güvenmek; gecikme yaratır, gizlilik riskleri doğurur ve projenin "hava boşluklu (air-gapped) ve egemen (sovereign)" felsefesini bozar. Yaptığımız yerel model benchmark testleri (örn. Gemma 4B ve Gemma 2 27B), bu modellerin Türkçe doğal dil işleme görevlerini başarıyla yerine getirebildiğini kanıtladı.

## Karar
Hafıza sınıflandırma ve varlık çıkarımı (`core/intelligence.py`) için tamamen yerel makinede çalışan **Ollama** kullanılacaktır. Eğer Ollama kapalıysa veya yanıt vermezse, dış API'lere gitmek yerine sistem güvenli bir şekilde varsayılan etiketlere ve odalara (`genel`) geri dönecektir (graceful degradation).

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Sıfır Veri Sızıntısı:** Kullanıcının özel anıları asla makine dışına çıkmaz, %100 gizlilik sağlanır.
- **Ücretsiz Çalışma:** API token maliyeti yoktur, arka planda sürekli hafıza işleme yapılabilir.
- **Egemenlik:** Projenin bulutsuz (offline-first) felsefesine tam uyum.

**Eksileri:**
- **Donanım Bağımlılığı:** Yerel makinede Gemma 4B/27B gibi modelleri tatmin edici hızlarda çalıştıracak RAM/VRAM gerekir.
- **Mantık Yürütme Sınırı:** Yerel modeller, devasa bulut modellerine kıyasla derin semantik nüansları kaçırabilir. Bu yüzden çok katı prompt mühendisliğine ihtiyaç duyarlar.
