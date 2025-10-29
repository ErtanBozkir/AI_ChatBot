-- ============================================
-- Firma Chatbot Stored Procedures
-- ============================================

USE ChatBotDB;
GO

-- ============================================
-- SP: sp_SoruCevap
-- Kullanıcının sorusunu alır, eşleştirme yapar ve cevap döner
-- ============================================

IF OBJECT_ID('dbo.sp_SoruCevap', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_SoruCevap;
GO

CREATE PROCEDURE dbo.sp_SoruCevap
    @KullaniciId INT,
    @Soru NVARCHAR(MAX),
    @Cevap NVARCHAR(MAX) OUTPUT,
    @SoruTurKod NVARCHAR(50) OUTPUT,
    @SoruTurId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @BaslangicZamani DATETIME = GETDATE();
    DECLARE @IslemSuresi INT;
    DECLARE @HataMesaji NVARCHAR(MAX);

    BEGIN TRY
        -- Değişkenleri sıfırla
        SET @Cevap = NULL;
        SET @SoruTurKod = NULL;
        SET @SoruTurId = NULL;

        -- 1. SORU EŞLEŞTİRME
        -- En uygun soru türünü bul (LIKE ile basit eşleştirme)
        SELECT TOP 1
            @SoruTurId = ST.Id,
            @SoruTurKod = ST.Kod
        FROM dbo.SORU_ESLESMELERI SE
        INNER JOIN dbo.SORU_TURLERI ST ON SE.SoruTurId = ST.Id
        WHERE ST.AktifMi = 1
            AND (
                @Soru LIKE '%' + SE.OrnekSoru + '%'
                OR SOUNDEX(@Soru) = SOUNDEX(SE.OrnekSoru)  -- Fonetik benzerlik
            )
        ORDER BY LEN(SE.OrnekSoru) DESC;  -- Daha uzun eşleşmelere öncelik

        -- 2. SORU TÜRÜNE GÖRE YANIT ÜRET
        IF @SoruTurKod IS NOT NULL
        BEGIN
            -- Burada soru türüne göre özel yanıtlar oluşturulur

            IF @SoruTurKod = 'IZIN_HAKKI_SORGULA'
            BEGIN
                -- Örnek: İzin hakkı sorgulama
                -- Gerçek uygulamada burası başka bir SP çağrısı veya tablo sorgusu olabilir
                DECLARE @IzinHakki INT = 15;  -- Demo değer

                SET @Cevap = N'İzin hakkınız: ' + CAST(@IzinHakki AS NVARCHAR(10)) + N' gün. ' +
                            N'Kullanılmış izin: 5 gün. Kalan: ' + CAST((@IzinHakki - 5) AS NVARCHAR(10)) + N' gün.';
            END

            ELSE IF @SoruTurKod = 'STOK_BILGISI_SORGULA'
            BEGIN
                -- Örnek: Stok bilgisi sorgulama
                SET @Cevap = N'Stok bilgisi sorgunuz için lütfen ürün kodunu belirtin. ' +
                            N'Örnek: "12345 kodlu ürünün stok durumu nedir?"';
            END

            ELSE IF @SoruTurKod = 'MAAS_BORDRO_SORGULA'
            BEGIN
                -- Örnek: Maaş bordro sorgulama
                SET @Cevap = N'Maaş ve bordro bilgileriniz İnsan Kaynakları departmanı tarafından ' +
                            N'her ayın 25-28''i arasında sisteme yüklenmektedir. ' +
                            N'Detaylı bilgi için IK departmanı ile iletişime geçebilirsiniz.';
            END

            ELSE IF @SoruTurKod = 'ZIMMET_SORGULA'
            BEGIN
                -- Örnek: Zimmet sorgulama
                SET @Cevap = N'Zimmetinizde kayıtlı ekipmanlar: Laptop (1 adet), Telefon (1 adet). ' +
                            N'Detaylı bilgi için Bilgi İşlem departmanını arayabilirsiniz.';
            END

            ELSE IF @SoruTurKod = 'EGITIM_TALEP'
            BEGIN
                -- Örnek: Eğitim talebi
                SET @Cevap = N'Eğitim taleplerinizi İnsan Kaynakları departmanına iletebilirsiniz. ' +
                            N'Eğitim programlarımız hakkında detaylı bilgi için: egitim@firma.com';
            END

            ELSE IF @SoruTurKod = 'GENEL_BILGI'
            BEGIN
                -- Genel bilgilendirme
                SET @Cevap = N'Bu konu hakkında size yardımcı olabilirim. ' +
                            N'Lütfen sorunuzu daha detaylı açıklar mısınız?';
            END

            ELSE
            BEGIN
                -- Tanımlanmamış soru türü - Python tarafında ChatGPT ile işlenecek
                SET @Cevap = NULL;
                SET @SoruTurKod = 'TANIMSIZ';
            END
        END
        ELSE
        BEGIN
            -- Hiçbir eşleşme bulunamadı - Python tarafında ChatGPT ile işlenecek
            SET @Cevap = NULL;
            SET @SoruTurKod = 'BILINMIYOR';
        END

        -- 3. İşlem süresini hesapla
        SET @IslemSuresi = DATEDIFF(MILLISECOND, @BaslangicZamani, GETDATE());

        -- 4. SOHBET GEÇMİŞİNE KAYDET
        INSERT INTO dbo.SOHBETLER (KullaniciId, Soru, Cevap, SoruTurId, Tarih, IslemSuresi)
        VALUES (@KullaniciId, @Soru, @Cevap, @SoruTurId, GETDATE(), @IslemSuresi);

        -- 5. İŞLEM LOGU
        INSERT INTO dbo.ISLEM_LOG (KullaniciId, Islem, Detay, Tarih, HataMi)
        VALUES (@KullaniciId, 'sp_SoruCevap',
                N'Soru türü: ' + ISNULL(@SoruTurKod, 'YOK') + N', İşlem süresi: ' + CAST(@IslemSuresi AS NVARCHAR(10)) + 'ms',
                GETDATE(), 0);

        RETURN 0;  -- Başarılı

    END TRY
    BEGIN CATCH
        -- Hata yakalama
        SET @HataMesaji = ERROR_MESSAGE();

        INSERT INTO dbo.ISLEM_LOG (KullaniciId, Islem, Detay, Tarih, HataMi)
        VALUES (@KullaniciId, 'sp_SoruCevap HATA', @HataMesaji, GETDATE(), 1);

        SET @Cevap = N'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.';

        RETURN -1;  -- Hata
    END CATCH
END
GO

-- ============================================
-- SP: sp_KullaniciGiris
-- Kullanıcı giriş kontrolü
-- ============================================

IF OBJECT_ID('dbo.sp_KullaniciGiris', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_KullaniciGiris;
GO

CREATE PROCEDURE dbo.sp_KullaniciGiris
    @KullaniciAdi NVARCHAR(50),
    @SifreHash NVARCHAR(255),
    @KullaniciId INT OUTPUT,
    @Basarili BIT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @KullaniciId = NULL;
    SET @Basarili = 0;

    -- Kullanıcıyı kontrol et
    SELECT
        @KullaniciId = Id
    FROM dbo.KULLANICILAR
    WHERE KullaniciAdi = @KullaniciAdi
        AND SifreHash = @SifreHash
        AND AktifMi = 1;

    IF @KullaniciId IS NOT NULL
    BEGIN
        SET @Basarili = 1;

        -- Başarılı giriş logu
        INSERT INTO dbo.ISLEM_LOG (KullaniciId, Islem, Detay, Tarih, HataMi)
        VALUES (@KullaniciId, 'Kullanıcı Girişi', 'Başarılı giriş', GETDATE(), 0);
    END
    ELSE
    BEGIN
        -- Başarısız giriş logu
        INSERT INTO dbo.ISLEM_LOG (KullaniciId, Islem, Detay, Tarih, HataMi)
        VALUES (NULL, 'Kullanıcı Girişi', 'Başarısız giriş denemesi: ' + @KullaniciAdi, GETDATE(), 1);
    END

    RETURN @Basarili;
END
GO

-- ============================================
-- SP: sp_SohbetGecmisiGetir
-- Kullanıcının sohbet geçmişini getirir
-- ============================================

IF OBJECT_ID('dbo.sp_SohbetGecmisiGetir', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_SohbetGecmisiGetir;
GO

CREATE PROCEDURE dbo.sp_SohbetGecmisiGetir
    @KullaniciId INT,
    @Limit INT = 50
AS
BEGIN
    SET NOCOUNT ON;

    SELECT TOP (@Limit)
        S.Id,
        S.Soru,
        S.Cevap,
        S.Tarih,
        ST.Kod AS SoruTuru,
        ST.Aciklama AS SoruAciklama,
        S.IslemSuresi
    FROM dbo.SOHBETLER S
    LEFT JOIN dbo.SORU_TURLERI ST ON S.SoruTurId = ST.Id
    WHERE S.KullaniciId = @KullaniciId
    ORDER BY S.Tarih DESC;
END
GO

PRINT 'Tüm stored procedure''lar başarıyla oluşturuldu!';
GO
