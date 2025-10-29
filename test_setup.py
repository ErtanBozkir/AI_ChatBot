"""
Test ortamı kurulum scripti
SQLite veritabanı ile çalışır, OpenAI API gerektirmez
"""

import sqlite3
import bcrypt
from datetime import datetime

def create_test_database():
    """SQLite test veritabanını oluşturur"""

    conn = sqlite3.connect('test_chatbot.db')
    cursor = conn.cursor()

    print("SQLite veritabanı oluşturuluyor...")

    # Tabloları oluştur
    cursor.executescript("""
        -- KULLANICILAR
        DROP TABLE IF EXISTS KULLANICILAR;
        CREATE TABLE KULLANICILAR (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            KullaniciAdi TEXT NOT NULL UNIQUE,
            SifreHash TEXT NOT NULL,
            Eposta TEXT NOT NULL UNIQUE,
            KayitTarihi TEXT NOT NULL,
            AktifMi INTEGER NOT NULL DEFAULT 1
        );

        -- SORU_TURLERI
        DROP TABLE IF EXISTS SORU_TURLERI;
        CREATE TABLE SORU_TURLERI (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Kod TEXT NOT NULL UNIQUE,
            Aciklama TEXT,
            AktifMi INTEGER NOT NULL DEFAULT 1,
            OlusturmaTarihi TEXT NOT NULL
        );

        -- SORU_ESLESMELERI
        DROP TABLE IF EXISTS SORU_ESLESMELERI;
        CREATE TABLE SORU_ESLESMELERI (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            SoruTurId INTEGER NOT NULL,
            OrnekSoru TEXT NOT NULL,
            OlusturmaTarihi TEXT NOT NULL,
            FOREIGN KEY (SoruTurId) REFERENCES SORU_TURLERI(Id)
        );

        -- SOHBETLER
        DROP TABLE IF EXISTS SOHBETLER;
        CREATE TABLE SOHBETLER (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            KullaniciId INTEGER NOT NULL,
            Soru TEXT NOT NULL,
            Cevap TEXT,
            SoruTurId INTEGER,
            Tarih TEXT NOT NULL,
            IslemSuresi INTEGER,
            FOREIGN KEY (KullaniciId) REFERENCES KULLANICILAR(Id),
            FOREIGN KEY (SoruTurId) REFERENCES SORU_TURLERI(Id)
        );

        -- ISLEM_LOG
        DROP TABLE IF EXISTS ISLEM_LOG;
        CREATE TABLE ISLEM_LOG (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            KullaniciId INTEGER,
            Islem TEXT NOT NULL,
            Detay TEXT,
            Tarih TEXT NOT NULL,
            HataMi INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (KullaniciId) REFERENCES KULLANICILAR(Id)
        );
    """)

    print("✓ Tablolar oluşturuldu")

    # Test kullanıcıları ekle (şifre: 12345)
    password = "12345"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor.executemany("""
        INSERT INTO KULLANICILAR (KullaniciAdi, SifreHash, Eposta, KayitTarihi, AktifMi)
        VALUES (?, ?, ?, ?, 1)
    """, [
        ('ahmet.yilmaz', hashed, 'ahmet.yilmaz@firma.com', datetime.now().isoformat()),
        ('test', hashed, 'test@firma.com', datetime.now().isoformat()),
        ('demo', hashed, 'demo@firma.com', datetime.now().isoformat()),
    ])

    print("✓ Test kullanıcıları eklendi")

    # Soru türleri ekle
    cursor.executemany("""
        INSERT INTO SORU_TURLERI (Kod, Aciklama, AktifMi, OlusturmaTarihi)
        VALUES (?, ?, 1, ?)
    """, [
        ('IZIN_HAKKI_SORGULA', 'İzin hakkı sorguları', datetime.now().isoformat()),
        ('MAAS_BORDRO_SORGULA', 'Maaş ve bordro sorguları', datetime.now().isoformat()),
        ('ZIMMET_SORGULA', 'Zimmet sorguları', datetime.now().isoformat()),
        ('EGITIM_TALEP', 'Eğitim talepleri', datetime.now().isoformat()),
        ('GENEL_BILGI', 'Genel bilgi', datetime.now().isoformat()),
    ])

    print("✓ Soru türleri eklendi")

    # Soru eşleştirmeleri ekle
    cursor.execute("SELECT Id FROM SORU_TURLERI WHERE Kod = 'IZIN_HAKKI_SORGULA'")
    izin_id = cursor.fetchone()[0]

    cursor.execute("SELECT Id FROM SORU_TURLERI WHERE Kod = 'MAAS_BORDRO_SORGULA'")
    maas_id = cursor.fetchone()[0]

    cursor.execute("SELECT Id FROM SORU_TURLERI WHERE Kod = 'ZIMMET_SORGULA'")
    zimmet_id = cursor.fetchone()[0]

    cursor.execute("SELECT Id FROM SORU_TURLERI WHERE Kod = 'EGITIM_TALEP'")
    egitim_id = cursor.fetchone()[0]

    cursor.executemany("""
        INSERT INTO SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
        VALUES (?, ?, ?)
    """, [
        (izin_id, 'izin', datetime.now().isoformat()),
        (izin_id, 'tatil', datetime.now().isoformat()),
        (izin_id, 'kaç gün', datetime.now().isoformat()),
        (maas_id, 'maaş', datetime.now().isoformat()),
        (maas_id, 'bordro', datetime.now().isoformat()),
        (maas_id, 'ücret', datetime.now().isoformat()),
        (zimmet_id, 'zimmet', datetime.now().isoformat()),
        (zimmet_id, 'ekipman', datetime.now().isoformat()),
        (egitim_id, 'eğitim', datetime.now().isoformat()),
        (egitim_id, 'kurs', datetime.now().isoformat()),
    ])

    print("✓ Soru eşleştirmeleri eklendi")

    conn.commit()
    conn.close()

    print("\n" + "="*50)
    print("TEST VERİTABANI HAZIR!")
    print("="*50)
    print("\nTest Kullanıcıları:")
    print("  Kullanıcı: ahmet.yilmaz / Şifre: 12345")
    print("  Kullanıcı: test / Şifre: 12345")
    print("  Kullanıcı: demo / Şifre: 12345")
    print("\n" + "="*50)

if __name__ == "__main__":
    create_test_database()
