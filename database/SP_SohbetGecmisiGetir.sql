ALTER PROCEDURE [dbo].[SP_SohbetGecmisiGetir]
    @TcKimlikNo nvarchar(50),
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
    LEFT JOIN dbo.SoruTurleri ST ON S.SoruTurId = ST.Id
    WHERE S.TcKimlikNo = @TcKimlikNo
    ORDER BY S.Tarih DESC;
END
