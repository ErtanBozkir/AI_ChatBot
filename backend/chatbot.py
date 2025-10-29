"""
Chatbot Modülü
OpenAI ChatGPT API entegrasyonu ve yanıt üretme
"""

import logging
import json
from typing import List, Dict, Optional, Any
from openai import OpenAI

from config import Config
from database import DatabaseManager
from document_reader import DocumentReader
from question_analyzer import QuestionAnalyzer

# Logging ayarları
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class ChatBot:
    """Chatbot ana sınıfı"""

    def __init__(self):
        self.db = DatabaseManager()
        self.doc_reader = DocumentReader()
        self.analyzer = QuestionAnalyzer()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
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

    def get_answer(self, tc_kimlik_no: str, soru: str, sohbet_gecmisi: List[Dict[str, str]] = None, session_id: str = None) -> Dict[str, Any]:
        """
        Kullanıcının sorusuna cevap verir (ana fonksiyon) - V2 ile parametreli sorgular

        İş akışı:
        1. ChatGPT ile soruyu analiz et → soru türü + parametreler çıkar
        2. SP_SoruCevap_V2 çağır (JSON parametrelerle)
        3. SP'den cevap geldiyse, döndür
        4. SP'den cevap gelmediyse, dokümanlardan ara
        5. Dokümanlardan da bulunamazsa, ChatGPT ile genel cevap
        6. Sonucu veritabanına kaydet (SP bunu otomatik yapıyor)

        Args:
            tc_kimlik_no: TC Kimlik No
            soru: Kullanıcının sorusu
            sohbet_gecmisi: Önceki sohbet geçmişi (opsiyonel)

        Returns:
            Cevap bilgileri
        """
        try:
            logger.info(f"Soru alındı (TC: {tc_kimlik_no}): {soru}")

            # 1. CHATGPT İLE SORU ANALİZİ (Soru türü + parametreler) - CONTEXT İLE
            # Stored procedure mesajları TERS sırada getiriyor (en yeni önce), düzeltelim
            if sohbet_gecmisi:
                sohbet_gecmisi = list(reversed(sohbet_gecmisi))
            analysis = self.analyzer.analyze_question(soru, tc_kimlik_no, sohbet_gecmisi)
            soru_tur_kod = analysis.get('soru_tur_kod', 'BILINMIYOR')
            parametreler = analysis.get('parametreler', {})
            guven_skoru = analysis.get('guven_skoru', 0.0)

            logger.info(f"Soru analizi: Tür={soru_tur_kod}, Güven={guven_skoru}, Parametreler={parametreler}")

            # 2. STORED PROCEDURE V2'Yİ ÇAĞIR (JSON parametrelerle)
            sp_result = None
            if Config.ENABLE_SP_SEARCH and soru_tur_kod != 'BILINMIYOR':
                try:
                    parametreler_json = json.dumps(parametreler, ensure_ascii=False)
                    sp_result = self.db.call_sp_soru_cevap_v2(
                        tc_kimlik_no=tc_kimlik_no,
                        soru=soru,
                        soru_tur_kod=soru_tur_kod,
                        parametreler_json=parametreler_json
                    )
                except Exception as e:
                    logger.error(f"SP_V2 çağrısı hatası: {str(e)}")

            # 3. SP'DEN CEVAP VAR MI?
            if sp_result and sp_result.get('cevap'):
                cevap = sp_result['cevap']
                kaynak = f"Veritabanı ({soru_tur_kod})"

                logger.info(f"SP'den cevap alındı: {soru_tur_kod}")

                # SP cevabını da session_id ile kaydet
                self._save_to_database(tc_kimlik_no, soru, cevap, None, session_id)

                return {
                    'success': True,
                    'cevap': cevap,
                    'kaynak': kaynak,
                    'soru_tur_kod': soru_tur_kod,
                    'parametreler': parametreler,
                    'guven_skoru': guven_skoru
                }

            # 4. DOKÜMANLARDAN ARA
            doc_answer = self.get_answer_from_documents(soru)
            if doc_answer:
                logger.info("Dokümanlardan cevap bulundu")

                # Veritabanına kaydet
                self._save_to_database(tc_kimlik_no, soru, doc_answer, None, session_id)

                return {
                    'success': True,
                    'cevap': doc_answer,
                    'kaynak': 'Dokümanlar + ChatGPT',
                    'soru_tur_kod': 'DOKUMAN'
                }

            # 5. CHATGPT İLE GENEL CEVAP
            if not self.client:
                return {
                    'success': False,
                    'cevap': 'OpenAI API key tanımlı değil. Lütfen yöneticinizle iletişime geçin.',
                    'kaynak': 'HATA'
                }

            logger.info("ChatGPT ile genel cevap üretiliyor")

            messages = [{"role": "system", "content": self.system_message}]

            # Sohbet geçmişini ekle (varsa)
            if sohbet_gecmisi:
                for msg in sohbet_gecmisi[-Config.MAX_HISTORY_LENGTH:]:
                    messages.append({"role": "user", "content": msg.get('Soru', msg.get('soru', ''))})
                    messages.append({"role": "assistant", "content": msg.get('Cevap', msg.get('cevap', ''))})

            # Yeni soruyu ekle
            messages.append({"role": "user", "content": soru})

            chatgpt_answer = self.call_chatgpt(messages)

            # Veritabanına kaydet
            self._save_to_database(tc_kimlik_no, soru, chatgpt_answer, None, session_id)

            return {
                'success': True,
                'cevap': chatgpt_answer,
                'kaynak': 'ChatGPT',
                'soru_tur_kod': 'GENEL'
            }

        except Exception as e:
            logger.error(f"Cevap üretme hatası: {str(e)}")
            import traceback
            traceback.print_exc()

            error_message = "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."

            return {
                'success': False,
                'cevap': error_message,
                'kaynak': 'HATA',
                'error': str(e)
            }

    def _save_to_database(self, tc_kimlik_no: str, soru: str, cevap: str, soru_tur_id: Optional[int], session_id: Optional[str] = None):
        """
        Sohbeti veritabanına kaydeder

        Args:
            tc_kimlik_no: TC Kimlik No
            soru: Soru
            cevap: Cevap
            soru_tur_id: Soru türü ID (opsiyonel)
            session_id: Session ID (opsiyonel)
        """
        try:
            query = """
                INSERT INTO SOHBETLER (TcKimlikNo, Soru, Cevap, SoruTurId, Tarih, SessionId)
                VALUES (?, ?, ?, ?, GETDATE(), ?)
            """
            self.db.execute_non_query(query, (tc_kimlik_no, soru, cevap, soru_tur_id, session_id))
            logger.debug(f"Sohbet veritabanına kaydedildi (SessionId: {session_id})")

        except Exception as e:
            logger.error(f"Veritabanına kaydetme hatası: {str(e)}")

    def get_sohbet_gecmisi(self, tc_kimlik_no: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Kullanıcının sohbet geçmişini getirir

        Args:
            tc_kimlik_no: TC Kimlik No
            limit: Maksimum kayıt sayısı

        Returns:
            Sohbet geçmişi
        """
        try:
            return self.db.get_sohbet_gecmisi(tc_kimlik_no, limit)
        except Exception as e:
            logger.error(f"Sohbet geçmişi getirme hatası: {str(e)}")
            return []

    def clear_sohbet_gecmisi(self, tc_kimlik_no: str) -> bool:
        """
        Kullanıcının sohbet geçmişini siler

        Args:
            tc_kimlik_no: TC Kimlik No

        Returns:
            Başarılı ise True
        """
        try:
            query = "DELETE FROM SOHBETLER WHERE TcKimlikNo = ?"
            self.db.execute_non_query(query, (tc_kimlik_no,))
            logger.info(f"Kullanıcı {tc_kimlik_no} sohbet geçmişi silindi")
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
