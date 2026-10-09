# Kurulum ve Yapılandırma Rehberi

Localmind kurulumu, servis yapılandırması ve sistem ayarları bu sayfada özetlenmiştir.

---

## 1. Standart Python Kurulumu

### Gereksinimler
* Python 3.11 veya üzeri
* Git
* Ollama (yerel zeka katmanı için önerilir)

### Adımlar

```bash
git clone https://codeberg.org/xmrah/localmind.git
cd localmind

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python server_sse.py
```

Web paneli `http://127.0.0.1:8000` adresinde çalışır.

---

## 2. NixOS ve Flakes ile Kurulum

Localmind doğrudan Nix flake desteğine sahiptir:

```bash
# Geliştirme kabuğuna girmek için:
nix develop

# Paneli doğrudan çalıştırmak için:
nix run .#dashboard
```

---

## 3. Systemd Servisleri

Localmind sistem başlangıcında arka planda çalıştırılabilir:

### Web Konsolu ve REST Servisi (`localmind.service`)

```ini
[Unit]
Description=Localmind AI Hafıza Sistemi (Dashboard)
After=network.target

[Service]
Type=simple
User=kullanici
WorkingDirectory=/home/kullanici/Projects/localmind
ExecStart=/home/kullanici/Projects/localmind/.venv/bin/python server_sse.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

### Open-WebUI Köprüsü (`localmind-mcp-sse.service`)

```ini
[Unit]
Description=Localmind HTTP MCP Köprüsü (Open-WebUI)
After=network.target

[Service]
Type=simple
User=kullanici
WorkingDirectory=/home/kullanici/Projects/localmind
ExecStart=/home/kullanici/Projects/localmind/.venv/bin/python server_http.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

---

## 4. Yapılandırma Parametreleri (`config.json`)

Sistem ayarları `config.json` dosyasından veya web arayüzündeki Ayarlar sekmesinden düzenlenir:

```json
{
  "fast_model": "qwen2.5-coder:7b",
  "smart_model": "qwen2.5-coder:7b",
  "conv_model": "qwen2.5-coder:7b",
  "decay_factor": 0.05,
  "auto_archive_conflicts": true,
  "ollama_base": "http://localhost:11434"
}
```

* `fast_model`: Hızlı oda sınıflandırması ve tek cümlelik özetler için kullanılan model.
* `smart_model`: Varlık ve ilişki çıkarımı yapan model.
* `conv_model`: Sohbet oturumlarını özetleyen model.
* `decay_factor`: Ebbinghaus unutma katsayısı.
* `auto_archive_conflicts`: Yeni anı eski bilgiyle çeliştiğinde eskisini otomatik arşive kaldırma onayı.
* `ollama_base`: Yerel Ollama sunucu adresi.
