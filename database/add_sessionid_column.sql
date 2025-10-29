-- SOHBETLER tablosuna SessionId kolonu ekle
USE TESTDB;
GO

-- SessionId kolonu ekle (varsa ekleme)
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID('SOHBETLER')
    AND name = 'SessionId'
)
BEGIN
    ALTER TABLE SOHBETLER
    ADD SessionId NVARCHAR(50) NULL;

    PRINT 'SessionId kolonu eklendi';
END
ELSE
BEGIN
    PRINT 'SessionId kolonu zaten mevcut';
END
GO

-- Index ekle
IF NOT EXISTS (
    SELECT * FROM sys.indexes
    WHERE name = 'IX_SOHBETLER_SessionId'
    AND object_id = OBJECT_ID('SOHBETLER')
)
BEGIN
    CREATE INDEX IX_SOHBETLER_SessionId
    ON SOHBETLER(SessionId, Tarih);

    PRINT 'Index oluşturuldu';
END
GO

-- Mevcut kayıtlar için SessionId üret (her kayda unique)
UPDATE SOHBETLER
SET SessionId = NEWID()
WHERE SessionId IS NULL;
GO

PRINT 'SessionId kolonu hazır!';
