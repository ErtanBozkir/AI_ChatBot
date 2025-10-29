

INSERT INTO dbo.SoruTurleri (Kod, Aciklama, AktifMi, OlusturmaTarihi)
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

