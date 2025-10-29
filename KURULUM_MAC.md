# 🍎 Firma Chatbot - MacBook Kurulum Rehberi

Mac kullanıcıları için özel hazırlanmış kurulum rehberi.

## 📋 Gereksinimler

- **MacOS** (herhangi bir versiyon)
- **Python 3.8+** (genellikle Mac'te zaten yüklüdür)

---

## ✅ Hızlı Kurulum (3 ADIM)

### 1️⃣ Terminal'i Açın

**Finder** → **Uygulamalar** → **Yardımcı Programlar** → **Terminal**

veya

**Spotlight** (Cmd + Space) → "Terminal" yazın → Enter

---

### 2️⃣ Proje Klasörüne Gidin

Terminal'de şunu yazın (projenizin olduğu yolu yazın):

```bash
cd ~/Downloads/AI_ChatBot
```

veya Finder'da klasörü bulup Terminal'e sürükleyin.

---

### 3️⃣ Kurulum Scriptlerini Çalıştırın

Terminal'de sırasıyla şu komutları yazın:

```bash
# Adım 1: Paketleri yükle (10 saniye)
bash install.sh

# Adım 2: Veritabanını oluştur (2 saniye)
bash setup_database.sh

# Adım 3: Sunucuyu başlat (HEMEN AÇILIR!)
bash start.sh
```

**Tarayıcınızda otomatik açılır:** http://localhost:5000

---

## 🔐 Giriş Bilgileri

```
Kullanıcı Adı: ahmet.yilmaz
Şifre: 12345
```

---

## 📝 Detaylı Adım Adım

### Python Kontrolü

Terminal'de şunu yazın:

```bash
python3 --version
```

**Çıktı:** `Python 3.8.x` veya üzeri görmelisiniz.

**Python yoksa:**
```bash
# Homebrew ile yükleyin
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3
```

---

### Kurulum Adımları

#### 1. Proje Klasörüne Git

```bash
# Downloads'a indirdiyseniz:
cd ~/Downloads/AI_ChatBot

# Masaüstüne indirdiyseniz:
cd ~/Desktop/AI_ChatBot

# Veya tam yolu yazın:
cd /Users/YourUsername/path/to/AI_ChatBot
```

#### 2. Script İzinlerini Kontrol Et

```bash
# Scriptleri çalıştırılabilir yap
chmod +x install.sh setup_database.sh start.sh
```

#### 3. Paketleri Yükle

```bash
bash install.sh
```

**Çıktı:**
```
================================================
FIRMA CHATBOT - KURULUM
================================================

Python paketleri yükleniyor...

[BAŞARILI] Tüm paketler yüklendi!
```

#### 4. Veritabanını Oluştur

```bash
bash setup_database.sh
```

**Çıktı:**
```
================================================
VERİTABANI OLUŞTURULUYOR
================================================

SQLite veritabanı oluşturuluyor...
✓ Tablolar oluşturuldu
✓ Test kullanıcıları eklendi
✓ Soru türleri eklendi

[BAŞARILI] Veritabanı hazır!
Test kullanıcısı: ahmet.yilmaz
Şifre: 12345
```

#### 5. Sunucuyu Başlat

```bash
bash start.sh
```

**Çıktı:**
```
================================================
FIRMA CHATBOT SUNUCUSU BAŞLATILIYOR
================================================

Sunucu başlatılıyor...

Tarayıcınızda şu adresi açın:
    http://localhost:5000

Kullanıcı: ahmet.yilmaz
Şifre: 12345
```

#### 6. Tarayıcıyı Aç

Safari, Chrome veya Firefox'ta şu adresi açın:

```
http://localhost:5000
```

---

## 🎯 Tek Komut ile Kurulum

Hepsini tek seferde çalıştırmak isterseniz:

```bash
cd ~/Downloads/AI_ChatBot && \
bash install.sh && \
bash setup_database.sh && \
bash start.sh
```

---

## 🛑 Sunucuyu Durdurmak

Terminal'de **Ctrl + C** tuşlarına basın.

---

## ❓ Sorun Giderme

### "Permission Denied" Hatası

```bash
chmod +x install.sh setup_database.sh start.sh
bash install.sh
```

### pip3 Bulunamadı

```bash
# Python3 ile pip kurulumu
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

### Port Kullanımda

Port 5000 başka bir uygulama tarafından kullanılıyorsa:

```bash
# Hangi program kullanıyor?
lsof -i :5000

# O programı kapatın veya
# simple_test_app.py içinde PORT=5001 yapın
```

### SSL Certificate Hatası

```bash
# Sertifikaları güncelle
/Applications/Python\ 3.x/Install\ Certificates.command
```

### "xcrun: error" Hatası

```bash
# Xcode Command Line Tools yükle
xcode-select --install
```

---

## 🖥️ Terminal İpuçları

### Klasöre Hızlı Git

Finder'da klasörü sağ tık → **"Hizmetler"** → **"Terminal'de Aç"**

### Geçmişi Temizle

```bash
clear
```

### Çalışan Python Processleri

```bash
ps aux | grep python
```

---

## 🎬 Video Anlatım (Adım Adım)

### 1. Terminal Aç
```
Spotlight (Cmd+Space) → "Terminal" → Enter
```

### 2. Klasöre Git
```bash
cd ~/Downloads/AI_ChatBot
```

### 3. Kur ve Çalıştır
```bash
bash install.sh
bash setup_database.sh
bash start.sh
```

### 4. Tarayıcı Aç
```
Safari → http://localhost:5000
```

### 5. Giriş Yap
```
Kullanıcı: ahmet.yilmaz
Şifre: 12345
```

---

## 📱 Mac Klavye Kısayolları

- **Terminal Aç:** Cmd + Space → "Terminal"
- **Kopyala:** Cmd + C
- **Yapıştır (Terminal):** Cmd + V
- **Temizle (Terminal):** Cmd + K
- **Yeni Terminal:** Cmd + T
- **Çıkış:** Ctrl + C

---

## 🌟 Hızlı Başlangıç Scripti

Kolaylık için masaüstünüze script ekleyin:

```bash
# Masaüstüne script oluştur
cat > ~/Desktop/chatbot-start.command << 'EOF'
#!/bin/bash
cd ~/Downloads/AI_ChatBot
bash start.sh
EOF

# Çalıştırılabilir yap
chmod +x ~/Desktop/chatbot-start.command
```

Artık **masaüstündeki ikona çift tıklayarak** sunucuyu başlatabilirsiniz!

---

## ✅ Kurulum Tamamlandı!

Şimdi şunları yapabilirsiniz:

✅ **http://localhost:5000** adresine gidin
✅ **ahmet.yilmaz / 12345** ile giriş yapın
✅ Chatbot'a soru sorun!

### Örnek Sorular:

```
✅ Kalan izin hakkım kaç gün?
✅ Maaşım ne zaman yatacak?
✅ Üzerimdeki zimmetler neler?
✅ Eğitim almak istiyorum
```

---

## 🎉 Başarıyla Çalışıyor!

Terminal'de şunu görüyorsanız her şey hazır:

```
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

**Safari'de http://localhost:5000 adresini açın ve chatbot'u test edin!**

---

## 📞 Yardım

Sorun yaşıyorsanız:

1. Terminal'deki **tam hata mesajını** kopyalayın
2. Python versiyonunuzu kontrol edin: `python3 --version`
3. Hangi adımda hata aldığınızı belirtin

**Hata logları:** `~/AI_ChatBot/chatbot.log`

---

## 🚀 İleri Seviye

### Arka Planda Çalıştır

```bash
nohup python3 simple_test_app.py > chatbot.log 2>&1 &
```

### Otomatik Başlatma

```bash
# Bilgisayar açıldığında otomatik başlat
# Sistem Tercihleri → Kullanıcılar ve Gruplar → Giriş Öğeleri
# chatbot-start.command dosyasını ekle
```

---

**Artık MacBook'unuzda firma chatbot'u çalışıyor!** 🎉🍎
