"""
Soru Analiz Modülü - ChatGPT ile soru türü ve parametreleri çıkarır
"""
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)


class QuestionAnalyzer:
    """ChatGPT kullanarak soruları analiz eder ve parametreleri çıkarır"""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
        self.model = Config.OPENAI_MODEL

        # Soru türleri ve açıklamaları
        self.soru_turleri = {
            'IZIN_HAKKI_SORGULA': 'SADECE kullanıcının KALAN yıllık izin hakkını sorgular (kaç gün izni kaldı). KULLANILAN izin geçmişi DEĞİL!',
            'STOK_BILGISI_SORGULA': 'Stok kodu için bakiye sorgular (stok_kod gerekli, depo_kod opsiyonel - belirtilmezse tüm depolar listelenir)',
            'MAAS_BORDRO_SORGULA': 'Maaş ve bordro bilgilerini sorgular (ay ve yıl opsiyonel)',
            'ZIMMET_SORGULA': 'Zimmet bilgilerini sorgular (ekipman_tipi opsiyonel)',
            'EGITIM_TALEP': 'Eğitim talebi oluşturur (egitim_konusu opsiyonel)',
            'MESAI_SORGULA': 'Mesai saatleri ve fazla mesai sorguları (baslangic_tarih, bitis_tarih opsiyonel)',
            'DEPARTMAN_BILGI': 'Departman iletişim bilgileri',
            'AVANS_TALEP': 'Avans talepleri',
            'IT_DESTEK': 'BT destek talepleri',
            'GENEL_BILGI': 'Genel bilgilendirme soruları',
            'BILINMIYOR': 'Tanımlanamayan sorular veya geçmiş kayıt sorguları (örn: kullanılan izinler, geçmiş talepler)'
        }

    def analyze_question(self, soru: str, tc_kimlik_no: str = None, sohbet_gecmisi: list = None) -> Dict[str, Any]:
        """
        Soruyu analiz eder, soru türünü ve parametreleri belirler

        Args:
            soru: Kullanıcının sorusu
            tc_kimlik_no: TC Kimlik No (otomatik eklenir)
            sohbet_gecmisi: Önceki sohbet geçmişi (context için)

        Returns:
            {
                'soru_tur_kod': str,
                'parametreler': dict,
                'guven_skoru': float,
                'aciklama': str
            }
        """
        if not self.client:
            logger.warning("OpenAI API key yok, basit analiz yapılıyor")
            return self._simple_analysis(soru)

        try:
            # ChatGPT'ye gönderilecek prompt
            system_prompt = self._create_system_prompt()

            # Context ekle
            context_text = ""
            if sohbet_gecmisi and len(sohbet_gecmisi) > 0:
                logger.info(f"Sohbet geçmişi var: {len(sohbet_gecmisi)} mesaj")
                logger.info(f"İlk mesaj yapısı: {list(sohbet_gecmisi[0].keys()) if sohbet_gecmisi else 'BOŞ'}")
                logger.info(f"İlk mesajın Soru değeri: '{sohbet_gecmisi[0].get('Soru', 'YOK')}' (len={len(sohbet_gecmisi[0].get('Soru', ''))})")

                context_text = "\n\nÖNCEKİ SOHBET (Context):\n"
                for i, msg in enumerate(sohbet_gecmisi[-3:]):  # Son 3 mesaj
                    soru_val = msg.get('Soru', '')
                    cevap_val = msg.get('Cevap', '')[:200]
                    logger.info(f"Context mesaj {i}: Soru='{soru_val[:50]}...', Cevap='{cevap_val[:50]}...'")
                    context_text += f"Kullanıcı: {soru_val}\n"
                    context_text += f"AI: {cevap_val}...\n\n"  # İlk 200 karakter

                logger.info(f"Context oluşturuldu: {len(context_text)} karakter")
                logger.info(f"Context içeriği:\n{context_text[:300]}...")
            else:
                logger.info("Sohbet geçmişi YOK")

            user_prompt = f"{context_text}Soru: {soru}\n\nÖNEMLİ: Eğer kullanıcı önceki mesajlarda bahsedilen bir konuya atıfta bulunuyorsa (örn: 'tüm depolardaki stoğu?'), context'i kullanarak parametreleri çıkar."

            logger.debug(f"ChatGPT'ye gönderilen prompt:\n{user_prompt[:500]}...")

            # ChatGPT'den yanıt al
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Daha deterministik sonuçlar için düşük
                response_format={"type": "json_object"}
            )

            # JSON yanıtı parse et
            result = json.loads(response.choices[0].message.content)

            # TC Kimlik No'yu otomatik ekle
            if tc_kimlik_no and 'parametreler' in result:
                result['parametreler']['tc_kimlik_no'] = tc_kimlik_no

            logger.info(f"Soru analiz edildi: {result.get('soru_tur_kod', 'BILINMIYOR')}")
            return result

        except Exception as e:
            logger.error(f"ChatGPT analiz hatası: {str(e)}")
            return self._simple_analysis(soru)

    def _create_system_prompt(self) -> str:
        """ChatGPT için sistem promptu oluşturur"""
        soru_turleri_text = "\n".join([
            f"- {kod}: {aciklama}"
            for kod, aciklama in self.soru_turleri.items()
        ])

        return f"""Sen bir firma chatbot asistanısın. Kullanıcının sorusunu analiz edip soru türünü ve parametreleri çıkarmalısın.

**ÖNEMLİ: Kullanıcı önceki mesajlarda bahsedilen konulara atıfta bulunabilir. Context kısmında verilen önceki sohbeti dikkatlice oku. Eğer kullanıcı "tüm depolardaki", "o ürünün", "aynı stokun" gibi ifadeler kullanıyorsa, context'te bahsedilen stok kodunu veya parametreleri kullan!**

MEVCUT SORU TÜRLERİ:
{soru_turleri_text}

GÖREVİN:
1. Önce context'i oku (varsa) - Önceki mesajlardaki stok kodlarını, ürün adlarını vb. not al
2. Yeni soruyu analiz et - Context'teki bilgileri kullan
3. En uygun soru türünü belirle
4. Soruda geçen parametreleri çıkar - Açık belirtilmese bile context'ten al
5. Yanıtını JSON formatında döndür

JSON FORMATI:
{{
    "soru_tur_kod": "SORU_TUR_KODU",
    "parametreler": {{
        "parametre1": "değer1",
        "parametre2": "değer2"
    }},
    "guven_skoru": 0.95,
    "aciklama": "Kısa açıklama"
}}

PARAMETRE ÖRNEKLERI:
- Stok sorgulama: stok_kod, depo_kod
- Bordro: ay (1-12), yil (2024)
- Mesai: baslangic_tarih, bitis_tarih (YYYY-MM-DD formatında)
- Zimmet: ekipman_tipi

ÖRNEKLER:

Soru: "6-01PM-5245-AA kodlu ürünün SATINALMA deposunda kaç adet var?"
{{
    "soru_tur_kod": "STOK_BILGISI_SORGULA",
    "parametreler": {{
        "stok_kod": "6-01PM-5245-AA",
        "depo_kod": "SATINALMA"
    }},
    "guven_skoru": 0.98,
    "aciklama": "Belirli depoda stok sorgulama"
}}

Soru: "6-01YM-0025-AA stok kodunun stoğu?"
{{
    "soru_tur_kod": "STOK_BILGISI_SORGULA",
    "parametreler": {{
        "stok_kod": "6-01YM-0025-AA"
    }},
    "guven_skoru": 0.95,
    "aciklama": "Tüm depolarda stok sorgulama (depo belirtilmemiş)"
}}

Soru: "Kalan izin hakkım kaç gün?"
{{
    "soru_tur_kod": "IZIN_HAKKI_SORGULA",
    "parametreler": {{}},
    "guven_skoru": 1.0,
    "aciklama": "Yıllık izin hakkı sorgulama (KALAN gün)"
}}

Soru: "Son 1 ayda kullandığım izinler"
{{
    "soru_tur_kod": "BILINMIYOR",
    "parametreler": {{}},
    "guven_skoru": 0.95,
    "aciklama": "İzin geçmişi sorgusu - veritabanı gerekli"
}}

Soru: "Geçen ay hangi tarihlerde izin kullandım?"
{{
    "soru_tur_kod": "BILINMIYOR",
    "parametreler": {{}},
    "guven_skoru": 0.95,
    "aciklama": "İzin geçmişi sorgusu - Text-to-SQL gerekli"
}}

Soru: "Eylül ayı bordrom ne kadar?"
{{
    "soru_tur_kod": "MAAS_BORDRO_SORGULA",
    "parametreler": {{
        "ay": "9",
        "yil": "2025"
    }},
    "guven_skoru": 0.95,
    "aciklama": "Bordro sorgulama"
}}

CONTEXT KULLANIMI ÖRNEĞİ:
Önceki Sohbet:
Kullanıcı: "6-01PM-5063-AA stok kodunun satınalma depo stoğu"
AI: "6-01PM-5063-AA stok kodunun SATINALMA deposunda 150 adet bulunmaktadır..."

Yeni Soru: "tüm depolardaki stoğu?"
{{
    "soru_tur_kod": "STOK_BILGISI_SORGULA",
    "parametreler": {{
        "stok_kod": "6-01PM-5063-AA"
    }},
    "guven_skoru": 0.90,
    "aciklama": "Context'ten stok kodu alındı, tüm depolar sorgulanacak"
}}

ÖNEMLİ KURALLAR:
- Stok kodlarını tam olarak çıkar (örn: "6-01PM-5245-AA")
- Tarihleri YYYY-MM-DD formatına çevir
- Ay isimlerini sayıya çevir (Ocak=1, Şubat=2, ...)
- **KRİTİK:** "Kalan izin hakkım?" → IZIN_HAKKI_SORGULA, ama "Kullandığım izinler?" → BILINMIYOR
- **KRİTİK:** "Son X ayda/günde kullandığım/aldığım izinler" → BILINMIYOR (geçmiş kayıt sorgusu)
- IZIN_HAKKI_SORGULA SADECE "kaç gün kaldı" soruları içindir
- Eğer emin değilsen guven_skoru'nu düşük tut
- Yanıtın sadece JSON olsun, başka açıklama ekleme
"""

    def _simple_analysis(self, soru: str) -> Dict[str, Any]:
        """
        OpenAI olmadan basit kelime eşleştirme ile analiz yapar
        """
        soru_lower = soru.lower()

        # Basit keyword matching
        if 'izin' in soru_lower or 'yıllık' in soru_lower:
            return {
                'soru_tur_kod': 'IZIN_HAKKI_SORGULA',
                'parametreler': {},
                'guven_skoru': 0.7,
                'aciklama': 'Basit analiz ile tespit edildi'
            }
        elif 'stok' in soru_lower or 'ürün' in soru_lower or 'depo' in soru_lower:
            # Basit regex ile stok kodu bulmaya çalış
            import re
            stok_pattern = r'[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+'
            stok_match = re.search(stok_pattern, soru, re.IGNORECASE)

            parametreler = {}
            if stok_match:
                parametreler['stok_kod'] = stok_match.group(0)

            # Depo kodunu bul
            depo_keywords = ['SATINALMA', 'IMALAT', 'MONTAJ', 'SEVKIYAT']
            for depo in depo_keywords:
                if depo.lower() in soru_lower:
                    parametreler['depo_kod'] = depo
                    break

            return {
                'soru_tur_kod': 'STOK_BILGISI_SORGULA',
                'parametreler': parametreler,
                'guven_skoru': 0.6,
                'aciklama': 'Basit analiz ile tespit edildi'
            }
        elif 'maaş' in soru_lower or 'bordro' in soru_lower:
            return {
                'soru_tur_kod': 'MAAS_BORDRO_SORGULA',
                'parametreler': {},
                'guven_skoru': 0.7,
                'aciklama': 'Basit analiz ile tespit edildi'
            }
        elif 'zimmet' in soru_lower or 'ekipman' in soru_lower:
            return {
                'soru_tur_kod': 'ZIMMET_SORGULA',
                'parametreler': {},
                'guven_skoru': 0.7,
                'aciklama': 'Basit analiz ile tespit edildi'
            }
        elif 'eğitim' in soru_lower or 'kurs' in soru_lower:
            return {
                'soru_tur_kod': 'EGITIM_TALEP',
                'parametreler': {},
                'guven_skoru': 0.7,
                'aciklama': 'Basit analiz ile tespit edildi'
            }
        else:
            return {
                'soru_tur_kod': 'BILINMIYOR',
                'parametreler': {},
                'guven_skoru': 0.3,
                'aciklama': 'Soru türü belirlenemedi'
            }


# Test
if __name__ == "__main__":
    analyzer = QuestionAnalyzer()

    test_sorular = [
        "Kalan izin hakkım kaç gün?",
        "6-01PM-5245-AA kodlu ürünün SATINALMA deposundaki stok durumu nedir?",
        "Eylül ayı bordrom ne kadar?",
        "Laptop zimmetim var mı?",
        "Python eğitimi almak istiyorum"
    ]

    print("=" * 70)
    print("SORU ANALİZ TESTİ")
    print("=" * 70)

    for soru in test_sorular:
        print(f"\n📝 Soru: {soru}")
        result = analyzer.analyze_question(soru, tc_kimlik_no="12345678901")
        print(f"   🎯 Tür: {result['soru_tur_kod']}")
        print(f"   📊 Güven: {result['guven_skoru']}")
        print(f"   📋 Parametreler: {result['parametreler']}")
        print(f"   💡 Açıklama: {result['aciklama']}")
