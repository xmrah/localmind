# 6. Langchain Reddi ve Doğrudan Ollama API Kullanımı

Tarih: 2026-05-10

## Durum
Kabul Edildi (Accepted)

## Bağlam
RAG (Retrieval-Augmented Generation) sistemleri geliştirilirken endüstri standardı olarak genellikle Langchain veya LlamaIndex gibi devasa kütüphaneler kullanılır. Ancak bu kütüphaneler inanılmaz derecede hantaldır, çok fazla dış bağımlılık getirir ve promptların arka planda nasıl işlendiğini soyutlayarak (kara kutu) kontrolü kaybettirir. Özellikle yerel (local) Ollama modelleriyle çalışırken en yüksek hızı ve en şeffaf kontrolü sağlamamız gerekiyordu.

## Karar
Langchain ve türevi soyutlama kütüphaneleri projeden tamamen reddedilmiştir. `core/intelligence.py` modülü içinde, httpx kullanılarak doğrudan Ollama'nın yerel REST API'sine (`http://localhost:11434/api/generate`) istek atılmaktadır. Sınıflandırma, varlık çıkarımı (entity extraction) ve upsert kararları için kendi ham promptlarımız statik stringler halinde yazılmıştır.

## Sonuçlar / Bedeller (Consequences)
**Artıları:**
- **Sıfır Hantallık:** Projenin bağımlılıkları (requirements.txt) inanılmaz hafif kalır.
- **Tam Şeffaflık:** LLM'e giden prompt metninde ne olduğunu kelimesi kelimesine kontrol edebilir, halüsinasyonları anında yakalayabiliriz.
- **Performans:** Arada hiçbir soyutlama katmanı (middleware) olmadığı için milisaniye düzeyinde API tepki süreleri elde edilir.

**Eksileri:**
- **Manuel İşçilik:** JSON ayrıştırma (parsing) veya yeniden deneme (retry) gibi işlemleri bizim kodlamamız gerekir.
- **Model Değişimi:** Yarın Ollama yerine başka bir yerel sağlayıcıya geçmek istersek, istek atan HTTP fonksiyonlarını manuel güncellememiz gerekir.
