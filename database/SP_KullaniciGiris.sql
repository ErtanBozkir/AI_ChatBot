/****** Object:  StoredProcedure [dbo].[SP_KullaniciGiris]    Script Date: 29.10.2025 21:59:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER PROCEDURE [dbo].[SP_KullaniciGiris]
    @TcKimlikNo NVARCHAR(50),
    @Sifre NVARCHAR(255),
    @Basarili BIT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

	declare @CalisanId int

    SET @CalisanId = NULL;
    SET @Basarili = 0;

    -- Kullanıcıyı kontrol et
    SELECT
        @CalisanId = Id
    FROM KNS_IK.dbo.Calisan
    WHERE TcKimlikNo = @TcKimlikNo
        AND Sifre = @Sifre
        AND AktifMi = 1;

    IF @CalisanId IS NOT NULL
    BEGIN
        SET @Basarili = 1;

        -- Başarılı giriş logu
        INSERT INTO dbo.ISLEM_LOG (TcKimlikNo, Islem, Detay, Tarih, HataMi)
        VALUES (@TcKimlikNo, 'Kullanıcı Girişi', 'Başarılı giriş', GETDATE(), 0);
    END
    ELSE
    BEGIN
        -- Başarısız giriş logu
        INSERT INTO dbo.ISLEM_LOG (TcKimlikNo, Islem, Detay, Tarih, HataMi)
        VALUES (NULL, 'Kullanıcı Girişi', 'Başarısız giriş denemesi: ' + @TcKimlikNo, GETDATE(), 1);
    END

    RETURN @Basarili;

/*
go
declare @Basarilix bit = 0
exec [SP_KullaniciGiris] @TcKimlikNo = '65968234430', @Sifre = '1111', @Basarili = @Basarilix output
select @Basarilix
go
*/
END