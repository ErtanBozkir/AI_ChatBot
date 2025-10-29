-- ============================================
-- Firma Chatbot Örnek Veriler
-- ============================================

USE ChatBotDB;
GO

PRINT 'Örnek veriler ekleniyor...';
GO

-- ============================================
-- 1. Örnek Kullanıcılar
-- Şifre: "12345" için bcrypt hash örneği
-- Gerçek uygulamada Python ile hash üretilmeli
-- ============================================

-- Test kullanıcıları
INSERT INTO dbo.KULLANICILAR (KullaniciAdi, SifreHash, Eposta, KayitTarihi, AktifMi)
VALUES
    ('ahmet.yilmaz', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfXJ8K7eSa', 'ahmet.yilmaz@firma.com', GETDATE(), 1),
    ('ayse.demir', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfXJ8K7eSa', 'ayse.demir@firma.com', GETDATE(), 1),
    ('mehmet.kaya', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfXJ8K7eSa', 'mehmet.kaya@firma.com', GETDATE(), 1),
    ('fatma.can', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfXJ8K7eSa', 'fatma.can@firma.com', GETDATE(), 1),
    ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfXJ8K7eSa', 'admin@firma.com', GETDATE(), 1);

PRINT 'Kullanıcılar eklendi.';
GO

-- ============================================
-- 2. Soru Türleri
-- ============================================

INSERT INTO dbo.SORU_TURLERI (Kod, Aciklama, AktifMi, OlusturmaTarihi)
VALUES
    ('IZIN_HAKKI_SORGULA', 'Kullanıcının kalan izin hakkını sorgular', 1, GETDATE()),
    ('STOK_BILGISI_SORGULA', 'Ürün stok bilgilerini sorgular', 1, GETDATE()),
    ('MAAS_BORDRO_SORGULA', 'Maaş ve bordro bilgilerini sorgular', 1, GETDATE()),
    ('ZIMMET_SORGULA', 'Zimmet bilgilerini sorgular', 1, GETDATE()),
    ('EGITIM_TALEP', 'Eğitim talepleri için', 1, GETDATE()),
    ('DEPARTMAN_BILGI', 'Departman iletişim bilgileri', 1, GETDATE()),
    ('MESAI_SORGULA', 'Mesai saatleri ve fazla mesai sorguları', 1, GETDATE()),
    ('AVANS_TALEP', 'Avans talepleri için', 1, GETDATE()),
    ('GENEL_BILGI', 'Genel bilgilendirme soruları', 1, GETDATE()),
    ('IT_DESTEK', 'BT destek talepleri', 1, GETDATE());

PRINT 'Soru türleri eklendi.';
GO

-- ============================================
-- 3. Soru Eşleştirmeleri
-- Kullanıcıların sorabileceği örnek sorular
-- ============================================

DECLARE @IzinHakkiId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'IZIN_HAKKI_SORGULA');
DECLARE @StokBilgisiId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'STOK_BILGISI_SORGULA');
DECLARE @MaasBordroId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'MAAS_BORDRO_SORGULA');
DECLARE @ZimmetId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'ZIMMET_SORGULA');
DECLARE @EgitimId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'EGITIM_TALEP');
DECLARE @DepartmanId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'DEPARTMAN_BILGI');
DECLARE @MesaiId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'MESAI_SORGULA');
DECLARE @AvansId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'AVANS_TALEP');
DECLARE @GenelBilgiId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'GENEL_BILGI');
DECLARE @ITDestekId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'IT_DESTEK');

-- İzin Hakkı Sorguları
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@IzinHakkiId, 'izin hakkı', GETDATE()),
    (@IzinHakkiId, 'kaç gün izin', GETDATE()),
    (@IzinHakkiId, 'kalan izin', GETDATE()),
    (@IzinHakkiId, 'iznim var mı', GETDATE()),
    (@IzinHakkiId, 'yıllık izin', GETDATE());

-- Stok Bilgisi Sorguları
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@StokBilgisiId, 'stok durumu', GETDATE()),
    (@StokBilgisiId, 'ürün stok', GETDATE()),
    (@StokBilgisiId, 'kaç adet var', GETDATE()),
    (@StokBilgisiId, 'depoda var mı', GETDATE());

-- Maaş Bordro Sorguları
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@MaasBordroId, 'maaş', GETDATE()),
    (@MaasBordroId, 'bordro', GETDATE()),
    (@MaasBordroId, 'ücret', GETDATE()),
    (@MaasBordroId, 'maaşım ne zaman', GETDATE());

-- Zimmet Sorguları
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@ZimmetId, 'zimmet', GETDATE()),
    (@ZimmetId, 'üzerimde kayıtlı', GETDATE()),
    (@ZimmetId, 'ekipman', GETDATE()),
    (@ZimmetId, 'laptop', GETDATE());

-- Eğitim Talepleri
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@EgitimId, 'eğitim almak', GETDATE()),
    (@EgitimId, 'kurs', GETDATE()),
    (@EgitimId, 'sertifika programı', GETDATE()),
    (@EgitimId, 'eğitim talebi', GETDATE());

