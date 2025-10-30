"""
Text-to-SQL Modülü
Doğal dil sorularını güvenli SQL sorgularına dönüştürür

GÜVENLİK ÖNLEMLERİ:
- Sadece SELECT sorgularına izin verilir
- Her sorguda WHERE TcKimlikNo = ? zorunludur
- SQL injection koruması (parametreli sorgular)
- DROP, DELETE, UPDATE, INSERT, ALTER, EXEC yasaktır
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI

from config import Config
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextToSQLEngine:
    """Text-to-SQL motoru - Güvenli SQL üretimi"""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.db = DatabaseManager()
        self.model = Config.OPENAI_MODEL

        # Database schema (önemli tablolar) - ACTUAL DATABASE STRUCTURE
        self.schema_context = """
# KNS_IK VERİTABANI SCHEMA'SI (GÜNCEL)

## Ana Tablolar:

### 1. Calisan (Çalışan Bilgileri)
- Id (int): Çalışan ID
- TcKimlikNo (varchar): TC Kimlik No
- Adi (nvarchar): İsim
- Soyadi (nvarchar): Soyisim
- DepartmanId (int): Departman ID
- GorevId (int): Görev/Pozisyon ID
- IseGirisTarihi (date): İşe giriş tarihi
- IstenAyrilmaTarihi (date): İşten çıkış tarihi
- AktifMi (bit): Aktif mi?
- IsEposta (nvarchar): İş e-postası
- TelefonNo (nvarchar): Telefon numarası
- DogumTarihi (date): Doğum tarihi
- Cinsiyet (nvarchar): Cinsiyet
- MedeniDurum (nvarchar): Medeni durum
- Maas (decimal): Maaş
- MaasParaBirimiId (int): Maaş para birimi ID

### 2. IzinTalep (İzin Talepleri) - ÖNEMLİ: ToplamGunSayisi KOLONU YOK!
- Id (int): Talep ID
- CalisanId (int): Çalışan ID
- IzinTipiId (int): İzin tipi ID
- BaslangicTarihi (date): Başlangıç tarihi
- BitisTarihi (date): Bitiş tarihi
- BaslangicSaati (time): Başlangıç saati
- BitisSaati (time): Bitiş saati
- TalepTarihi (datetime): Talep tarihi
- OnayTarihi (datetime): Onay tarihi
- OnayDurumu (nvarchar): **ÖNEMLİ: TAMAMEN BÜYÜK HARF KULLAN!** 'ONAYLANDI', 'REDDEDILDI', 'IPTAL_EDILDI', 'ONAY_BEKLIYOR'
- Aciklama (nvarchar): Açıklama
- SureTuru (nvarchar): Süre türü (TamGun, YarimGun, Saatlik)
- Adres (nvarchar): İzin adresi

NOT: İzin gün sayısını hesaplamak için DATEDIFF(DAY, BaslangicTarihi, BitisTarihi) + 1 kullan
**ÇOK ÖNEMLİ:** OnayDurumu kontrolünde MUTLAKA BÜYÜK HARF kullan: WHERE OnayDurumu = 'ONAYLANDI' (DOĞRU), 'Onaylandi' DEĞİL!

### 3. IzinTipi (İzin Türleri)
- Id (int): İzin tipi ID
- Kodu (nvarchar): İzin tipi kodu
- Adi (nvarchar): İzin tipi adı (Yıllık İzin, Mazeret İzni, Hastalık İzni, vb.)
- Turu (nvarchar): İzin türü
- BaslangicTarihi (date): Başlangıç tarihi
- BitisTarihi (date): Bitiş tarihi

