#!/usr/bin/env python3
"""
Admin tablosu oluşturma scripti
"""
import pyodbc
import sys

# Connection string
conn_str = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=10.0.54.21,1433;DATABASE=TESTDB;UID=ChatBotUser;PWD=Kns1234?;Encrypt=yes;TrustServerCertificate=yes;"

# SQL script
sql_script = """
-- ADMIN_KULLANICILAR tablosu
IF OBJECT_ID('dbo.ADMIN_KULLANICILAR', 'U') IS NOT NULL
    DROP TABLE dbo.ADMIN_KULLANICILAR;

CREATE TABLE dbo.ADMIN_KULLANICILAR (
    Id INT PRIMARY KEY IDENTITY(1,1),
    TcKimlikNo NVARCHAR(11) NOT NULL UNIQUE,
    EklenmeTarihi DATETIME NOT NULL DEFAULT GETDATE(),
    AktifMi BIT NOT NULL DEFAULT 1
);

-- Index ekle
CREATE INDEX IX_ADMIN_KULLANICILAR_TcKimlikNo ON dbo.ADMIN_KULLANICILAR(TcKimlikNo);

-- Test kullanıcısını admin olarak ekle (TC: 65968234430)
INSERT INTO dbo.ADMIN_KULLANICILAR (TcKimlikNo, AktifMi)
VALUES ('65968234430', 1);

SELECT 'ADMIN_KULLANICILAR tablosu oluşturuldu' AS Mesaj;
SELECT 'Admin kullanıcı eklendi: 65968234430' AS Mesaj;
"""

try:
    print("Veritabanına bağlanılıyor...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    print("SQL scripti çalıştırılıyor...")

    # Split by semicolon and execute each statement
    statements = [s.strip() for s in sql_script.split(';') if s.strip()]

    for statement in statements:
        if statement:
            print(f"\nÇalıştırılıyor: {statement[:50]}...")
            cursor.execute(statement)

            # Try to fetch results if any
            try:
                if cursor.description:
                    results = cursor.fetchall()
                    for row in results:
                        print(f"  -> {row[0]}")
            except:
                pass

    conn.commit()
    print("\n✓ Tüm SQL komutları başarıyla çalıştırıldı!")

    # Verify
    cursor.execute("SELECT COUNT(*) FROM ADMIN_KULLANICILAR")
    count = cursor.fetchone()[0]
    print(f"\n✓ ADMIN_KULLANICILAR tablosunda {count} kayıt var")

    cursor.execute("SELECT TcKimlikNo, EklenmeTarihi FROM ADMIN_KULLANICILAR")
    for row in cursor.fetchall():
        print(f"  - Admin: {row[0]} (Eklenme: {row[1]})")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n✗ Hata: {str(e)}")
    sys.exit(1)
