-- =============================================
-- Doküman Yönetimi Tabloları
-- RAG (Retrieval-Augmented Generation) Sistemi için
-- =============================================

-- Database adı .env'den gelecek, default TESTDB
USE TESTDB;
GO

-- =============================================
-- DOSYALAR Tablosu
-- Yüklenen Word ve PDF dosyalarının bilgileri
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DOSYALAR')
BEGIN
    CREATE TABLE DOSYALAR (
        DosyaId INT IDENTITY(1,1) PRIMARY KEY,
        DosyaAdi NVARCHAR(255) NOT NULL,
        DosyaYolu NVARCHAR(500) NOT NULL,
        DosyaTipi NVARCHAR(10) NOT NULL, -- .pdf, .docx
        Boyut BIGINT NOT NULL, -- Byte cinsinden
        YukleyenTcKimlikNo NVARCHAR(11) NOT NULL,
        YuklenmeTarihi DATETIME DEFAULT GETDATE(),
        IslenmeDurumu INT DEFAULT 0, -- 0: Bekliyor, 1: İşlendi, 2: Hata
        IslenmeHatasi NVARCHAR(MAX) NULL,
        ChunkSayisi INT DEFAULT 0,
        AktifMi BIT DEFAULT 1,
        SilinmeTarihi DATETIME NULL

        -- NOT: Cross-database FK desteklenmiyor, manual olarak kontrol edilecek
        -- CONSTRAINT FK_DOSYALAR_Yukleyen FOREIGN KEY (YukleyenTcKimlikNo)
        --     REFERENCES KNS_IK.dbo.Calisan(TcKimlikNo)
    );

    PRINT 'DOSYALAR tablosu oluşturuldu.';
END
ELSE
BEGIN
    PRINT 'DOSYALAR tablosu zaten mevcut.';
END
GO

-- =============================================
-- DOKUMAN_CHUNKS Tablosu
-- Doküman metinlerinin parçaları (chunks)
-- Vector embeddings buraya kaydedilecek
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DOKUMAN_CHUNKS')
BEGIN
    CREATE TABLE DOKUMAN_CHUNKS (
        ChunkId INT IDENTITY(1,1) PRIMARY KEY,
        DosyaId INT NOT NULL,
        ChunkMetni NVARCHAR(MAX) NOT NULL,
        ChunkIndex INT NOT NULL, -- Chunk'ın sırası
        KarakterSayisi INT NOT NULL,
        -- Embedding bilgileri JSON olarak saklanacak
        -- FAISS index'i file system'de, metadata burada
        EmbeddingOlusturuldu BIT DEFAULT 0,
        OlusturmaTarihi DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_DOKUMAN_CHUNKS_Dosya FOREIGN KEY (DosyaId)
            REFERENCES DOSYALAR(DosyaId) ON DELETE CASCADE
    );

    -- Index for faster queries
    CREATE INDEX IX_DOKUMAN_CHUNKS_DosyaId ON DOKUMAN_CHUNKS(DosyaId);
    CREATE INDEX IX_DOKUMAN_CHUNKS_EmbeddingOlusturuldu ON DOKUMAN_CHUNKS(EmbeddingOlusturuldu);

    PRINT 'DOKUMAN_CHUNKS tablosu oluşturuldu.';
END
ELSE
BEGIN
    PRINT 'DOKUMAN_CHUNKS tablosu zaten mevcut.';
END
GO

-- =============================================
-- DOKUMAN_SORGULARI Tablosu
-- Kullanıcıların doküman tabanlı sorguları
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DOKUMAN_SORGULARI')
BEGIN
    CREATE TABLE DOKUMAN_SORGULARI (
        SorguId INT IDENTITY(1,1) PRIMARY KEY,
        TcKimlikNo NVARCHAR(11) NOT NULL,
        SessionId NVARCHAR(50) NULL,
        Soru NVARCHAR(MAX) NOT NULL,
        Cevap NVARCHAR(MAX) NOT NULL,
        KullanilanChunklar NVARCHAR(MAX) NULL, -- JSON: [chunkId1, chunkId2, ...]
        SimilarityScore FLOAT NULL, -- En yüksek benzerlik skoru
        SorguTarihi DATETIME DEFAULT GETDATE(),
        CevapSuresi INT NULL -- Millisecond

        -- NOT: Cross-database FK desteklenmiyor
        -- CONSTRAINT FK_DOKUMAN_SORGULARI_Kullanici FOREIGN KEY (TcKimlikNo)
        --     REFERENCES KNS_IK.dbo.Calisan(TcKimlikNo)
    );

    -- Indexes
    CREATE INDEX IX_DOKUMAN_SORGULARI_TcKimlikNo ON DOKUMAN_SORGULARI(TcKimlikNo);
    CREATE INDEX IX_DOKUMAN_SORGULARI_SessionId ON DOKUMAN_SORGULARI(SessionId);
    CREATE INDEX IX_DOKUMAN_SORGULARI_SorguTarihi ON DOKUMAN_SORGULARI(SorguTarihi);

    PRINT 'DOKUMAN_SORGULARI tablosu oluşturuldu.';
END
ELSE
BEGIN
    PRINT 'DOKUMAN_SORGULARI tablosu zaten mevcut.';
END
GO

-- =============================================
-- View: Dosya İstatistikleri
-- =============================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'VW_DOSYA_ISTATISTIKLERI')
    DROP VIEW VW_DOSYA_ISTATISTIKLERI;
