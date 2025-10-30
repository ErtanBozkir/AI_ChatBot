"""
RAG (Retrieval-Augmented Generation) Engine
Doküman tabanlı soru-cevap sistemi
"""

import logging
import json
import time
from typing import Dict, Any, List
from openai import OpenAI

from config import Config
from vector_store import VectorStoreManager
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG sistemi - Doküman tabanlı AI cevaplama"""

    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.db = DatabaseManager()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

        # RAG ayarları
        self.top_k = 5  # En benzer kaç chunk alınacak
        self.similarity_threshold = 0.3  # Minimum benzerlik skoru
        self.model = Config.OPENAI_MODEL

    def should_use_documents(self, question: str) -> bool:
        """
        Sorunun dokümanlardan mı yoksa SQL'den mi cevaplanacağına karar verir

        Args:
            question: Kullanıcı sorusu

        Returns:
            True ise dokümanlardan cevapla
        """
        # SQL keywords (kullanıcı verisiyle ilgili - kişisel data)
        sql_keywords = [
            'kaç', 'ne kadar', 'izin', 'maaş', 'zimmet', 'bordro',
            'mesai', 'tatil', 'kalan', 'toplam', 'son',
            'hangi', 'departman', 'çalışıyorum', 'benim', 'bende',
            'kullandığım', 'aldığım', 'talep', 'yıllık', 'üzerimde',
            'yıldır', 'ne zaman', 'kaç gün', 'avans', 'harcama',
            'stok', 'bakiye', 'adet', 'miktar', 'ürün', 'malzeme', 'depo'
        ]

        # Document keywords (şirket kuralları, prosedürler, talimatlar)
        doc_keywords = [
            'nasıl', 'nedir', 'ne demek', 'prosedür', 'kural', 'politika',
            'talimat', 'süreç', 'adım', 'gerekli', 'başvuru', 'form',
            'yapılır', 'uygulanır', 'şekilde'
        ]

        question_lower = question.lower()

        # SQL keyword varsa ve doc keyword yoksa SQL kullan
        has_sql_keyword = any(kw in question_lower for kw in sql_keywords)
        has_doc_keyword = any(kw in question_lower for kw in doc_keywords)

        # "nasıl", "nedir" gibi AÇIKLAYICI sorular dokümandan
        # ANCAK kişisel veri içeriyorsa (hangi departmandayım, nasıl izin alabilirim) SQL+Doküman
        if has_doc_keyword and not has_sql_keyword:
            return True

        # Kişisel veri sorgusu ise SQL
        if has_sql_keyword:
            return False

        # Belirsiz durumlarda doküman ara
        return True

    def answer_from_documents(
        self,
        question: str,
        tc_kimlik_no: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Soruyu dokümanlardan cevaplar (RAG)

        Args:
            question: Kullanıcı sorusu
            tc_kimlik_no: Kullanıcı TC no
            session_id: Session ID

        Returns:
            Cevap ve metadata
        """
        start_time = time.time()

        try:
            # 1. Relevant chunk'ları bul
            relevant_chunks = self.vector_store.similarity_search(
                question,
                k=self.top_k,
                score_threshold=self.similarity_threshold
            )

            if not relevant_chunks:
                return {
                    'success': False,
                    'cevap': 'Üzgünüm, sorunuzla ilgili doküman bulunamadı.',
                    'kaynak': 'Dokümanlar',
                    'chunks_found': 0
                }

            # 2. Context oluştur
            context_parts = []
            for i, chunk in enumerate(relevant_chunks, 1):
                context_parts.append(
                    f"[Doküman {i}: {chunk['file_name']}]\n{chunk['content']}"
                )

            context = "\n\n---\n\n".join(context_parts)

            # 3. GPT'ye prompt gönder
            system_prompt = """Sen KNS Otomotiv şirketinin AI asistanısın.
Görevin: Şirket dokümanlarından yararlanarak çalışanların sorularını cevaplamak.

Kurallar:
- Sadece verilen dokümanlar içindeki bilgileri kullan
- Emin olmadığın konularda "bu konuda yetkili birimle iletişime geçmenizi öneririm" de
- Cevaplarını açık, anlaşılır ve profesyonel bir dille ver
- Doküman adlarını kaynak olarak belirt"""

            user_prompt = f"""Soru: {question}

İlgili Dokümanlar:
{context}

Lütfen yukarıdaki dokümanları kullanarak soruyu cevapla."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            answer = response.choices[0].message.content

            # 4. Cevabı database'e kaydet
            elapsed_time = int((time.time() - start_time) * 1000)
            chunk_ids = [c['chunk_id'] for c in relevant_chunks]

            # Database'e kaydet
            self.db.execute_non_query(
                """
                INSERT INTO DOKUMAN_SORGULARI
                (TcKimlikNo, SessionId, Soru, Cevap, KullanilanChunklar, SimilarityScore, CevapSuresi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tc_kimlik_no,
                    session_id,
                    question,
                    answer,
                    json.dumps(chunk_ids),
                    float(relevant_chunks[0]['similarity_score']),  # numpy.float32 -> Python float
                    elapsed_time
                )
            )

            # Kaynak bilgisi
            unique_files = list(set([c['file_name'] for c in relevant_chunks]))
            kaynak = f"Dokümanlar: {', '.join(unique_files[:3])}"

            logger.info(
                f"RAG cevap oluşturuldu: {len(relevant_chunks)} chunk, "
                f"{elapsed_time}ms"
            )

            return {
                'success': True,
                'cevap': answer,
                'kaynak': kaynak,
                'guven_skoru': float(relevant_chunks[0]['similarity_score']),  # numpy.float32 -> Python float
                'chunks_found': len(relevant_chunks),
                'response_time_ms': elapsed_time,
                'documents_used': unique_files
            }

        except Exception as e:
            logger.error(f"RAG hatası: {str(e)}")
            return {
                'success': False,
                'cevap': 'Üzgünüm, cevap oluştururken bir hata oluştu.',
                'error': str(e)
            }

    def hybrid_answer(
        self,
        question: str,
        tc_kimlik_no: str,
        session_id: str = None,
        sql_answer: str = None
    ) -> Dict[str, Any]:
        """
        Hem SQL hem doküman sonuçlarını birleştiren hibrit cevap

        Args:
            question: Soru
            tc_kimlik_no: TC no
            session_id: Session ID
            sql_answer: SQL'den gelen cevap (varsa)

        Returns:
            Birleştirilmiş cevap
        """
        try:
            # Dokümanlardan cevap al
            doc_result = self.answer_from_documents(question, tc_kimlik_no, session_id)

            if not doc_result['success']:
                # Sadece SQL cevabı varsa onu döndür
                if sql_answer:
                    return {
                        'success': True,
                        'cevap': sql_answer,
                        'kaynak': 'SQL',
                        'guven_skoru': 1.0
                    }
                return doc_result

            # Her ikisi de varsa birleştir
            if sql_answer:
                combined = f"{sql_answer}\n\n**Ek Bilgi:**\n{doc_result['cevap']}"
                return {
                    'success': True,
                    'cevap': combined,
                    'kaynak': 'SQL + Dokümanlar',
                    'guven_skoru': doc_result.get('guven_skoru', 0.5),
                    'hybrid': True
                }

            return doc_result

        except Exception as e:
            logger.error(f"Hybrid answer hatası: {str(e)}")
            return {
                'success': False,
                'cevap': 'Üzgünüm, cevap oluştururken bir hata oluştu.',
                'error': str(e)
            }


# Test fonksiyonu
if __name__ == "__main__":
    print("=" * 60)
    print("RAG ENGINE TEST")
    print("=" * 60)

    if not Config.OPENAI_API_KEY:
        print("\n✗ OPENAI_API_KEY bulunamadı!")
        exit(1)

    rag = RAGEngine()

    # Test soruları
    test_questions = [
        "İzin talebi nasıl yapılır?",
        "Maaş ödeme günü nedir?",
        "Çalışma saatleri nedir?"
    ]

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Soru: {q}")
        print(f"{'='*60}")

        # Routing kararı
        use_docs = rag.should_use_documents(q)
        print(f"Kaynak: {'Dokümanlar' if use_docs else 'SQL'}")

        if use_docs:
            result = rag.answer_from_documents(q, "12345678901")
            if result['success']:
                print(f"\nCevap:\n{result['cevap']}")
                print(f"\nKaynak: {result.get('kaynak', 'N/A')}")
                print(f"Güven Skoru: {result.get('guven_skoru', 0):.2f}")
                print(f"Chunk Sayısı: {result.get('chunks_found', 0)}")
            else:
                print(f"\n✗ Hata: {result.get('error', 'Unknown')}")

    print("\n✓ RAG Engine modülü hazır!")
