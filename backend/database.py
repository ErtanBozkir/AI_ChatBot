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
        self.connection_string = Config().get_connection_string
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

    def call_sp_soru_cevap(self, tc_kimlik_no: str, soru: str) -> Dict[str, Any]:
        """
        SP_SoruCevap stored procedure'ünü çağırır

        Args:
            tc_kimlik_no: TC Kimlik No
            soru: Kullanıcının sorusu

        Returns:
            Cevap bilgileri içeren dictionary
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    DECLARE @Cevap NVARCHAR(MAX)
                    DECLARE @SoruTurKod NVARCHAR(50)

                    EXEC SP_SoruCevap ?, ?, @Cevap OUTPUT, @SoruTurKod OUTPUT

                    SELECT @Cevap AS Cevap, @SoruTurKod AS SoruTurKod
                """, (tc_kimlik_no, soru))

                result = cursor.fetchone()

                return {
                    'cevap': result.Cevap if result else None,
                    'soru_tur_kod': result.SoruTurKod if result else None,
                    'tc_kimlik_no': tc_kimlik_no,
                    'soru': soru
                }

        except Exception as e:
            logger.error(f"SP_SoruCevap hatası: {str(e)}")
            raise

    def call_sp_soru_cevap_v2(self, tc_kimlik_no: str, soru: str,
                               soru_tur_kod: str, parametreler_json: str) -> Dict[str, Any]:
        """
        SP_SoruCevap_V2 stored procedure'ünü çağırır (JSON parametrelerle)

        Args:
            tc_kimlik_no: TC Kimlik No
            soru: Kullanıcının sorusu
            soru_tur_kod: Soru türü kodu (ChatGPT'den)
            parametreler_json: Parametreler JSON formatında

        Returns:
            Cevap bilgileri içeren dictionary
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    DECLARE @Cevap NVARCHAR(MAX)

                    EXEC SP_SoruCevap_V2 ?, ?, ?, ?, @Cevap OUTPUT

                    SELECT @Cevap AS Cevap
                """, (tc_kimlik_no, soru, soru_tur_kod, parametreler_json))

                result = cursor.fetchone()

                return {
                    'cevap': result.Cevap if result else None,
                    'soru_tur_kod': soru_tur_kod,
                    'tc_kimlik_no': tc_kimlik_no,
                    'soru': soru,
                    'parametreler': parametreler_json
                }

        except Exception as e:
            logger.error(f"SP_SoruCevap_V2 hatası: {str(e)}")
            raise

    def call_sp_kullanici_giris(self, tc_kimlik_no: str, sifre: str) -> bool:
        """
        SP_KullaniciGiris stored procedure'ünü çağırır

        Args:
            tc_kimlik_no: TC Kimlik No
            sifre: Şifre (plain text)

        Returns:
            Başarılı ise True
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    DECLARE @Basarili BIT

                    EXEC SP_KullaniciGiris ?, ?, @Basarili OUTPUT

                    SELECT @Basarili AS Basarili
                """, (tc_kimlik_no, sifre))

                result = cursor.fetchone()

                if result:
                    return bool(result.Basarili)
                else:
                    return False

        except Exception as e:
            logger.error(f"SP_KullaniciGiris hatası: {str(e)}")
            return False

    def get_sohbet_gecmisi(self, tc_kimlik_no: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Kullanıcının sohbet geçmişini getirir

        Args:
            tc_kimlik_no: TC Kimlik No
            limit: Maksimum kayıt sayısı

        Returns:
            Sohbet geçmişi listesi
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("EXEC SP_SohbetGecmisiGetir ?, ?", (tc_kimlik_no, limit))

                columns = [column[0] for column in cursor.description]
                results = []

                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                return results

        except Exception as e:
            logger.error(f"Sohbet geçmişi getirme hatası: {str(e)}")
            raise

    def get_sohbet_gecmisi_by_session(self, tc_kimlik_no: str, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Kullanıcının belirli bir session'a ait sohbet geçmişini getirir

        Args:
            tc_kimlik_no: TC Kimlik No
            session_id: Session ID
            limit: Maksimum kayıt sayısı

        Returns:
            Session'a ait sohbet geçmişi listesi
        """
        try:
            query = """
                SELECT TOP (?)
                    Id, Soru, Cevap, Tarih, SoruTurId, SessionId
                FROM SOHBETLER
                WHERE TcKimlikNo = ? AND SessionId = ?
                ORDER BY Tarih DESC
            """
            return self.execute_query(query, (limit, tc_kimlik_no, session_id))

        except Exception as e:
            logger.error(f"Session sohbet geçmişi getirme hatası: {str(e)}")
            raise

    def get_sessions_list(self, tc_kimlik_no: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Kullanıcının sohbet session'larını listeler

        Args:
            tc_kimlik_no: TC Kimlik No
            limit: Maksimum session sayısı

        Returns:
            Session listesi (ilk mesaj, tarih, mesaj sayısı ile)
        """
        try:
            query = """
                SELECT TOP (?)
                    SessionId,
                    MIN(Tarih) AS IlkMesajTarihi,
                    MAX(Tarih) AS SonMesajTarihi,
                    COUNT(*) AS MesajSayisi,
                    (SELECT TOP 1 Soru FROM SOHBETLER WHERE TcKimlikNo = s.TcKimlikNo AND SessionId = s.SessionId ORDER BY Tarih ASC) AS IlkSoru
                FROM SOHBETLER s
                WHERE TcKimlikNo = ? AND SessionId IS NOT NULL
                GROUP BY SessionId, TcKimlikNo
                ORDER BY MAX(Tarih) DESC
            """
            return self.execute_query(query, (limit, tc_kimlik_no))

        except Exception as e:
            logger.error(f"Session listesi getirme hatası: {str(e)}")
            raise

    def get_calisan_by_tc(self, tc_kimlik_no: str) -> Optional[Dict[str, Any]]:
        """
        Çalışan bilgilerini TC Kimlik No ile getirir (KNS_IK.dbo.Calisan)
        ADMIN_KULLANICILAR tablosundan admin kontrolü yapar

        Args:
            tc_kimlik_no: TC Kimlik No

        Returns:
            Çalışan bilgileri (AdminMi alanı dahil)
        """
        query = """
            SELECT
                c.Id,
                c.TcKimlikNo,
                c.Adi + ' ' + c.Soyadi AS AdSoyad,
                COALESCE(c.IsEposta, c.Eposta) AS Eposta,
                c.DepartmanId AS Departman,
                c.AktifMi,
                CASE
                    WHEN a.TcKimlikNo IS NOT NULL AND a.AktifMi = 1 THEN 1
                    ELSE 0
                END AS AdminMi
            FROM KNS_IK.dbo.Calisan c
            LEFT JOIN ADMIN_KULLANICILAR a ON c.TcKimlikNo = a.TcKimlikNo
            WHERE c.TcKimlikNo = ? AND c.AktifMi = 1
        """
        results = self.execute_query(query, (tc_kimlik_no,))
        return results[0] if results else None

    def add_islem_log(self, tc_kimlik_no: Optional[str], islem: str,
                      detay: Optional[str] = None, hata_mi: bool = False) -> bool:
        """
        İşlem logu ekler

        Args:
            tc_kimlik_no: TC Kimlik No (opsiyonel)
            islem: İşlem açıklaması
            detay: Detay bilgisi (opsiyonel)
            hata_mi: Hata durumu

        Returns:
            Başarılı ise True
        """
        try:
            query = """
                INSERT INTO ISLEM_LOG (TcKimlikNo, Islem, Detay, Tarih, HataMi)
                VALUES (?, ?, ?, GETDATE(), ?)
            """
            self.execute_non_query(query, (tc_kimlik_no, islem, detay, hata_mi))
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

    # ============================================
    # DASHBOARD İSTATİSTİKLERİ
    # ============================================

    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Genel kullanım istatistiklerini getirir

        Returns:
            Kullanım istatistikleri
        """
        try:
            query = """
                SELECT
                    COUNT(DISTINCT TcKimlikNo) AS ToplamKullanici,
                    COUNT(DISTINCT SessionId) AS ToplamSession,
                    COUNT(*) AS ToplamMesaj,
                    COUNT(DISTINCT CAST(Tarih AS DATE)) AS AktifGunSayisi
                FROM SOHBETLER
                WHERE Tarih >= DATEADD(MONTH, -1, GETDATE())
            """
            result = self.execute_query(query)
            return result[0] if result else {}

        except Exception as e:
            logger.error(f"Kullanım istatistikleri hatası: {str(e)}")
            return {}

    def get_top_questions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        En çok sorulan soruları getirir

        Args:
            limit: Maksimum kayıt sayısı

        Returns:
            En çok sorulan sorular listesi
        """
        try:
            query = """
                SELECT TOP (?)
                    Soru,
                    COUNT(*) AS SoruSayisi,
                    MAX(Tarih) AS SonSoruTarihi
                FROM SOHBETLER
                WHERE Tarih >= DATEADD(MONTH, -1, GETDATE())
                GROUP BY Soru
                ORDER BY COUNT(*) DESC
            """
            return self.execute_query(query, (limit,))

        except Exception as e:
            logger.error(f"En çok sorulan sorular hatası: {str(e)}")
            return []

    def get_questions_per_user(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Kullanıcı başına soru sayısını getirir

        Args:
            limit: Maksimum kullanıcı sayısı

        Returns:
            Kullanıcı başına soru sayısı listesi
        """
        try:
            query = """
                SELECT TOP (?)
                    s.TcKimlikNo,
                    c.Adi + ' ' + c.Soyadi AS AdSoyad,
                    COUNT(*) AS SoruSayisi,
                    MAX(s.Tarih) AS SonSoruTarihi
                FROM SOHBETLER s
                LEFT JOIN KNS_IK.dbo.Calisan c ON s.TcKimlikNo = c.TcKimlikNo
                WHERE s.Tarih >= DATEADD(MONTH, -1, GETDATE())
                GROUP BY s.TcKimlikNo, c.Adi, c.Soyadi
                ORDER BY COUNT(*) DESC
            """
            return self.execute_query(query, (limit,))

        except Exception as e:
            logger.error(f"Kullanıcı başına soru sayısı hatası: {str(e)}")
            return []

    def get_success_rate(self) -> Dict[str, Any]:
        """
        Başarı oranını getirir (feedback tablosundan)

        Returns:
            Başarı oranı istatistikleri
        """
        try:
            query = """
                SELECT
                    COUNT(*) AS ToplamFeedback,
                    SUM(CASE WHEN Reaksiyon = 'positive' THEN 1 ELSE 0 END) AS OlumluFeedback,
                    SUM(CASE WHEN Reaksiyon = 'negative' THEN 1 ELSE 0 END) AS OlumsuzFeedback,
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            CAST(SUM(CASE WHEN Reaksiyon = 'positive' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100
                        ELSE 0
                    END AS BasariOrani
                FROM KULLANICI_FEEDBACK
                WHERE FeedbackTarihi >= DATEADD(MONTH, -1, GETDATE())
            """
            result = self.execute_query(query)
            return result[0] if result else {}

        except Exception as e:
            logger.error(f"Başarı oranı hatası: {str(e)}")
            return {}

    def get_peak_usage_times(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Yoğun kullanım saatlerini ve günlerini getirir

        Returns:
            Saatlik ve günlük kullanım istatistikleri
        """
        try:
            # Saatlik istatistikler
            hourly_query = """
                SELECT
                    DATEPART(HOUR, Tarih) AS Saat,
                    COUNT(*) AS MesajSayisi
                FROM SOHBETLER
                WHERE Tarih >= DATEADD(MONTH, -1, GETDATE())
                GROUP BY DATEPART(HOUR, Tarih)
                ORDER BY DATEPART(HOUR, Tarih)
            """
            hourly_stats = self.execute_query(hourly_query)

            # Günlük istatistikler (Haftalık)
            daily_query = """
                SELECT
                    CASE DATEPART(WEEKDAY, Tarih)
                        WHEN 1 THEN 'Pazar'
                        WHEN 2 THEN 'Pazartesi'
                        WHEN 3 THEN 'Salı'
                        WHEN 4 THEN 'Çarşamba'
                        WHEN 5 THEN 'Perşembe'
                        WHEN 6 THEN 'Cuma'
                        WHEN 7 THEN 'Cumartesi'
                    END AS Gun,
                    DATEPART(WEEKDAY, Tarih) AS GunNumarasi,
                    COUNT(*) AS MesajSayisi
                FROM SOHBETLER
                WHERE Tarih >= DATEADD(MONTH, -1, GETDATE())
                GROUP BY DATEPART(WEEKDAY, Tarih)
                ORDER BY DATEPART(WEEKDAY, Tarih)
            """
            daily_stats = self.execute_query(daily_query)

            return {
                'hourly': hourly_stats,
                'daily': daily_stats
            }

        except Exception as e:
            logger.error(f"Yoğun kullanım saatleri hatası: {str(e)}")
            return {'hourly': [], 'daily': []}


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