-- Departman Bilgileri
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@DepartmanId, 'hangi departman', GETDATE()),
    (@DepartmanId, 'iletişim bilgisi', GETDATE()),
    (@DepartmanId, 'telefon numarası', GETDATE()),
    (@DepartmanId, 'kime ulaşabilirim', GETDATE());

-- Mesai Sorguları
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@MesaiId, 'mesai saati', GETDATE()),
    (@MesaiId, 'fazla mesai', GETDATE()),
    (@MesaiId, 'çalışma saatleri', GETDATE()),
    (@MesaiId, 'ne zaman çalışıyorum', GETDATE());

-- Avans Talepleri
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@AvansId, 'avans', GETDATE()),
    (@AvansId, 'kredi', GETDATE()),
    (@AvansId, 'ödünç', GETDATE());

-- Genel Bilgi
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@GenelBilgiId, 'bilgi almak', GETDATE()),
    (@GenelBilgiId, 'yardım', GETDATE()),
    (@GenelBilgiId, 'nasıl yapabilirim', GETDATE());

-- IT Destek
INSERT INTO dbo.SORU_ESLESMELERI (SoruTurId, OrnekSoru, OlusturmaTarihi)
VALUES
    (@ITDestekId, 'bilgisayar', GETDATE()),
    (@ITDestekId, 'internet', GETDATE()),
    (@ITDestekId, 'şifre', GETDATE()),
    (@ITDestekId, 'teknik destek', GETDATE()),
    (@ITDestekId, 'sistem', GETDATE());

PRINT 'Soru eşleştirmeleri eklendi.';
GO

-- ============================================
-- 4. Örnek Sohbet Geçmişi
-- ============================================

DECLARE @KullaniciId INT = (SELECT TOP 1 Id FROM dbo.KULLANICILAR WHERE KullaniciAdi = 'ahmet.yilmaz');
DECLARE @SoruTurId INT = (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'IZIN_HAKKI_SORGULA');

INSERT INTO dbo.SOHBETLER (KullaniciId, Soru, Cevap, SoruTurId, Tarih, IslemSuresi)
VALUES
    (@KullaniciId, 'Kalan izin hakkım ne kadar?', 'İzin hakkınız: 15 gün. Kullanılmış izin: 5 gün. Kalan: 10 gün.', @SoruTurId, DATEADD(DAY, -2, GETDATE()), 125),
    (@KullaniciId, 'Maaşım ne zaman yatacak?', 'Maaş ve bordro bilgileriniz İnsan Kaynakları departmanı tarafından her ayın 25-28''i arasında sisteme yüklenmektedir.',
     (SELECT Id FROM dbo.SORU_TURLERI WHERE Kod = 'MAAS_BORDRO_SORGULA'), DATEADD(DAY, -1, GETDATE()), 98);

PRINT 'Örnek sohbet geçmişi eklendi.';
GO

-- ============================================
-- 5. Örnek İşlem Logları
-- ============================================

INSERT INTO dbo.ISLEM_LOG (KullaniciId, Islem, Detay, Tarih, HataMi)
VALUES
    (@KullaniciId, 'Kullanıcı Girişi', 'Başarılı giriş', DATEADD(HOUR, -2, GETDATE()), 0),
    (@KullaniciId, 'sp_SoruCevap', 'Soru türü: IZIN_HAKKI_SORGULA, İşlem süresi: 125ms', DATEADD(HOUR, -1, GETDATE()), 0),
    (NULL, 'Sistem Başlatma', 'Chatbot sistemi başlatıldı', DATEADD(DAY, -1, GETDATE()), 0);

PRINT 'Örnek işlem logları eklendi.';
GO

-- ============================================
-- Veri Kontrolü
-- ============================================

PRINT '';
PRINT '=== VERİ ÖZET RAPORU ===';
PRINT 'Kullanıcı sayısı: ' + CAST((SELECT COUNT(*) FROM dbo.KULLANICILAR) AS VARCHAR(10));
PRINT 'Soru türü sayısı: ' + CAST((SELECT COUNT(*) FROM dbo.SORU_TURLERI) AS VARCHAR(10));
PRINT 'Soru eşleştirme sayısı: ' + CAST((SELECT COUNT(*) FROM dbo.SORU_ESLESMELERI) AS VARCHAR(10));
PRINT 'Sohbet geçmişi sayısı: ' + CAST((SELECT COUNT(*) FROM dbo.SOHBETLER) AS VARCHAR(10));
PRINT 'Log kaydı sayısı: ' + CAST((SELECT COUNT(*) FROM dbo.ISLEM_LOG) AS VARCHAR(10));
PRINT '';
PRINT 'Tüm örnek veriler başarıyla eklendi!';
PRINT '';
PRINT 'Test için kullanıcı bilgileri:';
PRINT '  Kullanıcı adı: ahmet.yilmaz';
PRINT '  Şifre: 12345';
GO
