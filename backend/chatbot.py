"""
Chatbot Modülü
OpenAI ChatGPT API entegrasyonu ve yanıt üretme
"""

import logging
from typing import List, Dict, Optional, Any
from openai import OpenAI

from config import Config
from database import DatabaseManager
from document_reader import DocumentReader

# Logging ayarları
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class ChatBot:
    """Chatbot ana sınıfı"""

    def __init__(self):
        self.db = DatabaseManager()
        self.doc_reader = DocumentReader()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.temperature = Config.OPENAI_TEMPERATURE
        self.max_tokens = Config.OPENAI_MAX_TOKENS

        # Sistem mesajı
        self.system_message = """
        Sen bir firma chatbot asistanısın. Türkçe konuşuyorsun.
        Görevin, çalışanlara izin hakları, stok bilgileri, maaş bordro, zimmet ve diğer
        firma içi konularda yardımcı olmak.

        Nazik, profesyonel ve yardımsever bir dil kullan.
        Bilmediğin konularda "Bilmiyorum, ilgili departmana yönlendirebilirim" de.
        Kısa ve öz cevaplar ver.
        """

    def call_chatgpt(self, messages: List[Dict[str, str]]) -> str:
        """
        OpenAI ChatGPT API'yi çağırır

        Args:
            messages: Mesaj geçmişi

        Returns:
            ChatGPT yanıtı
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            answer = response.choices[0].message.content
            logger.info(f"ChatGPT yanıtı alındı (token: {response.usage.total_tokens})")

            return answer

        except Exception as e:
            logger.error(f"ChatGPT API hatası: {str(e)}")
            return "Üzgünüm, şu anda bir hata oluştu. Lütfen tekrar deneyin."

    def get_answer_from_documents(self, soru: str) -> Optional[str]:
        """
        Dokümanlardan cevap arar

        Args:
            soru: Kullanıcının sorusu

        Returns:
            Doküman tabanlı cevap veya None
        """
        if not Config.ENABLE_DOCUMENT_SEARCH:
            return None

        try:
            # Dokümanlarda ara
            results = self.doc_reader.search_in_documents(soru, max_results=3)

            if not results:
                logger.info("Dokümanlarda ilgili bilgi bulunamadı")
                return None

            # Bulunan bilgileri birleştir
            context = "Dokümanlarda bulunan ilgili bilgiler:\n\n"
            for i, result in enumerate(results, 1):
                context += f"{i}. {result['document']}:\n{result['snippet']}\n\n"

            # ChatGPT ile yanıt oluştur
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": f"Aşağıdaki bilgileri kullanarak şu soruya cevap ver:\n\nSoru: {soru}\n\n{context}"}
            ]

            answer = self.call_chatgpt(messages)
            logger.info(f"Doküman tabanlı yanıt oluşturuldu")

            return answer

        except Exception as e:
            logger.error(f"Doküman arama hatası: {str(e)}")
            return None

    def enhance_answer_with_chatgpt(self, soru: str, base_answer: str) -> str:
        """
        Stored procedure'dan gelen cevabı ChatGPT ile geliştirir

        Args:
            soru: Kullanıcının sorusu
            base_answer: Temel cevap (SP'den gelen)

        Returns:
            Geliştirilmiş cevap
        """
        try:
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": f"Şu soruya verilen cevabı daha detaylı ve anlaşılır hale getir:\n\nSoru: {soru}\nCevap: {base_answer}"}
            ]

            enhanced_answer = self.call_chatgpt(messages)
            logger.info("Cevap ChatGPT ile geliştirildi")

            return enhanced_answer

        except Exception as e:
            logger.error(f"Cevap geliştirme hatası: {str(e)}")
            return base_answer

    def get_answer(self, kullanici_id: int, soru: str, sohbet_gecmisi: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Kullanıcının sorusuna cevap verir (ana fonksiyon)

        İş akışı:
        1. Stored procedure'u çağır
        2. SP'den cevap geldiyse, opsiyonel olarak ChatGPT ile geliştir
        3. SP'den cevap gelmediyse, dokümanlardan ara
        4. Dokümanlardan da bulunamazsa, ChatGPT'ye sor
        5. Sonucu veritabanına kaydet

        Args:
            kullanici_id: Kullanıcı ID
            soru: Kullanıcının sorusu
            sohbet_gecmisi: Önceki sohbet geçmişi (opsiyonel)

        Returns:
            Cevap bilgileri
        """
        try:
            logger.info(f"Soru alındı (Kullanıcı: {kullanici_id}): {soru}")

            # 1. STORED PROCEDURE'U ÇAĞIR
            sp_result = None
            if Config.ENABLE_SP_SEARCH:
                try:
                    sp_result = self.db.call_sp_soru_cevap(kullanici_id, soru)
                except Exception as e:
                    logger.error(f"SP çağrısı hatası: {str(e)}")

            # 2. SP'DEN CEVAP VAR MI?
            if sp_result and sp_result.get('cevap'):
                cevap = sp_result['cevap']
                kaynak = f"Stored Procedure ({sp_result.get('soru_tur_kod', 'BILINMIYOR')})"

                logger.info(f"SP'den cevap alındı: {sp_result.get('soru_tur_kod')}")

                return {
                    'success': True,
                    'cevap': cevap,
                    'kaynak': kaynak,
                    'soru_tur_kod': sp_result.get('soru_tur_kod'),
                    'soru_tur_id': sp_result.get('soru_tur_id')
                }

            # 3. DOKÜMANLARDAN ARA
            doc_answer = self.get_answer_from_documents(soru)
            if doc_answer:
                logger.info("Dokümanlardan cevap bulundu")

                # Veritabanına kaydet
                self._save_to_database(kullanici_id, soru, doc_answer, None)

                return {
                    'success': True,
                    'cevap': doc_answer,
                    'kaynak': 'Dokümanlar + ChatGPT',
                    'soru_tur_kod': 'DOKUMAN',
                    'soru_tur_id': None
                }

            # 4. CHATGPT İLE GENEL CEVAP
            logger.info("ChatGPT ile genel cevap üretiliyor")

            messages = [{"role": "system", "content": self.system_message}]

            # Sohbet geçmişini ekle (varsa)
            if sohbet_gecmisi:
                for msg in sohbet_gecmisi[-Config.MAX_HISTORY_LENGTH:]:
                    messages.append({"role": "user", "content": msg.get('soru', '')})
                    messages.append({"role": "assistant", "content": msg.get('cevap', '')})

            # Yeni soruyu ekle
            messages.append({"role": "user", "content": soru})

            chatgpt_answer = self.call_chatgpt(messages)

            # Veritabanına kaydet
            self._save_to_database(kullanici_id, soru, chatgpt_answer, None)

            return {
                'success': True,
                'cevap': chatgpt_answer,
                'kaynak': 'ChatGPT',
                'soru_tur_kod': 'GENEL',
                'soru_tur_id': None
            }

        except Exception as e:
            logger.error(f"Cevap üretme hatası: {str(e)}")
            error_message = "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."

            return {
                'success': False,
                'cevap': error_message,
                'kaynak': 'HATA',
                'error': str(e)
            }

    def _save_to_database(self, kullanici_id: int, soru: str, cevap: str, soru_tur_id: Optional[int]):
        """
        Sohbeti veritabanına kaydeder

        Args:
            kullanici_id: Kullanıcı ID
            soru: Soru
            cevap: Cevap
            soru_tur_id: Soru türü ID (opsiyonel)
        """
        try:
            query = """
                INSERT INTO SOHBETLER (KullaniciId, Soru, Cevap, SoruTurId, Tarih)
                VALUES (?, ?, ?, ?, GETDATE())
            """
            self.db.execute_non_query(query, (kullanici_id, soru, cevap, soru_tur_id))
            logger.debug("Sohbet veritabanına kaydedildi")

        except Exception as e:
            logger.error(f"Veritabanına kaydetme hatası: {str(e)}")

    def get_sohbet_gecmisi(self, kullanici_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Kullanıcının sohbet geçmişini getirir

        Args:
            kullanici_id: Kullanıcı ID
            limit: Maksimum kayıt sayısı

        Returns:
            Sohbet geçmişi
        """
        try:
            return self.db.get_sohbet_gecmisi(kullanici_id, limit)
        except Exception as e:
            logger.error(f"Sohbet geçmişi getirme hatası: {str(e)}")
            return []

    def clear_sohbet_gecmisi(self, kullanici_id: int) -> bool:
        """
        Kullanıcının sohbet geçmişini siler

        Args:
            kullanici_id: Kullanıcı ID

        Returns:
            Başarılı ise True
        """
        try:
            query = "DELETE FROM SOHBETLER WHERE KullaniciId = ?"
            self.db.execute_non_query(query, (kullanici_id,))
            logger.info(f"Kullanıcı {kullanici_id} sohbet geçmişi silindi")
            return True

        except Exception as e:
            logger.error(f"Sohbet geçmişi silme hatası: {str(e)}")
            return False


# Test fonksiyonu
if __name__ == "__main__":
    print("=" * 50)
    print("CHATBOT TESTİ")
    print("=" * 50)

    # API key kontrolü
    if not Config.OPENAI_API_KEY:
        print("\n✗ OPENAI_API_KEY bulunamadı!")
        print("Lütfen .env dosyasında OPENAI_API_KEY tanımlayın.")
    else:
        print("\n✓ OpenAI API key bulundu")

        chatbot = ChatBot()

        # Test sorusu
        test_soru = "Merhaba, bana yardımcı olabilir misin?"
        print(f"\nTest Sorusu: {test_soru}")

        try:
            result = chatbot.get_answer(1, test_soru)
            print(f"\nKaynak: {result.get('kaynak')}")
            print(f"Cevap: {result.get('cevap')}")
        except Exception as e:
            print(f"\n✗ Hata: {str(e)}")
