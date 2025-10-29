# Firma Chatbot - AI Destekli Akıllı Asistan

Modern teknolojilerle geliştirilmiş, MSSQL veritabanı entegreli, ChatGPT destekli firma içi chatbot sistemi.

## Özellikler

- **ChatGPT Entegrasyonu**: OpenAI GPT-4 ile güçlendirilmiş akıllı yanıtlar
- **MSSQL Veritabanı**: Stored Procedure tabanlı soru-cevap sistemi
- **Doküman Okuma**: PDF, Word, Excel, PowerPoint dosyalarından bilgi çıkarma
- **Kullanıcı Yönetimi**: JWT token tabanlı güvenli kimlik doğrulama
- **Sohbet Geçmişi**: Tüm konuşmaların kayıt altına alınması
- **Modüler Yapı**: Kolayca yeni soru türleri ve kurallar eklenebilir
- **Modern Arayüz**: Responsive, kullanıcı dostu web arayüzü

## Teknolojiler

### Backend
- **Python 3.8+**
- **Flask**: Web framework
- **pyodbc**: MSSQL bağlantısı
- **OpenAI API**: ChatGPT entegrasyonu
- **bcrypt**: Şifre güvenliği
- **JWT**: Token yönetimi

### Frontend
- **HTML5/CSS3**
- **Vanilla JavaScript**
- **Modern responsive tasarım**

### Veritabanı
- **Microsoft SQL Server**
- **Stored Procedures**
- **Optimized indexes**

## Proje Yapısı

```
AI_ChatBot/
├── database/
│   ├── create_tables.sql          # Tablo oluşturma scriptleri
│   ├── create_sp.sql               # Stored procedure'lar
│   └── sample_data.sql             # Örnek veriler
├── backend/
│   ├── app.py                      # Ana Flask uygulaması
│   ├── config.py                   # Konfigürasyon yönetimi
│   ├── database.py                 # MSSQL bağlantı ve işlemleri
│   ├── auth.py                     # Kimlik doğrulama
│   ├── chatbot.py                  # ChatGPT entegrasyonu
│   └── document_reader.py          # Doküman okuma
├── frontend/
│   ├── index.html                  # Ana sayfa
│   └── static/
│       ├── css/style.css           # Stil dosyası
│       └── js/app.js               # JavaScript
├── documents/                      # Talimat dokümanları
├── requirements.txt                # Python bağımlılıkları
├── .env.example                    # Örnek çevre değişkenleri
└── README.md                       # Bu dosya
```

## Kurulum

### 1. Gereksinimler

- Python 3.8 veya üzeri
- Microsoft SQL Server 2016 veya üzeri
- ODBC Driver 17 for SQL Server
- OpenAI API Key

### 2. Proje Kurulumu

```bash
# Projeyi klonlayın
git clone <repo-url>
cd AI_ChatBot

# Virtual environment oluşturun
python -m venv venv

# Virtual environment'ı aktifleştirin
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 3. Veritabanı Kurulumu

```bash
# SQL Server'a bağlanın ve scriptleri çalıştırın

# 1. Tabloları oluştur
sqlcmd -S localhost -U sa -P YourPassword -i database/create_tables.sql

# 2. Stored procedure'ları oluştur
sqlcmd -S localhost -U sa -P YourPassword -i database/create_sp.sql

# 3. Örnek verileri yükle
sqlcmd -S localhost -U sa -P YourPassword -i database/sample_data.sql
```

### 4. Çevre Değişkenlerini Ayarlayın

```bash
# .env.example dosyasını kopyalayın
cp .env.example .env

# .env dosyasını düzenleyin ve gerekli bilgileri girin
```

### 5. Uygulamayı Başlatın

```bash
# Backend dizinine gidin
cd backend

# Flask uygulamasını başlatın
python app.py
```

Uygulama şu adreste çalışacaktır: `http://localhost:5000`

## Konfigürasyon

`.env` dosyasında yapılması gereken ayarlar:

### Flask Ayarları
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
HOST=0.0.0.0
PORT=5000
```

### Veritabanı Ayarları
```env
DB_SERVER=localhost
DB_NAME=ChatBotDB
DB_USERNAME=sa
DB_PASSWORD=YourPassword123!
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_PORT=1433
```

### OpenAI API Ayarları
```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000
```

### JWT Ayarları
```env
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Doküman Ayarları
```env
DOCUMENTS_PATH=./documents
ENABLE_DOCUMENT_SEARCH=True
ENABLE_SP_SEARCH=True
```

## Kullanım

### 1. Giriş Yapma

İlk kullanımda test kullanıcısı ile giriş yapabilirsiniz:
- **Kullanıcı Adı**: ahmet.yilmaz
- **Şifre**: 12345

