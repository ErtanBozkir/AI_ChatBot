
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER PROCEDURE [dbo].[SP_SoruCevap]
   @TcKimlikNo NVARCHAR(50), 
   @Soru NVARCHAR(MAX),
   @Cevap NVARCHAR(MAX) OUTPUT,
   @SoruTurKod NVARCHAR(50) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @BaslangicZamani DATETIME = GETDATE();
    DECLARE @IslemSuresi INT;
    DECLARE @HataMesaji NVARCHAR(MAX);
	declare @SoruTurId int

    BEGIN TRY
        -- Değişkenleri sıfırla
        SET @Cevap = NULL;
        SET @SoruTurKod = NULL;
        SET @SoruTurId = NULL;

        -- 1. SORU EŞLEŞTİRME
        -- Soru metnini analiz ederek en uygun soru türünü bul
        IF @Soru LIKE N'%izin%' OR @Soru LIKE N'%İzin%' OR @Soru LIKE N'%yıllık%'
        BEGIN
            SELECT @SoruTurId = Id, @SoruTurKod = Kod
            FROM dbo.SoruTurleri
            WHERE Kod = 'IZIN_HAKKI_SORGULA' AND AktifMi = 1;
        END
        ELSE IF @Soru LIKE N'%maaş%' OR @Soru LIKE N'%bordro%' OR @Soru LIKE N'%ücret%'
        BEGIN
            SELECT @SoruTurId = Id, @SoruTurKod = Kod
            FROM dbo.SoruTurleri
            WHERE Kod = 'MAAS_BORDRO_SORGULA' AND AktifMi = 1;
        END
        ELSE IF @Soru LIKE N'%zimmet%' OR @Soru LIKE N'%ekipman%' OR @Soru LIKE N'%demirbaş%'
        BEGIN
            SELECT @SoruTurId = Id, @SoruTurKod = Kod
            FROM dbo.SoruTurleri
            WHERE Kod = 'ZIMMET_SORGULA' AND AktifMi = 1;
        END
        ELSE IF @Soru LIKE N'%eğitim%' OR @Soru LIKE N'%kurs%' OR @Soru LIKE N'%seminer%'
        BEGIN
            SELECT @SoruTurId = Id, @SoruTurKod = Kod
            FROM dbo.SoruTurleri
            WHERE Kod = 'EGITIM_TALEP' AND AktifMi = 1;
        END
        ELSE IF @Soru LIKE N'%stok%' OR @Soru LIKE N'%ürün%' OR @Soru LIKE N'%envanter%'
        BEGIN
            SELECT @SoruTurId = Id, @SoruTurKod = Kod
            FROM dbo.SoruTurleri
            WHERE Kod = 'STOK_BILGISI_SORGULA' AND AktifMi = 1;
        END

		declare @CalisanId int
		select @CalisanId = Id
		from KNS_IK.dbo.Calisan 
		where TcKimlikNo = @TcKimlikNo and AktifMi = 1

        -- 2. SORU TÜRÜNE GÖRE YANIT ÜRET
        IF @SoruTurKod IS NOT NULL
        BEGIN
            -- Burada soru türüne göre özel yanıtlar oluşturulur

            IF @SoruTurKod = 'IZIN_HAKKI_SORGULA'
            BEGIN
                create table #TempIzinBakiyeRaporu(CalisanId int, IzinTipiId int, ToplamHakEdisBakiye decimal(30, 2), ToplamKullanilanIzin decimal(30, 2), KalanIzinBakiye decimal(30, 2)) 
						
				exec KNS_IK.dbo.IzinBakiyesiGetir @sp_CalisanId = @CalisanId, @sp_IzinTipiId = 1, @sp_RaporTuru = 'İzin Bakiye Raporu'

				set @Cevap = ''
				select @Cevap = it.Adi + ' Hakkınız: ' + cast(i.KalanIzinBakiye as varchar(100)) + ' Gün Kalmıştır.'
				from #TempIzinBakiyeRaporu i left join KNS_IK.dbo.IzinTipi it with(nolock) on it.Id = i.IzinTipiId
											 left join KNS_IK.dbo.Calisan c with(nolock) on c.Id = i.CalisanId

                /*SET @Cevap = N'İzin hakkınız: ' + CAST(@IzinHakki AS NVARCHAR(10)) + N' gün. ' +
                            N'Kullanılmış izin: 59 gün. Kalan: ' + CAST((@IzinHakki - 5) AS NVARCHAR(10)) + N' gün.';*/
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
        INSERT INTO dbo.SOHBETLER (TcKimlikNo, Soru, Cevap, SoruTurId, Tarih, IslemSuresi)
        VALUES (@TcKimlikNo, @Soru, @Cevap, @SoruTurId, GETDATE(), @IslemSuresi);

        -- 5. İŞLEM LOGU
        INSERT INTO dbo.ISLEM_LOG (TcKimlikNo, Islem, Detay, Tarih, HataMi)
        VALUES (@TcKimlikNo, 'SP_SoruCevap',
                N'Soru türü: ' + ISNULL(@SoruTurKod, 'YOK') + N', İşlem süresi: ' + CAST(@IslemSuresi AS NVARCHAR(10)) + 'ms',
                GETDATE(), 0);

        RETURN 0;  -- Başarılı

    END TRY
    BEGIN CATCH
        -- Hata yakalama
        SET @HataMesaji = ERROR_MESSAGE();

        INSERT INTO dbo.ISLEM_LOG (TcKimlikNo, Islem, Detay, Tarih, HataMi)
        VALUES (@TcKimlikNo, 'SP_SoruCevap HATA', @HataMesaji, GETDATE(), 1);

        SET @Cevap = N'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.';

        RETURN -1;  -- Hata
    END CATCH
END