### 4. AvansTalep (Avans Talepleri)
- Id (int): Avans ID
- CalisanId (int): Çalışan ID
- Tutar (decimal): Avans tutarı
- ParaBirimiId (int): Para birimi ID
- Tarih (date): Avans tarihi
- TalepTarihi (datetime): Talep tarihi
- Sebep (nvarchar): Sebep
- Aciklama (nvarchar): Açıklama
- OnayTarihi (datetime): Onay tarihi
- OnayDurumu (nvarchar): **TAMAMEN BÜYÜK HARF!** 'ONAYLANDI', 'REDDEDILDI', 'IPTAL_EDILDI', 'ONAY_BEKLIYOR'
- Mesaj (nvarchar): Mesaj

### 5. HarcamaTalep (Harcama Talepleri)
- Id (int): Harcama ID
- CalisanId (int): Çalışan ID
- Adi (nvarchar): Harcama adı
- TalepTarihi (datetime): Talep tarihi
- OnayTarihi (datetime): Onay tarihi
- OnayDurumu (nvarchar): **TAMAMEN BÜYÜK HARF!** 'ONAYLANDI', 'REDDEDILDI', 'IPTAL_EDILDI', 'ONAY_BEKLIYOR'
- Aciklama (nvarchar): Açıklama
- Mesaj (nvarchar): Mesaj

NOT: HarcamaTalep toplam tutar içermez, detaylar başka tabloda olabilir

### 6. Gorev (Görevler/Pozisyonlar)
- Id (int): Görev ID
- Adi (nvarchar): Görev adı
- UnvanAdi (nvarchar): Ünvan adı
- UnvanId (int): Ünvan ID

### 7. Departman (Departmanlar)
- Id (int): Departman ID
- Kodu (nvarchar): Departman kodu
- Adi (nvarchar): Departman adı
- UstDepartmanId (int): Üst departman ID

## ÖNEMLİ NOTLAR:
- IzinBakiye tablosu YOK! İzin bakiyesi için başka bir yöntem kullanılmalı
- Zimmet tablosu YOK! Zimmet sorguları yapılamaz
- İzin gün sayısı hesaplamak için: DATEDIFF(DAY, BaslangicTarihi, BitisTarihi) + 1
- **KRİTİK:** OnayDurumu değerleri TAMAMEN BÜYÜK HARF: 'ONAYLANDI', 'REDDEDILDI', 'IPTAL_EDILDI', 'ONAY_BEKLIYOR'

## JOIN İpuçları:
- Calisan.Id = IzinTalep.CalisanId
- Calisan.Id = AvansTalep.CalisanId
- Calisan.Id = HarcamaTalep.CalisanId
- Calisan.GorevId = Gorev.Id
- Calisan.DepartmanId = Departman.Id
- IzinTalep.IzinTipiId = IzinTipi.Id