Veya yeni bir hesap oluşturabilirsiniz.

### 2. Soru Sorma

Chat arayüzünde sorularınızı yazın:
- "Kalan izin hakkım kaç gün?"
- "Maaşım ne zaman yatacak?"
- "Üzerimdeki zimmetler neler?"

### 3. Hızlı Sorular

Ana ekranda bulunan hızlı soru butonlarını kullanabilirsiniz.

### 4. Doküman Ekleme

Talimat dokümanlarınızı `documents/` klasörüne ekleyin. Desteklenen formatlar:
- PDF (.pdf)
- Word (.docx, .doc)
- Excel (.xlsx, .xls)
- PowerPoint (.pptx, .ppt)
- Metin (.txt)

## API Endpoints

### Kimlik Doğrulama
```
POST /api/auth/register       # Kullanıcı kaydı
POST /api/auth/login          # Kullanıcı girişi
GET  /api/auth/verify         # Token doğrulama
```

### Chatbot
```
POST   /api/chat/ask          # Soru sor
GET    /api/chat/history      # Sohbet geçmişi
DELETE /api/chat/clear        # Geçmişi temizle
```

### Dokümanlar
```
GET  /api/documents           # Doküman listesi
POST /api/documents/search    # Dokümanlarda ara
```

### Yönetim
```
GET /api/admin/soru-turleri      # Soru türlerini listele
GET /api/admin/soru-eslesmeleri  # Soru eşleştirmelerini listele
```

## Yeni Soru Türü Ekleme

### 1. Veritabanına Ekle

```sql
-- Yeni soru türü ekle
INSERT INTO SORU_TURLERI (Kod, Aciklama, AktifMi)
VALUES ('YENI_SORU_TURU', 'Yeni soru türü açıklaması', 1);

-- Soru eşleştirmeleri ekle
INSERT INTO SORU_ESLESMELERI (SoruTurId, OrnekSoru)
VALUES
    ((SELECT Id FROM SORU_TURLERI WHERE Kod = 'YENI_SORU_TURU'), 'örnek soru 1'),
    ((SELECT Id FROM SORU_TURLERI WHERE Kod = 'YENI_SORU_TURU'), 'örnek soru 2');
```

### 2. Stored Procedure'u Güncelle

`database/create_sp.sql` dosyasındaki `sp_SoruCevap` prosedürüne yeni ELSE IF bloğu ekleyin:

```sql
ELSE IF @SoruTurKod = 'YENI_SORU_TURU'
BEGIN
    -- Özel işlemler
    SET @Cevap = 'Yanıtınız burada...'
END
```

## Geliştirme ve Test

### Backend Testleri

```bash
# Test modüllerini çalıştır
python backend/config.py       # Konfigürasyon testi
python backend/database.py     # Veritabanı testi
python backend/auth.py         # Auth testi
python backend/chatbot.py      # Chatbot testi
```

### Debug Modu

`.env` dosyasında `DEBUG=True` yaparak detaylı log çıktıları alabilirsiniz.

## Güvenlik

- Tüm şifreler bcrypt ile hash'lenir
- JWT token tabanlı kimlik doğrulama
- SQL injection koruması (parametreli sorgular)
- CORS ayarları
- HTTPS kullanımı önerilir (production ortamında)

## Performans Optimizasyonu

- Veritabanı indexleri optimize edilmiş
- Connection pooling kullanımı
- Doküman okuma önbellekleme
- API rate limiting (production için önerilir)

## Sorun Giderme

### Veritabanı Bağlantı Hatası

```bash
# ODBC Driver kontrolü
odbcinst -q -d

# Bağlantı string'i test et
python -c "import pyodbc; print(pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=ChatBotDB;UID=sa;PWD=YourPassword'))"
```

### OpenAI API Hatası

- API key'inizin geçerli olduğundan emin olun
- API kullanım limitinizi kontrol edin
- İnternet bağlantınızı kontrol edin

### Port Kullanımda Hatası

```bash
# Başka bir port kullanın
PORT=8000 python backend/app.py
```

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## Destek

Sorularınız için:
- Issue açın: [GitHub Issues]
- Email: support@firma.com

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## Changelog

### v1.0.0 (2024)
- İlk sürüm
- ChatGPT entegrasyonu
- MSSQL veritabanı desteği
- Doküman okuma özellikleri
- Web arayüzü

## Gelecek Özellikler

- [ ] Çoklu dil desteği
- [ ] Sesli komut desteği
- [ ] Mobile uygulama
- [ ] Admin panel
- [ ] Analitik dashboard
- [ ] E-posta bildirimleri
- [ ] Slack/Teams entegrasyonu
- [ ] Vector database (embeddings) entegrasyonu

---

**Geliştirici**: AI Chatbot Team
**Son Güncelleme**: 2024
