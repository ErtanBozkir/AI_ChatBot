-- ============================================
-- Firma Chatbot Veritabanı Tabloları
-- ============================================

-- Veritabanı oluştur (eğer yoksa)
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ChatBotDB')
BEGIN
    CREATE DATABASE ChatBotDB;
END
GO

USE ChatBotDB;
GO

-- ============================================
-- 1. KULLANICILAR Tablosu
-- ============================================
IF OBJECT_ID('dbo.KULLANICILAR', 'U') IS NOT NULL
    DROP TABLE dbo.KULLANICILAR;
GO

CREATE TABLE dbo.KULLANICILAR (
    Id INT PRIMARY KEY IDENTITY(1,1),
    KullaniciAdi NVARCHAR(50) NOT NULL UNIQUE,
    SifreHash NVARCHAR(255) NOT NULL,
    Eposta NVARCHAR(100) NOT NULL UNIQUE,
    KayitTarihi DATETIME NOT NULL DEFAULT GETDATE(),
    AktifMi BIT NOT NULL DEFAULT 1,
    CONSTRAINT CK_KULLANICILAR_Eposta CHECK (Eposta LIKE '%@%.%')
);
GO

-- Index oluştur
CREATE INDEX IX_KULLANICILAR_KullaniciAdi ON dbo.KULLANICILAR(KullaniciAdi);
CREATE INDEX IX_KULLANICILAR_Eposta ON dbo.KULLANICILAR(Eposta);
GO

-- ============================================
-- 2. SORU_TURLERI Tablosu
-- ============================================
IF OBJECT_ID('dbo.SORU_TURLERI', 'U') IS NOT NULL
    DROP TABLE dbo.SORU_TURLERI;
GO

CREATE TABLE dbo.SORU_TURLERI (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Kod NVARCHAR(50) NOT NULL UNIQUE,
    Aciklama NVARCHAR(255) NULL,
    AktifMi BIT NOT NULL DEFAULT 1,
    OlusturmaTarihi DATETIME NOT NULL DEFAULT GETDATE()
);
GO

CREATE INDEX IX_SORU_TURLERI_Kod ON dbo.SORU_TURLERI(Kod);
GO

-- ============================================
-- 3. SORU_ESLESMELERI Tablosu
-- ============================================
IF OBJECT_ID('dbo.SORU_ESLESMELERI', 'U') IS NOT NULL
    DROP TABLE dbo.SORU_ESLESMELERI;
GO

CREATE TABLE dbo.SORU_ESLESMELERI (
    Id INT PRIMARY KEY IDENTITY(1,1),
    SoruTurId INT NOT NULL,
    OrnekSoru NVARCHAR(500) NOT NULL,
    OlusturmaTarihi DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_SORU_ESLESMELERI_SoruTurId
        FOREIGN KEY (SoruTurId) REFERENCES dbo.SORU_TURLERI(Id)
        ON DELETE CASCADE
);
GO

CREATE INDEX IX_SORU_ESLESMELERI_SoruTurId ON dbo.SORU_ESLESMELERI(SoruTurId);
GO

-- ============================================
-- 4. SOHBETLER Tablosu
-- ============================================
IF OBJECT_ID('dbo.SOHBETLER', 'U') IS NOT NULL
    DROP TABLE dbo.SOHBETLER;
GO

CREATE TABLE dbo.SOHBETLER (
    Id INT PRIMARY KEY IDENTITY(1,1),
    KullaniciId INT NOT NULL,
    Soru NVARCHAR(MAX) NOT NULL,
    Cevap NVARCHAR(MAX) NULL,
    SoruTurId INT NULL,
    Tarih DATETIME NOT NULL DEFAULT GETDATE(),
    IslemSuresi INT NULL, -- Milisaniye cinsinden
    CONSTRAINT FK_SOHBETLER_KullaniciId
        FOREIGN KEY (KullaniciId) REFERENCES dbo.KULLANICILAR(Id)
        ON DELETE CASCADE,
    CONSTRAINT FK_SOHBETLER_SoruTurId
        FOREIGN KEY (SoruTurId) REFERENCES dbo.SORU_TURLERI(Id)
        ON DELETE SET NULL
);
GO

CREATE INDEX IX_SOHBETLER_KullaniciId ON dbo.SOHBETLER(KullaniciId);
CREATE INDEX IX_SOHBETLER_Tarih ON dbo.SOHBETLER(Tarih DESC);
CREATE INDEX IX_SOHBETLER_SoruTurId ON dbo.SOHBETLER(SoruTurId);
GO

-- ============================================
-- 5. ISLEM_LOG Tablosu
-- ============================================
IF OBJECT_ID('dbo.ISLEM_LOG', 'U') IS NOT NULL
    DROP TABLE dbo.ISLEM_LOG;
GO

CREATE TABLE dbo.ISLEM_LOG (
    Id INT PRIMARY KEY IDENTITY(1,1),
    KullaniciId INT NULL,
    Islem NVARCHAR(255) NOT NULL,
    Detay NVARCHAR(MAX) NULL,
    Tarih DATETIME NOT NULL DEFAULT GETDATE(),
    HataMi BIT NOT NULL DEFAULT 0,
    CONSTRAINT FK_ISLEM_LOG_KullaniciId
        FOREIGN KEY (KullaniciId) REFERENCES dbo.KULLANICILAR(Id)
        ON DELETE SET NULL
);
GO

CREATE INDEX IX_ISLEM_LOG_KullaniciId ON dbo.ISLEM_LOG(KullaniciId);
CREATE INDEX IX_ISLEM_LOG_Tarih ON dbo.ISLEM_LOG(Tarih DESC);
CREATE INDEX IX_ISLEM_LOG_HataMi ON dbo.ISLEM_LOG(HataMi);
GO

-- ============================================
-- 6. SESSION Tablosu (JWT yerine opsiyonel)
-- ============================================
IF OBJECT_ID('dbo.SESSIONS', 'U') IS NOT NULL
    DROP TABLE dbo.SESSIONS;
GO

CREATE TABLE dbo.SESSIONS (
    Id INT PRIMARY KEY IDENTITY(1,1),
    KullaniciId INT NOT NULL,
    Token NVARCHAR(500) NOT NULL UNIQUE,
    OlusturmaTarihi DATETIME NOT NULL DEFAULT GETDATE(),
    SonKullanim DATETIME NOT NULL,
    AktifMi BIT NOT NULL DEFAULT 1,
    CONSTRAINT FK_SESSIONS_KullaniciId
        FOREIGN KEY (KullaniciId) REFERENCES dbo.KULLANICILAR(Id)
        ON DELETE CASCADE
);
GO

CREATE INDEX IX_SESSIONS_Token ON dbo.SESSIONS(Token);
CREATE INDEX IX_SESSIONS_KullaniciId ON dbo.SESSIONS(KullaniciId);
GO

PRINT 'Tüm tablolar başarıyla oluşturuldu!';
GO
