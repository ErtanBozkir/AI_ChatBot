# 🚀 Firma Chatbot - Windows Kurulum Rehberi

Bu rehber, chatbot'u kendi bilgisayarınızda çalıştırmak için gereken tüm adımları içerir.

## 📋 Gereksinimler

- **Windows 10 veya üzeri**
- **Python 3.8 veya üzeri** (Python yoksa aşağıdan indirin)

---

## 🔽 Adım 1: Python Kurulumu

Eğer Python kurulu değilse:

1. **Python İndir:**
   - https://www.python.org/downloads/ adresine gidin
   - "Download Python 3.x.x" butonuna tıklayın
   - İndirilen dosyayı çalıştırın

2. **Kurulum Sırasında ÖNEMLİ:**
   - ✅ **"Add Python to PATH"** kutucuğunu işaretleyin!
   - "Install Now" tıklayın
   - Kurulum bittiğinde "Close" tıklayın

3. **Python Kontrolü:**
   - `Win + R` tuşlarına basın
   - `cmd` yazıp Enter'a basın
   - Açılan siyah pencerede şunu yazın:
     ```
     python --version
     ```
   - Python 3.8 veya üzeri görüyorsanız hazırsınız!

---

## 📦 Adım 2: Projeyi İndirin

### Seçenek A: Git ile İndirme (Önerilen)

```bash
# Komut satırını açın (cmd)
git clone <your-repo-url>
cd AI_ChatBot
```

### Seçenek B: ZIP ile İndirme

1. GitHub'daki projeyi açın
2. Yeşil "Code" butonuna tıklayın
3. "Download ZIP" seçin
4. ZIP dosyasını çıkarın
5. Çıkarılan klasörü açın

---

## ⚙️ Adım 3: Otomatik Kurulum (TEK TIK!)

Proje klasörüne geldikten sonra:

### 1️⃣ Paketleri Yükleyin

`install.bat` dosyasına **çift tıklayın**

- Siyah bir pencere açılacak
- Paketler otomatik yüklenecek (5-10 saniye)
- "BASARILI" mesajı görünce bir tuşa basın

### 2️⃣ Veritabanını Oluşturun

`setup_database.bat` dosyasına **çift tıklayın**

- Test veritabanı oluşturulacak (2 saniye)
- Test kullanıcıları eklenecek
- "BASARILI" mesajı görünce bir tuşa basın

### 3️⃣ Sunucuyu Başlatın

`start.bat` dosyasına **çift tıklayın**

- Sunucu başlayacak
- Tarayıcınızda otomatik açılacak (veya manuel açın)

**URL:** http://localhost:5000

---

## 🎯 Adım 4: Giriş Yapın ve Test Edin

Tarayıcınızda http://localhost:5000 açıldığında:

### Giriş Bilgileri:
```
Kullanıcı Adı: ahmet.yilmaz
Şifre: 12345
```

### Test Soruları:
```
✅ Kalan izin hakkım kaç gün?
✅ Maaşım ne zaman yatacak?
✅ Üzerimdeki zimmetler neler?
✅ Eğitim almak istiyorum
✅ Merhaba!
```

---

## 🔧 Manuel Kurulum (Alternatif)

Eğer .bat dosyaları çalışmazsa, komut satırından manuel olarak:

### 1. Komut Satırını Açın
```bash
# Windows tuşu + R
# "cmd" yazın ve Enter
# Proje klasörüne gidin:
cd C:\Users\YourUsername\AI_ChatBot
```

### 2. Paketleri Yükleyin
```bash
pip install -r requirements_test.txt
```

### 3. Veritabanını Oluşturun
```bash
python test_setup.py
```

### 4. Sunucuyu Başlatın
```bash
python simple_test_app.py
```

### 5. Tarayıcıda Açın
```
http://localhost:5000
```

---

## ❓ Sorun Giderme

### Python Bulunamadı Hatası

**Hata:** `'python' is not recognized...`

**Çözüm:**
1. Python'u tekrar kurun
2. Kurulumda "Add Python to PATH" seçeneğini işaretleyin
3. Bilgisayarı yeniden başlatın

### Paket Yükleme Hatası

**Hata:** `error: Microsoft Visual C++ 14.0 is required`

**Çözüm:**
```bash
pip install --upgrade pip
pip install -r requirements_test.txt
```

### Port Kullanımda Hatası

**Hata:** `Address already in use`

**Çözüm:**
- Başka bir program 5000 portunu kullanıyor
- O programı kapatın veya
- `simple_test_app.py` dosyasında PORT değerini değiştirin (örn: 5001)

### Tarayıcı Açılmıyor

**Çözüm:**
- Manuel olarak şu adresi açın: http://localhost:5000
- Veya: http://127.0.0.1:5000

---

## 🎬 Kısa Özet (Hızlı Başlangıç)

```bash
# 1. Python 3.8+ yükleyin (python.org)
# 2. Projeyi indirin
# 3. Proje klasöründe:

install.bat              # Çift tık - Paketleri yükle
setup_database.bat       # Çift tık - Veritabanı oluştur
start.bat                # Çift tık - Sunucu başlat

# 4. Tarayıcıda aç: http://localhost:5000
# 5. Giriş: ahmet.yilmaz / 12345
```

---

## 📞 Yardım

Sorun yaşıyorsanız:

1. **Hata mesajını** tam olarak kopyalayın
2. **Hangi adımda** hata aldığınızı belirtin
3. **Python versiyonunuzu** kontrol edin: `python --version`

---

## 🌟 Özellikler

✅ **Kullanıcı Girişi** - Güvenli kimlik doğrulama
✅ **Akıllı Soru-Cevap** - İzin, maaş, zimmet sorguları
✅ **Sohbet Geçmişi** - Tüm konuşmalar kaydedilir
✅ **Modern Arayüz** - Web tabanlı, responsive
✅ **Offline Çalışır** - İnternet bağlantısı gerektirmez
✅ **Mock AI** - OpenAI API key'e ihtiyaç yok

---

## 🎉 Başarıyla Kuruldu!

Artık firma chatbot'unuz hazır! Keyifli kullanımlar! 🚀

**İlk sorunuzu sorun ve yapay zeka asistanınızla sohbet edin!**
