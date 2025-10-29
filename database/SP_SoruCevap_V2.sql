
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- Versiyon 2: JSON parametrelerle çalışan soru-cevap stored procedure
CREATE OR ALTER PROCEDURE [dbo].[SP_SoruCevap_V2]
   @TcKimlikNo NVARCHAR(50),
   @Soru NVARCHAR(MAX),
   @SoruTurKod NVARCHAR(50),  -- ChatGPT'den gelen soru türü
   @ParametrelerJSON NVARCHAR(MAX),  -- ChatGPT'den gelen parametreler (JSON)
   @Cevap NVARCHAR(MAX) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @BaslangicZamani DATETIME = GETDATE();
    DECLARE @IslemSuresi INT;
    DECLARE @HataMesaji NVARCHAR(MAX);
    DECLARE @SoruTurId INT;
    DECLARE @CalisanId INT;

    BEGIN TRY
        -- Değişkenleri sıfırla
        SET @Cevap = NULL;
        SET @SoruTurId = NULL;

        -- Soru türü ID'sini bul
        SELECT @SoruTurId = Id
        FROM dbo.SoruTurleri
        WHERE Kod = @SoruTurKod AND AktifMi = 1;

        -- Çalışan ID'sini bul
        SELECT @CalisanId = Id
        FROM KNS_IK.dbo.Calisan
        WHERE TcKimlikNo = @TcKimlikNo AND AktifMi = 1;

        -- SORU TÜRÜNE GÖRE YANIT ÜRET
        IF @SoruTurKod = 'IZIN_HAKKI_SORGULA'
        BEGIN
            -- İzin bakiyesi sorgulama
            CREATE TABLE #TempIzinBakiyeRaporu(
                CalisanId INT,
                IzinTipiId INT,
                ToplamHakEdisBakiye DECIMAL(30, 2),
                ToplamKullanilanIzin DECIMAL(30, 2),
                KalanIzinBakiye DECIMAL(30, 2)
            );

            EXEC KNS_IK.dbo.IzinBakiyesiGetir
                @sp_CalisanId = @CalisanId,
                @sp_IzinTipiId = 1,
                @sp_RaporTuru = 'İzin Bakiye Raporu';

            SET @Cevap = '';
            SELECT @Cevap = it.Adi + ' Hakkınız: ' + CAST(i.KalanIzinBakiye AS VARCHAR(100)) + ' Gün Kalmıştır.'
            FROM #TempIzinBakiyeRaporu i
            LEFT JOIN KNS_IK.dbo.IzinTipi it WITH(NOLOCK) ON it.Id = i.IzinTipiId
            LEFT JOIN KNS_IK.dbo.Calisan c WITH(NOLOCK) ON c.Id = i.CalisanId;

            DROP TABLE #TempIzinBakiyeRaporu;
        END

        ELSE IF @SoruTurKod = 'STOK_BILGISI_SORGULA'
        BEGIN
            -- JSON'dan parametreleri çıkar
            DECLARE @StokKod NVARCHAR(100);
            DECLARE @DepoKod NVARCHAR(100);
            DECLARE @Bakiye DECIMAL(18,2);
            DECLARE @StokTanim NVARCHAR(255);

            -- JSON parse et
            SELECT @StokKod = JSON_VALUE(@ParametrelerJSON, '$.stok_kod');
            SELECT @DepoKod = JSON_VALUE(@ParametrelerJSON, '$.depo_kod');

            -- Stok kodu zorunlu
            IF @StokKod IS NULL
            BEGIN
                SET @Cevap = N'Stok sorgulama için stok kodu belirtmelisiniz. ' +
                            N'Örnek: "6-01PM-5245-AA kodlu ürünün stoğu nedir?"';
            END
            ELSE
            BEGIN
                -- Ürün tanımını al
                SELECT TOP 1 @StokTanim = sk.Isim
                FROM ORAES.dbo.StokKarti sk WITH(NOLOCK)
                WHERE sk.Sirket_Kod = 'tzyKNS' AND sk.Kod = @StokKod;

                -- DEPO BELİRTİLMİŞSE: Sadece o depodaki stoku göster
                IF @DepoKod IS NOT NULL
                BEGIN
                    SELECT @Bakiye = sb.Bakiye
                    FROM ORAES.dbo.StokBakiyeleri sb WITH(NOLOCK)
                    WHERE sb.Sirket_Kod = 'tzyKNS'
                        AND sb.StokKod = @StokKod
                        AND sb.DepoKod = @DepoKod;

                    IF @Bakiye IS NOT NULL
                    BEGIN
                        SET @Cevap = N'📦 Stok Bilgisi:' + CHAR(13) + CHAR(10) +
                                    N'Ürün: ' + ISNULL(@StokTanim, @StokKod) + CHAR(13) + CHAR(10) +
                                    N'Stok Kodu: ' + @StokKod + CHAR(13) + CHAR(10) +
                                    N'Depo: ' + @DepoKod + CHAR(13) + CHAR(10) +
                                    N'Bakiye: ' + CAST(@Bakiye AS NVARCHAR(50)) + N' adet';
                    END
                    ELSE
                    BEGIN
                        SET @Cevap = N'❌ ' + @StokKod + N' kodlu ürün için ' + @DepoKod +
                                    N' deposunda stok kaydı bulunamadı.';
                    END
                END
                -- DEPO BELİRTİLMEMİŞSE: Tüm depolardaki stokları listele
                ELSE
                BEGIN
                    DECLARE @ToplamBakiye DECIMAL(18,2);
                    DECLARE @DepoSayisi INT;

                    -- Toplam bakiye ve depo sayısını hesapla
                    SELECT
                        @ToplamBakiye = SUM(sb.Bakiye),
                        @DepoSayisi = COUNT(DISTINCT sb.DepoKod)
                    FROM ORAES.dbo.StokBakiyeleri sb WITH(NOLOCK)
                    WHERE sb.Sirket_Kod = 'tzyKNS'
                        AND sb.StokKod = @StokKod
                        AND sb.Bakiye > 0;

                    IF @ToplamBakiye > 0
                    BEGIN
                        SET @Cevap = N'📦 Stok Bilgisi:' + CHAR(13) + CHAR(10) +
                                    N'Ürün: ' + ISNULL(@StokTanim, @StokKod) + CHAR(13) + CHAR(10) +
                                    N'Stok Kodu: ' + @StokKod + CHAR(13) + CHAR(10) +
                                    N'Toplam Bakiye: ' + CAST(@ToplamBakiye AS NVARCHAR(50)) + N' adet' +
                                    N' (' + CAST(@DepoSayisi AS NVARCHAR(10)) + N' depoda)' +
                                    CHAR(13) + CHAR(10) + CHAR(13) + CHAR(10) +
                                    N'Depo Detayları:' + CHAR(13) + CHAR(10);

                        -- Her depo için bakiye ekle (cursor kullanarak)
                        DECLARE @DepoTemp NVARCHAR(50);
                        DECLARE @BakiyeTemp DECIMAL(18,2);

                        DECLARE depo_cursor CURSOR FOR
                        SELECT DepoKod, Bakiye
                        FROM ORAES.dbo.StokBakiyeleri WITH(NOLOCK)
                        WHERE Sirket_Kod = 'tzyKNS'
                            AND StokKod = @StokKod
                            AND Bakiye > 0
                        ORDER BY Bakiye DESC;

                        OPEN depo_cursor;
                        FETCH NEXT FROM depo_cursor INTO @DepoTemp, @BakiyeTemp;

                        WHILE @@FETCH_STATUS = 0
                        BEGIN
                            SET @Cevap = @Cevap +
                                        N'  • ' + @DepoTemp + N': ' +
                                        CAST(@BakiyeTemp AS NVARCHAR(50)) + N' adet' +
                                        CHAR(13) + CHAR(10);

                            FETCH NEXT FROM depo_cursor INTO @DepoTemp, @BakiyeTemp;
                        END

                        CLOSE depo_cursor;
                        DEALLOCATE depo_cursor;
                    END
                    ELSE
                    BEGIN
                        SET @Cevap = N'❌ ' + @StokKod + N' kodlu ürün için hiçbir depoda stok bulunamadı.';
                    END
                END
            END
        END

        ELSE IF @SoruTurKod = 'MAAS_BORDRO_SORGULA'
        BEGIN
            -- Bordro sorgulama (parametrelerle genişletilebilir)
            DECLARE @Ay INT;
            DECLARE @Yil INT;

            SELECT @Ay = CAST(JSON_VALUE(@ParametrelerJSON, '$.ay') AS INT);
            SELECT @Yil = CAST(JSON_VALUE(@ParametrelerJSON, '$.yil') AS INT);

            IF @Ay IS NOT NULL AND @Yil IS NOT NULL
            BEGIN
                SET @Cevap = N'Maaş ve bordro bilgileriniz İnsan Kaynakları departmanı tarafından ' +
                            N'her ayın 25-28''i arasında sisteme yüklenmektedir. ' +
                            CAST(@Ay AS NVARCHAR(2)) + N'/' + CAST(@Yil AS NVARCHAR(4)) +
                            N' dönemi için detaylı bilgi için IK departmanı ile iletişime geçebilirsiniz.';
            END
            ELSE
            BEGIN
                SET @Cevap = N'Maaş ve bordro bilgileriniz İnsan Kaynakları departmanı tarafından ' +
                            N'her ayın 25-28''i arasında sisteme yüklenmektedir. ' +
                            N'Detaylı bilgi için IK departmanı ile iletişime geçebilirsiniz.';
            END
        END

        ELSE IF @SoruTurKod = 'ZIMMET_SORGULA'
        BEGIN
            ------------------------------------------------------------------
            -- ZIMMET SORGULAMA – DETAYLI LİSTE (Depo listesi gibi)
            ------------------------------------------------------------------
            DECLARE @EkipmanTipi NVARCHAR(100);
            SELECT @EkipmanTipi = JSON_VALUE(@ParametrelerJSON, '$.ekipman_tipi');

            -- Geçici tablo: SP_KNS_Zimmetler sonuçlarını tutacak
            CREATE TABLE #TempZimmetler (
                TCNo            NVARCHAR(4000),
                AdSoyad         NVARCHAR(4000),
                Atolye          NVARCHAR(4000),
                ZimmetTarihi    DATE,
                StokKod         NVARCHAR(4000),
                StokTanim       NVARCHAR(4000),
                Marka           NVARCHAR(4000),
                Model           NVARCHAR(4000),
                Miktar          FLOAT,
                DepoKod         NVARCHAR(4000),
                MalzemeGrubu1   NVARCHAR(4000),
                MalzemeGrubu2   NVARCHAR(4000),
                MalzemeGrubu3   NVARCHAR(4000)
            );

            -- SP'yi çalıştırıp tüm zimmetleri tabloya doldur
            INSERT INTO #TempZimmetler
            EXEC [ORAES].[dbo].[SP_KNS_Zimmetler];

            ------------------------------------------------------------------
            -- Başlık
            ------------------------------------------------------------------
            SET @Cevap = N'📋 **Zimmet Listesi**' + CHAR(13)+CHAR(10)+CHAR(13)+CHAR(10);

            

            ------------------------------------------------------------------
            -- Cursor ile satır satır ekle
            ------------------------------------------------------------------
            DECLARE @Tarih   NVARCHAR(12),
                    @Tanim   NVARCHAR(255),
                    @Marka   NVARCHAR(100),
                    @Model   NVARCHAR(100),
                    @Miktar  NVARCHAR(30),
                    @Depo    NVARCHAR(50);

            DECLARE zimmet_cursor CURSOR LOCAL FAST_FORWARD FOR
                SELECT 
                    CONVERT(NVARCHAR(10), ZimmetTarihi, 104) AS Tarih,
                    StokKod,
                    ISNULL(StokTanim, StokKod)               AS Tanim,
                    ISNULL(Marka, '-')                     AS Marka,
                    ISNULL(Model, '-')                     AS Model,
                    CAST(Miktar AS NVARCHAR(20)) + ' adet' AS Miktar,
                    ISNULL(DepoKod, '-')                   AS Depo
                FROM #TempZimmetler
                WHERE TCNo = @TcKimlikNo
				ORDER BY ZimmetTarihi DESC, StokKod

            OPEN zimmet_cursor;
            FETCH NEXT FROM zimmet_cursor INTO @Tarih, @StokKod, @Tanim, @Marka, @Model, @Miktar, @Depo;

            IF @@FETCH_STATUS <> 0
            BEGIN
                -- Hiç kayıt yoksa
                SET @Cevap = @Cevap + N'❌ Zimmet kaydınız bulunamadı.';
            END
            ELSE
            BEGIN
                WHILE @@FETCH_STATUS = 0
                BEGIN
                    SET @Cevap = @Cevap +
                                N'• **' + @Tarih + N'** – ' +
                                ISNULL(@Tanim, @StokKod) + N'  ' +
                                N'(' + @Marka + N' ' + @Model + N')' + CHAR(13)+CHAR(10) +
                                N'   Miktar: ' + @Miktar + CHAR(13)+CHAR(10) + CHAR(13)+CHAR(10);

                    FETCH NEXT FROM zimmet_cursor INTO @Tarih, @StokKod, @Tanim, @Marka, @Model, @Miktar, @Depo;
                END
            END

            CLOSE zimmet_cursor;
            DEALLOCATE zimmet_cursor;

            DROP TABLE #TempZimmetler;
        END

        -- ... diğer bloklar ve CATCH kısmı aynı kalır ...

        ELSE IF @SoruTurKod = 'EGITIM_TALEP'
        BEGIN
            DECLARE @EgitimKonusu NVARCHAR(255);
            SELECT @EgitimKonusu = JSON_VALUE(@ParametrelerJSON, '$.egitim_konusu');

            IF @EgitimKonusu IS NOT NULL
            BEGIN
                SET @Cevap = N'Eğitim talebiniz (' + @EgitimKonusu + N') İnsan Kaynakları departmanına iletilecektir. ' +
                            N'Eğitim programlarımız hakkında detaylı bilgi için: ik@knsotomotiv.com';
            END
            ELSE
            BEGIN
                SET @Cevap = N'Eğitim taleplerinizi İnsan Kaynakları departmanına iletebilirsiniz. ' +
                            N'Eğitim programlarımız hakkında detaylı bilgi için: ik@knsotomotiv.com';
            END
        END

        ELSE IF @SoruTurKod = 'GENEL_BILGI'
        BEGIN
            SET @Cevap = N'Bu konu hakkında size yardımcı olabilirim. ' +
                        N'Lütfen sorunuzu daha detaylı açıklar mısınız?';
        END

        ELSE
        BEGIN
            -- Tanımlanmamış soru türü - Python tarafında ChatGPT ile işlenecek
            SET @Cevap = NULL;
        END

        -- İşlem süresini hesapla
        SET @IslemSuresi = DATEDIFF(MILLISECOND, @BaslangicZamani, GETDATE());

        -- SOHBET GEÇMİŞİNE KAYDET
        INSERT INTO dbo.Sohbetler (TcKimlikNo, Soru, Cevap, SoruTurId, Tarih, IslemSuresi)
        VALUES (@TcKimlikNo, @Soru, @Cevap, @SoruTurId, GETDATE(), @IslemSuresi);

        -- İŞLEM LOGU
        INSERT INTO dbo.ISLEM_LOG (TcKimlikNo, Islem, Detay, Tarih, HataMi)
        VALUES (@TcKimlikNo, 'SP_SoruCevap_V2',
                N'Soru türü: ' + ISNULL(@SoruTurKod, 'YOK') + N', Parametreler: ' + ISNULL(@ParametrelerJSON, '{}') +
                N', İşlem süresi: ' + CAST(@IslemSuresi AS NVARCHAR(10)) + 'ms',
                GETDATE(), 0);

        RETURN 0;  -- Başarılı

    END TRY
    BEGIN CATCH
        -- Hata yakalama
        SET @HataMesaji = ERROR_MESSAGE();

        INSERT INTO dbo.ISLEM_LOG (TcKimlikNo, Islem, Detay, Tarih, HataMi)
        VALUES (@TcKimlikNo, 'SP_SoruCevap_V2 HATA', @HataMesaji, GETDATE(), 1);

        SET @Cevap = N'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin. Hata: ' + @HataMesaji;

        RETURN -1;  -- Hata
    END CATCH
END
GO
