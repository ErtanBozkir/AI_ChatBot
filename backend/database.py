"""
Veritabanı Yönetim Modülü
MSSQL bağlantısı ve stored procedure çağrılarını yönetir
"""

import pyodbc
import logging
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from contextlib import contextmanager
from config import Config

# Logging ayarları
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """MSSQL veritabanı yönetim sınıfı"""

    def __init__(self):
        self.connection_string = Config.get_connection_string
        self._connection = None

    @contextmanager
    def get_connection(self):
        """Context manager ile veritabanı bağlantısı"""
        connection = None
        try:
            connection = pyodbc.connect(self.connection_string)
            logger.info("Veritabanı bağlantısı başarılı")
            yield connection
        except pyodbc.Error as e:
            logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()
                logger.debug("Veritabanı bağlantısı kapatıldı")

    def test_connection(self) -> bool:
        """Veritabanı bağlantısını test eder"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Bağlantı testi başarısız: {str(e)}")
            return False

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        SQL sorgusu çalıştırır ve sonuçları dictionary listesi olarak döndürür

        Args:
            query: SQL sorgusu
            params: Sorgu parametreleri

        Returns:
            Sonuç listesi
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Sonuçları al
                columns = [column[0] for column in cursor.description] if cursor.description else []
                results = []

                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                logger.debug(f"Sorgu başarılı: {len(results)} satır döndü")
                return results

        except Exception as e:
            logger.error(f"Sorgu hatası: {str(e)}")
            raise

    def execute_non_query(self, query: str, params: tuple = None) -> int:
        """
        INSERT, UPDATE, DELETE sorguları çalıştırır

        Args:
            query: SQL sorgusu
            params: Sorgu parametreleri

        Returns:
            Etkilenen satır sayısı
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                row_count = cursor.rowcount

                logger.debug(f"Sorgu başarılı: {row_count} satır etkilendi")
                return row_count

        except Exception as e:
            logger.error(f"Sorgu hatası: {str(e)}")
            raise

    def call_sp_soru_cevap(self, kullanici_id: int, soru: str) -> Dict[str, Any]:
        """
        sp_SoruCevap stored procedure'ünü çağırır

        Args:
            kullanici_id: Kullanıcı ID
            soru: Kullanıcının sorusu

        Returns:
            Cevap bilgileri içeren dictionary
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # OUTPUT parametreleri
                cevap = ""
                soru_tur_kod = ""
                soru_tur_id = 0

                # Stored procedure çağrısı
                result = cursor.execute(
                    "{CALL sp_SoruCevap (?, ?, ?, ?, ?)}",
                    (kullanici_id, soru, cevap, soru_tur_kod, soru_tur_id)
                )

                # OUTPUT parametrelerini al
                cursor.nextset()  # Sonraki result set'e geç

                # Alternatif yöntem: SELECT ile OUTPUT parametrelerini al
                cursor.execute("""
                    DECLARE @Cevap NVARCHAR(MAX)
                    DECLARE @SoruTurKod NVARCHAR(50)
                    DECLARE @SoruTurId INT

                    EXEC sp_SoruCevap ?, ?, @Cevap OUTPUT, @SoruTurKod OUTPUT, @SoruTurId OUTPUT

                    SELECT @Cevap AS Cevap, @SoruTurKod AS SoruTurKod, @SoruTurId AS SoruTurId
                """, (kullanici_id, soru))

                result = cursor.fetchone()

                return {
                    'cevap': result.Cevap if result else None,
                    'soru_tur_kod': result.SoruTurKod if result else None,
                    'soru_tur_id': result.SoruTurId if result else None,
                    'kullanici_id': kullanici_id,
                    'soru': soru
                }

        except Exception as e:
            logger.error(f"sp_SoruCevap hatası: {str(e)}")
            raise

    def call_sp_kullanici_giris(self, kullanici_adi: str, sifre_hash: str) -> Tuple[Optional[int], bool]:
        """
        sp_KullaniciGiris stored procedure'ünü çağırır

        Args:
            kullanici_adi: Kullanıcı adı
            sifre_hash: Şifre hash'i

        Returns:
            (kullanici_id, basarili) tuple'ı
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    DECLARE @KullaniciId INT
                    DECLARE @Basarili BIT

                    EXEC sp_KullaniciGiris ?, ?, @KullaniciId OUTPUT, @Basarili OUTPUT

                    SELECT @KullaniciId AS KullaniciId, @Basarili AS Basarili
                """, (kullanici_adi, sifre_hash))

                result = cursor.fetchone()

                if result:
                    return (result.KullaniciId, bool(result.Basarili))
                else:
                    return (None, False)

        except Exception as e:
            logger.error(f"sp_KullaniciGiris hatası: {str(e)}")
            return (None, False)

    def get_sohbet_gecmisi(self, kullanici_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Kullanıcının sohbet geçmişini getirir

        Args:
            kullanici_id: Kullanıcı ID
            limit: Maksimum kayıt sayısı

        Returns:
            Sohbet geçmişi listesi
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("EXEC sp_SohbetGecmisiGetir ?, ?", (kullanici_id, limit))

                columns = [column[0] for column in cursor.description]
                results = []

                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                return results

        except Exception as e:
            logger.error(f"Sohbet geçmişi getirme hatası: {str(e)}")
            raise

    def get_kullanici_by_id(self, kullanici_id: int) -> Optional[Dict[str, Any]]:
        """
        Kullanıcı bilgilerini ID ile getirir

        Args:
            kullanici_id: Kullanıcı ID

        Returns:
            Kullanıcı bilgileri
        """
        query = """
            SELECT Id, KullaniciAdi, Eposta, KayitTarihi, AktifMi
            FROM KULLANICILAR
            WHERE Id = ? AND AktifMi = 1
        """
        results = self.execute_query(query, (kullanici_id,))
        return results[0] if results else None

    def get_kullanici_by_username(self, kullanici_adi: str) -> Optional[Dict[str, Any]]:
        """
        Kullanıcı bilgilerini kullanıcı adı ile getirir

        Args:
            kullanici_adi: Kullanıcı adı

        Returns:
            Kullanıcı bilgileri
        """
        query = """
            SELECT Id, KullaniciAdi, SifreHash, Eposta, KayitTarihi, AktifMi
            FROM KULLANICILAR
            WHERE KullaniciAdi = ? AND AktifMi = 1
        """
        results = self.execute_query(query, (kullanici_adi,))
        return results[0] if results else None

    def add_islem_log(self, kullanici_id: Optional[int], islem: str,
                      detay: Optional[str] = None, hata_mi: bool = False) -> bool:
        """
        İşlem logu ekler

        Args:
            kullanici_id: Kullanıcı ID (opsiyonel)
            islem: İşlem açıklaması
            detay: Detay bilgisi (opsiyonel)
            hata_mi: Hata durumu

        Returns:
            Başarılı ise True
        """
        try:
            query = """
                INSERT INTO ISLEM_LOG (KullaniciId, Islem, Detay, Tarih, HataMi)
                VALUES (?, ?, ?, GETDATE(), ?)
            """
            self.execute_non_query(query, (kullanici_id, islem, detay, hata_mi))
            return True
        except Exception as e:
            logger.error(f"Log ekleme hatası: {str(e)}")
            return False

    def get_soru_turleri(self) -> List[Dict[str, Any]]:
        """Tüm aktif soru türlerini getirir"""
        query = """
            SELECT Id, Kod, Aciklama, OlusturmaTarihi
            FROM SORU_TURLERI
            WHERE AktifMi = 1
            ORDER BY Kod
        """
        return self.execute_query(query)

    def get_soru_eslesmeleri(self, soru_tur_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Soru eşleştirmelerini getirir

        Args:
            soru_tur_id: Belirli bir soru türü ID'si (opsiyonel)

        Returns:
            Eşleştirme listesi
        """
        if soru_tur_id:
            query = """
                SELECT SE.Id, SE.SoruTurId, SE.OrnekSoru, ST.Kod AS SoruTurKodu
                FROM SORU_ESLESMELERI SE
                INNER JOIN SORU_TURLERI ST ON SE.SoruTurId = ST.Id
                WHERE SE.SoruTurId = ?
                ORDER BY SE.OrnekSoru
            """
            return self.execute_query(query, (soru_tur_id,))
        else:
            query = """
                SELECT SE.Id, SE.SoruTurId, SE.OrnekSoru, ST.Kod AS SoruTurKodu
                FROM SORU_ESLESMELERI SE
                INNER JOIN SORU_TURLERI ST ON SE.SoruTurId = ST.Id
                ORDER BY ST.Kod, SE.OrnekSoru
            """
            return self.execute_query(query)


# Test fonksiyonu
if __name__ == "__main__":
    print("=" * 50)
    print("VERITABANI BAĞLANTI TESTİ")
    print("=" * 50)

    db = DatabaseManager()

    # Bağlantı testi
    if db.test_connection():
        print("\n✓ Veritabanı bağlantısı başarılı!")

        # Soru türlerini listele
        print("\nSoru Türleri:")
        soru_turleri = db.get_soru_turleri()
        for st in soru_turleri:
            print(f"  - {st['Kod']}: {st['Aciklama']}")

    else:
        print("\n✗ Veritabanı bağlantısı başarısız!")
