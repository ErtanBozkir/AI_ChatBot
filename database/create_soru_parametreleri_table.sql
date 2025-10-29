-- SORU_PARAMETRELERI tablosu: Her soru türünün hangi parametreleri aldığını tanımlar

IF OBJECT_ID('dbo.SORU_PARAMETRELERI', 'U') IS NOT NULL
    DROP TABLE dbo.SORU_PARAMETRELERI;
GO

CREATE TABLE dbo.SORU_PARAMETRELERI (
    Id INT PRIMARY KEY IDENTITY(1,1),
    SoruTurKod NVARCHAR(50) NOT NULL,
    ParametreAdi NVARCHAR(50) NOT NULL,
    VeriTipi NVARCHAR(20) NOT NULL, -- 'TEXT', 'NUMBER', 'DATE'
    ZorunluMu BIT NOT NULL DEFAULT 1,
    Aciklama NVARCHAR(255) NULL,
    OrnekDeger NVARCHAR(100) NULL
);
GO

CREATE INDEX IX_SORU_PARAMETRELERI_SoruTurKod ON dbo.SORU_PARAMETRELERI(SoruTurKod);
GO

-- Örnek parametreler
INSERT INTO dbo.SORU_PARAMETRELERI (SoruTurKod, ParametreAdi, VeriTipi, ZorunluMu, Aciklama, OrnekDeger)
VALUES
    -- Stok bakiye sorgulama
    ('STOK_BILGISI_SORGULA', 'stok_kod', 'TEXT', 1, 'Ürün/Stok kodu', '6-01PM-5245-AA'),
    ('STOK_BILGISI_SORGULA', 'depo_kod', 'TEXT', 0, 'Depo kodu (opsiyonel, belirtilmezse tüm depolar)', 'SATINALMA'),

    -- İzin hakkı (parametre gerekmiyor, TC kimlikten otomatik)
    -- ('IZIN_HAKKI_SORGULA', 'tc_kimlik_no', 'TEXT', 1, 'TC Kimlik No', '11111111111'),

    -- Maaş bordro
    ('MAAS_BORDRO_SORGULA', 'ay', 'NUMBER', 0, 'Ay bilgisi (1-12)', '9'),
    ('MAAS_BORDRO_SORGULA', 'yil', 'NUMBER', 0, 'Yıl bilgisi', '2025'),

    -- Zimmet sorgulama
    ('ZIMMET_SORGULA', 'ekipman_tipi', 'TEXT', 0, 'Ekipman türü', 'Laptop'),

    -- Eğitim talep
    ('EGITIM_TALEP', 'egitim_konusu', 'TEXT', 0, 'Eğitim konusu', 'Python'),

    -- Mesai sorgulama
    ('MESAI_SORGULA', 'baslangic_tarih', 'DATE', 0, 'Başlangıç tarihi', '2025-01-01'),
    ('MESAI_SORGULA', 'bitis_tarih', 'DATE', 0, 'Bitiş tarihi', '2025-01-31');
GO