GO

CREATE VIEW VW_DOSYA_ISTATISTIKLERI AS
SELECT
    d.DosyaId,
    d.DosyaAdi,
    d.DosyaTipi,
    d.Boyut,
    d.YukleyenTcKimlikNo,
    c.AdSoyad AS YukleyenAdi,
    d.YuklenmeTarihi,
    d.IslenmeDurumu,
    d.ChunkSayisi,
    d.AktifMi,
    COUNT(dc.ChunkId) AS GercekChunkSayisi,
    SUM(CASE WHEN dc.EmbeddingOlusturuldu = 1 THEN 1 ELSE 0 END) AS IslenenmisChunkSayisi
FROM
    DOSYALAR d
    LEFT JOIN KNS_IK.dbo.Calisan c ON d.YukleyenTcKimlikNo = c.TcKimlikNo
    LEFT JOIN DOKUMAN_CHUNKS dc ON d.DosyaId = dc.DosyaId
WHERE
    d.AktifMi = 1
GROUP BY
    d.DosyaId, d.DosyaAdi, d.DosyaTipi, d.Boyut, d.YukleyenTcKimlikNo,
    c.AdSoyad, d.YuklenmeTarihi, d.IslenmeDurumu, d.ChunkSayisi, d.AktifMi;
GO

PRINT 'VW_DOSYA_ISTATISTIKLERI view''u oluşturuldu.';
GO

-- =============================================
-- Stored Procedure: Dosya Yükleme
-- =============================================
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'SP_DosyaYukle')
    DROP PROCEDURE SP_DosyaYukle;
GO

CREATE PROCEDURE SP_DosyaYukle
    @DosyaAdi NVARCHAR(255),
    @DosyaYolu NVARCHAR(500),
    @DosyaTipi NVARCHAR(10),
    @Boyut BIGINT,
    @YukleyenTcKimlikNo NVARCHAR(11),
    @DosyaId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        INSERT INTO DOSYALAR (DosyaAdi, DosyaYolu, DosyaTipi, Boyut, YukleyenTcKimlikNo)
        VALUES (@DosyaAdi, @DosyaYolu, @DosyaTipi, @Boyut, @YukleyenTcKimlikNo);

        SET @DosyaId = SCOPE_IDENTITY();

        -- Log (ISLEM_LOG tablosuna kaydet)
        IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ISLEM_LOG')
        BEGIN
            INSERT INTO ISLEM_LOG (TcKimlikNo, Islem, Aciklama, IslemTarihi)
            VALUES (@YukleyenTcKimlikNo, 'Dosya Yükleme',
                    'Dosya: ' + @DosyaAdi + ', ID: ' + CAST(@DosyaId AS NVARCHAR(10)),
                    GETDATE());
        END
    END TRY
    BEGIN CATCH
        SET @DosyaId = -1;
        THROW;
    END CATCH
END
GO

PRINT 'SP_DosyaYukle stored procedure''u oluşturuldu.';
GO

-- =============================================
-- Stored Procedure: Chunk Kaydetme
-- =============================================
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'SP_ChunkKaydet')
    DROP PROCEDURE SP_ChunkKaydet;
GO

CREATE PROCEDURE SP_ChunkKaydet
    @DosyaId INT,
    @ChunkMetni NVARCHAR(MAX),
    @ChunkIndex INT,
    @ChunkId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        DECLARE @KarakterSayisi INT = LEN(@ChunkMetni);

        INSERT INTO DOKUMAN_CHUNKS (DosyaId, ChunkMetni, ChunkIndex, KarakterSayisi)
        VALUES (@DosyaId, @ChunkMetni, @ChunkIndex, @KarakterSayisi);

        SET @ChunkId = SCOPE_IDENTITY();

        -- Dosya chunk sayısını güncelle
        UPDATE DOSYALAR
        SET ChunkSayisi = (SELECT COUNT(*) FROM DOKUMAN_CHUNKS WHERE DosyaId = @DosyaId)
        WHERE DosyaId = @DosyaId;
    END TRY
    BEGIN CATCH
        SET @ChunkId = -1;
        THROW;
    END CATCH
END
GO

PRINT 'SP_ChunkKaydet stored procedure''u oluşturuldu.';
GO

-- =============================================
-- Stored Procedure: Dosya İşleme Durumu Güncelleme
-- =============================================
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'SP_DosyaIslemeDurumuGuncelle')
    DROP PROCEDURE SP_DosyaIslemeDurumuGuncelle;
GO

CREATE PROCEDURE SP_DosyaIslemeDurumuGuncelle
    @DosyaId INT,
    @IslenmeDurumu INT,
    @IslenmeHatasi NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE DOSYALAR
    SET
        IslenmeDurumu = @IslenmeDurumu,
        IslenmeHatasi = @IslenmeHatasi
    WHERE
        DosyaId = @DosyaId;
END
GO

PRINT 'SP_DosyaIslemeDurumuGuncelle stored procedure''u oluşturuldu.';
GO

-- =============================================
-- Test Data (Opsiyonel - Sadece development için)
-- =============================================
-- INSERT INTO DOSYALAR (DosyaAdi, DosyaYolu, DosyaTipi, Boyut, YukleyenTcKimlikNo)
-- VALUES ('test.pdf', '/uploads/test.pdf', '.pdf', 1024, '12345678901');

PRINT '========================================';
PRINT 'Doküman yönetimi tabloları hazır!';
PRINT '========================================';
GO