## Örnek Sorgular:
- "Hangi departmandayım?" → SELECT d.Adi FROM KNS_IK.dbo.Departman d INNER JOIN KNS_IK.dbo.Calisan c ON c.DepartmanId = d.Id WHERE c.TcKimlikNo = ?
- "Son 2 ayda kullandığım izinler" → SELECT it.Adi, i.BaslangicTarihi, i.BitisTarihi, DATEDIFF(DAY, i.BaslangicTarihi, i.BitisTarihi) + 1 AS GunSayisi FROM KNS_IK.dbo.IzinTalep i INNER JOIN KNS_IK.dbo.IzinTipi it ON i.IzinTipiId = it.Id WHERE i.CalisanId = (SELECT Id FROM KNS_IK.dbo.Calisan WHERE TcKimlikNo = ?) AND i.BaslangicTarihi >= DATEADD(MONTH, -2, GETDATE()) AND i.OnayDurumu = 'ONAYLANDI'
- "Kaç yıldır çalışıyorum?" → SELECT DATEDIFF(YEAR, IseGirisTarihi, GETDATE()) AS CalismaYili FROM KNS_IK.dbo.Calisan WHERE TcKimlikNo = ?
- "Son avans talebim ne zaman?" → SELECT TOP 1 Tarih, Tutar, OnayDurumu FROM KNS_IK.dbo.AvansTalep WHERE CalisanId = (SELECT Id FROM KNS_IK.dbo.Calisan WHERE TcKimlikNo = ?) ORDER BY TalepTarihi DESC
- "Onay bekleyen izinlerim" → SELECT COUNT(*) FROM KNS_IK.dbo.IzinTalep WHERE CalisanId = (SELECT Id FROM KNS_IK.dbo.Calisan WHERE TcKimlikNo = ?) AND OnayDurumu = 'ONAY_BEKLIYOR'
- "Reddedilen taleplerim" → SELECT * FROM KNS_IK.dbo.IzinTalep WHERE CalisanId = (SELECT Id FROM KNS_IK.dbo.Calisan WHERE TcKimlikNo = ?) AND OnayDurumu = 'REDDEDILDI'
"""

    def is_safe_query(self, sql: str) -> tuple[bool, str]:
        """
        SQL sorgusunun güvenli olup olmadığını kontrol eder

        Returns:
            (güvenli_mi, hata_mesajı)
        """
        sql_upper = sql.upper()

        # Tehlikeli komutları kontrol et
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE',
            'EXEC', 'EXECUTE', 'SP_', 'XP_', 'CREATE', 'GRANT', 'REVOKE'
        ]

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False, f"Tehlikeli komut tespit edildi: {keyword}"

        # SELECT kontrolü
        if 'SELECT' not in sql_upper:
            return False, "Sadece SELECT sorgularına izin verilir"

        # TcKimlikNo kontrolü (parametreli ? olmalı)
        if 'TCKIMLIKNO' not in sql_upper:
            return False, "Sorgu TcKimlikNo filtrelemesi içermelidir"

        # Birden fazla statement kontrolü (;)
        if ';' in sql and sql.strip()[-1] != ';':
            return False, "Birden fazla SQL statement'a izin verilmez"

        return True, ""

    def generate_sql(self, question: str, tc_kimlik_no: str) -> Dict[str, Any]:
        """
        Doğal dil sorusundan SQL üretir

        Args:
            question: Kullanıcının sorusu
            tc_kimlik_no: Kullanıcının TC Kimlik No

        Returns:
            {
                'success': bool,
                'sql': str,
                'error': str (varsa)
            }
        """
        try:
            # ChatGPT ile SQL üret
            system_prompt = f"""Sen bir SQL expert'isin. KNS Otomotiv şirketinin İK veritabanından veri çeken güvenli SQL sorguları oluşturuyorsun.

{self.schema_context}

## ÖNEMLİ GÜVENLİK KURALLARI:
1. **SADECE SELECT** sorgularına izin var
2. Her sorguda **TcKimlikNo parametresi kullan** (? ile)
3. Kullanıcı **sadece kendi verilerine** erişebilir
4. CalisanId'yi TcKimlikNo'dan bul: (SELECT Id FROM KNS_IK.dbo.Calisan WHERE TcKimlikNo = ?)
5. **Tüm tablo isimleri** KNS_IK.dbo. prefix'i ile başlamalı
6. Parametreli sorgu kullan (WHERE TcKimlikNo = ? şeklinde)
7. **KRİTİK:** OnayDurumu değerleri MUTLAKA BÜYÜK HARF: WHERE OnayDurumu = 'ONAYLANDI' (✓ DOĞRU), WHERE OnayDurumu = 'Onaylandi' (✗ YANLIŞ)

## ÇIKTI FORMATI:
Sadece SQL sorgusunu döndür. Açıklama yapma, markdown kullanma.
"""

            user_prompt = f"""Kullanıcı TC: {tc_kimlik_no}

Soru: {question}

Güvenli bir SELECT sorgusu oluştur. TcKimlikNo parametresi için ? kullan."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Düşük temperature (tutarlılık için)
                max_tokens=500
            )

            sql = response.choices[0].message.content.strip()

            # Markdown temizle
            sql = sql.replace('```sql', '').replace('```', '').strip()

            # Güvenlik kontrolü
            is_safe, error_msg = self.is_safe_query(sql)
            if not is_safe:
                logger.error(f"Güvensiz SQL üretildi: {error_msg}")
                return {
                    'success': False,
                    'error': f"Güvenlik hatası: {error_msg}",
                    'sql': sql
                }

            logger.info(f"SQL üretildi: {sql}")
            return {
                'success': True,
                'sql': sql
            }

        except Exception as e:
            logger.error(f"SQL üretme hatası: {str(e)}")
            return {
                'success': False,
                'error': f"SQL üretme hatası: {str(e)}"
            }

    def execute_sql_and_format_answer(
        self,
        question: str,
        tc_kimlik_no: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Soruyu SQL'e çevir, çalıştır ve sonucu doğal dille formatla
        Tüm işlemleri TEXT_TO_SQL_LOGS tablosuna kaydeder

        Args:
            question: Kullanıcının sorusu
            tc_kimlik_no: TC Kimlik No
            session_id: Session ID

        Returns:
            {
                'success': bool,
                'cevap': str,
                'sql': str,
                'data': list,
                'error': str (varsa)
            }
        """
        import time
        start_time = time.time()

        log_data = {
            'tc_kimlik_no': tc_kimlik_no,
            'session_id': session_id,
            'soru': question,
            'sql': None,
            'durum': None,
            'hata': None,
            'sonuc_sayisi': 0,
            'guvenlik': None,
            'sure': 0
        }

        try:
            # 1. SQL üret
            sql_result = self.generate_sql(question, tc_kimlik_no)

            if not sql_result['success']:
                log_data['durum'] = 'URETIM_HATASI'
                log_data['hata'] = sql_result.get('error', 'SQL üretimi başarısız')
                log_data['sql'] = sql_result.get('sql', '')
                log_data['sure'] = int((time.time() - start_time) * 1000)
                self._save_log(log_data)

                return {
                    'success': False,
                    'error': sql_result['error'],
                    'cevap': "Üzgünüm, bu soruyu güvenli bir şekilde cevaplayamıyorum."
                }

            sql = sql_result['sql']
            log_data['sql'] = sql

            # 2. SQL'i çalıştır (tc_kimlik_no parametresi ile)
            try:
                results = self.db.execute_query(sql, (tc_kimlik_no,))
                log_data['sonuc_sayisi'] = len(results) if results else 0
            except Exception as e:
                logger.error(f"SQL çalıştırma hatası: {str(e)}")
                log_data['durum'] = 'SQL_HATASI'
                log_data['hata'] = str(e)
                log_data['sure'] = int((time.time() - start_time) * 1000)
                self._save_log(log_data)

                return {
                    'success': False,
                    'error': f"SQL çalıştırma hatası: {str(e)}",
                    'sql': sql,
                    'cevap': "Veritabanı sorgusunda bir hata oluştu."
                }

            # 3. Sonucu doğal dille formatla
            if not results:
                log_data['durum'] = 'BASARILI'
                log_data['guvenlik'] = 'OK - Güvenli sorgu'
                log_data['sure'] = int((time.time() - start_time) * 1000)
                self._save_log(log_data)

                return {
                    'success': True,
                    'cevap': "Bu soru için herhangi bir kayıt bulunamadı.",
                    'sql': sql,
                    'data': []
                }

            # ChatGPT ile sonucu formatla
            formatted_answer = self.format_results_with_gpt(question, results)

            log_data['durum'] = 'BASARILI'
            log_data['guvenlik'] = 'OK - Güvenli sorgu'
            log_data['sure'] = int((time.time() - start_time) * 1000)
            self._save_log(log_data)

            return {
                'success': True,
                'cevap': formatted_answer,
                'sql': sql,
                'data': results
            }

        except Exception as e:
            logger.error(f"Text-to-SQL hatası: {str(e)}")
            log_data['durum'] = 'GENEL_HATA'
            log_data['hata'] = str(e)
            log_data['sure'] = int((time.time() - start_time) * 1000)
            self._save_log(log_data)

            return {
                'success': False,
                'error': str(e),
                'cevap': "Bir hata oluştu."
            }

    def _save_log(self, log_data: Dict[str, Any]):
        """
        Text-to-SQL işlemini veritabanına kaydeder (TESTDB'ye)

        Args:
            log_data: Log bilgileri
        """
        try:
            query = """
                INSERT INTO TESTDB.dbo.TEXT_TO_SQL_LOGS
                (TcKimlikNo, SessionId, Soru, UretilenSQL, SQLParametreleri,
                 BasariDurumu, HataMesaji, SonucSayisi, GuvenlikKontrol, CalismaZamani)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute_non_query(
                query,
                (
                    log_data.get('tc_kimlik_no'),
                    log_data.get('session_id'),
                    log_data.get('soru'),
                    log_data.get('sql'),
                    f"TcKimlikNo = {log_data.get('tc_kimlik_no')}",
                    log_data.get('durum'),
                    log_data.get('hata'),
                    log_data.get('sonuc_sayisi'),
                    log_data.get('guvenlik'),
                    log_data.get('sure')
                )
            )
            logger.info(f"Text-to-SQL log kaydedildi (TESTDB): {log_data.get('durum')}")
        except Exception as e:
            logger.error(f"Log kaydetme hatası: {str(e)}")

    def format_results_with_gpt(self, question: str, results: List[Dict]) -> str:
        """
        SQL sonuçlarını doğal dilde formatlar

        Args:
            question: Orijinal soru
            results: SQL sorgu sonuçları

        Returns:
            Doğal dilde formatlanmış cevap
        """
        try:
            # Sonuçları JSON formatında hazırla
            results_json = json.dumps(results, ensure_ascii=False, default=str)

            system_prompt = """Sen KNS Otomotiv'in AI asistanısın. SQL sorgu sonuçlarını kullanıcı dostu bir dille açıklıyorsun.

Kurallar:
- Kısa ve öz cevaplar ver
- Sayıları ve tarihleri net belirt
- Türkçe kullan
- Profesyonel ama samimi bir dil kullan"""

            user_prompt = f"""Soru: {question}

Veritabanı sonuçları:
{results_json}

Bu sonuçları kullanarak soruya doğal bir dille cevap ver."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Sonuç formatlama hatası: {str(e)}")
            # Hata durumunda basit formatla
            if len(results) == 1 and len(results[0]) == 1:
                return str(list(results[0].values())[0])
            return json.dumps(results, ensure_ascii=False, indent=2)


# Test fonksiyonu
if __name__ == "__main__":
    print("=" * 80)
    print("TEXT-TO-SQL TEST")
    print("=" * 80)

    if not Config.OPENAI_API_KEY:
        print("\n✗ OPENAI_API_KEY bulunamadı!")
        exit(1)

    engine = TextToSQLEngine()

    # Test soruları
    test_questions = [
        "Kalan izin günüm kaç?",
        "Üzerimdeki zimmetler neler?",
        "Hangi departmandayım?",
        "Son izin talebim ne zaman?",
        "Kaç yıldır çalışıyorum?"
    ]

    test_tc = "12345678901"  # Test TC

    for q in test_questions:
        print(f"\n{'='*80}")
        print(f"Soru: {q}")
        print(f"{'='*80}")

        result = engine.execute_sql_and_format_answer(q, test_tc)

        if result['success']:
            print(f"\n✓ SQL: {result.get('sql', 'N/A')}")
            print(f"\nCevap: {result['cevap']}")
        else:
            print(f"\n✗ Hata: {result.get('error', 'Unknown')}")

    print("\n✓ Text-to-SQL modülü hazır!")
