"""
Vector Store Modülü
FAISS ile embedding ve similarity search
"""

import os
import pickle
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path

# OpenAI embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config import Config
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreManager:
    """FAISS vector store yönetimi"""

    def __init__(self):
        self.db = DatabaseManager()
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=Config.OPENAI_API_KEY,
            model="text-embedding-ada-002"
        )

        # Vector store dizini
        self.vector_store_dir = Path(Config.DOCUMENTS_PATH) / "vector_stores"
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)

        # Ana FAISS index dosyası
        self.index_path = self.vector_store_dir / "faiss_index"

        # Vector store (lazy loading)
        self._vector_store = None

    @property
    def vector_store(self):
        """Vector store'u lazy load eder"""
        if self._vector_store is None:
            self._vector_store = self.load_vector_store()
        return self._vector_store

    def create_embeddings_for_chunks(self, file_id: int) -> Dict[str, Any]:
        """
        Bir dosyanın chunklarına embedding oluşturur ve FAISS'e ekler

        Args:
            file_id: Dosya ID'si

        Returns:
            İşlem sonucu
        """
        try:
            # Chunk'ları database'den al
            query = """
                SELECT ChunkId, ChunkMetni, ChunkIndex
                FROM DOKUMAN_CHUNKS
                WHERE DosyaId = ? AND EmbeddingOlusturuldu = 0
                ORDER BY ChunkIndex
            """
            chunks = self.db.execute_query(query, (file_id,))

            if not chunks:
                return {
                    'success': True,
                    'message': 'Tüm chunklar zaten işlenmiş',
                    'embedded_count': 0
                }

            # Dosya bilgisini al
            file_info = self.db.execute_query(
                "SELECT DosyaAdi FROM DOSYALAR WHERE DosyaId = ?",
                (file_id,)
            )
            file_name = file_info[0]['DosyaAdi'] if file_info else f"File_{file_id}"

            # Langchain Document objelerine dönüştür
            documents = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk['ChunkMetni'],
                    metadata={
                        'chunk_id': chunk['ChunkId'],
                        'file_id': file_id,
                        'file_name': file_name,
                        'chunk_index': chunk['ChunkIndex']
                    }
                )
                documents.append(doc)

            # Vector store'a ekle
            if self._vector_store is None:
                # İlk kez oluşturuluyorsa
                self._vector_store = FAISS.from_documents(documents, self.embeddings)
                logger.info(f"Yeni FAISS index oluşturuldu: {len(documents)} doküman")
            else:
                # Mevcut index'e ekle
                self._vector_store.add_documents(documents)
                logger.info(f"FAISS index'e eklendi: {len(documents)} doküman")

            # Index'i kaydet
            self.save_vector_store()

            # Database'de embedding durumunu güncelle
            for chunk in chunks:
                self.db.execute_non_query(
                    "UPDATE DOKUMAN_CHUNKS SET EmbeddingOlusturuldu = 1 WHERE ChunkId = ?",
                    (chunk['ChunkId'],)
                )

            logger.info(f"Dosya {file_id} için {len(chunks)} chunk embed edildi")

            return {
                'success': True,
                'file_id': file_id,
                'embedded_count': len(chunks),
                'total_documents_in_store': len(self._vector_store.docstore._dict)
            }

        except Exception as e:
            error_msg = f"Embedding oluşturma hatası: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Sorguya en benzer chunk'ları bulur

        Args:
            query: Arama sorgusu
            k: Döndürülecek maksimum sonuç sayısı
            score_threshold: Minimum benzerlik skoru (0-1 arası)

        Returns:
            En benzer chunk'lar ve metadata'ları
        """
        try:
            if self.vector_store is None:
                logger.warning("Vector store boş")
                return []

            # Similarity search with scores
            results_with_scores = self.vector_store.similarity_search_with_score(
                query, k=k
            )

            # Sonuçları filtrele ve formatla
            formatted_results = []
            for doc, score in results_with_scores:
                # FAISS distance'ı similarity'ye çevir (düşük distance = yüksek similarity)
                # L2 distance kullanıyoruz, 0'a yakın = çok benzer
                similarity = 1 / (1 + score)  # Score'u 0-1 arası similarity'ye dönüştür

                if similarity >= score_threshold:
                    formatted_results.append({
                        'chunk_id': doc.metadata.get('chunk_id'),
                        'file_id': doc.metadata.get('file_id'),
                        'file_name': doc.metadata.get('file_name'),
                        'chunk_index': doc.metadata.get('chunk_index'),
                        'content': doc.page_content,
                        'similarity_score': similarity,
                        'distance': score
                    })

            logger.info(f"Sorgu '{query[:50]}...' için {len(formatted_results)} sonuç bulundu")
            return formatted_results

        except Exception as e:
            logger.error(f"Similarity search hatası: {str(e)}")
            return []

    def save_vector_store(self):
        """Vector store'u diske kaydeder"""
        try:
            if self._vector_store is not None:
                self._vector_store.save_local(str(self.index_path))
                logger.info(f"Vector store kaydedildi: {self.index_path}")
        except Exception as e:
            logger.error(f"Vector store kaydetme hatası: {str(e)}")

    def load_vector_store(self):
        """Vector store'u diskten yükler"""
        try:
            if self.index_path.exists():
                vector_store = FAISS.load_local(
                    str(self.index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                doc_count = len(vector_store.docstore._dict)
                logger.info(f"Vector store yüklendi: {doc_count} doküman")
                return vector_store
            else:
                logger.info("Vector store bulunamadı, yeni oluşturulacak")
                return None
        except Exception as e:
            logger.error(f"Vector store yükleme hatası: {str(e)}")
            return None

    def rebuild_vector_store(self) -> Dict[str, Any]:
        """
        Tüm dokümanlar için vector store'u sıfırdan oluşturur

        Returns:
            İşlem sonucu
        """
        try:
            # Tüm embedded olmamış chunkları al
            query = """
                SELECT c.ChunkId, c.ChunkMetni, c.ChunkIndex, c.DosyaId, d.DosyaAdi
                FROM DOKUMAN_CHUNKS c
                INNER JOIN DOSYALAR d ON c.DosyaId = d.DosyaId
                WHERE d.AktifMi = 1
                ORDER BY c.DosyaId, c.ChunkIndex
            """
            chunks = self.db.execute_query(query)

            if not chunks:
                return {
                    'success': False,
                    'message': 'İşlenecek chunk bulunamadı'
                }

            # Document'leri oluştur
            documents = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk['ChunkMetni'],
                    metadata={
                        'chunk_id': chunk['ChunkId'],
                        'file_id': chunk['DosyaId'],
                        'file_name': chunk['DosyaAdi'],
                        'chunk_index': chunk['ChunkIndex']
                    }
                )
                documents.append(doc)

            # Yeni vector store oluştur
            self._vector_store = FAISS.from_documents(documents, self.embeddings)
            self.save_vector_store()

            # Tüm chunk'ları embedded olarak işaretle
            self.db.execute_non_query("UPDATE DOKUMAN_CHUNKS SET EmbeddingOlusturuldu = 1")

            logger.info(f"Vector store yeniden oluşturuldu: {len(documents)} doküman")

            return {
                'success': True,
                'total_documents': len(documents),
                'message': 'Vector store başarıyla yeniden oluşturuldu'
            }

        except Exception as e:
            error_msg = f"Vector store rebuild hatası: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def delete_file_from_store(self, file_id: int) -> bool:
        """
        Bir dosyanın tüm chunk'larını vector store'dan siler
        NOT: FAISS doğrudan silme desteklemez, rebuild gerekir

        Args:
            file_id: Dosya ID'si

        Returns:
            Başarılı ise True
        """
        try:
            # Chunkları database'den sil
            self.db.execute_non_query(
                "DELETE FROM DOKUMAN_CHUNKS WHERE DosyaId = ?",
                (file_id,)
            )

            # Vector store'u yeniden oluştur
            self.rebuild_vector_store()

            logger.info(f"Dosya {file_id} vector store'dan silindi")
            return True
        except Exception as e:
            logger.error(f"Dosya silme hatası: {str(e)}")
            return False

    def get_store_stats(self) -> Dict[str, Any]:
        """Vector store istatistiklerini döndürür"""
        try:
            if self.vector_store is None:
                return {
                    'total_documents': 0,
                    'index_exists': False
                }

            return {
                'total_documents': len(self.vector_store.docstore._dict),
                'index_exists': True,
                'index_path': str(self.index_path)
            }
        except Exception as e:
            logger.error(f"Stats hatası: {str(e)}")
            return {
                'error': str(e)
            }


# Test fonksiyonu
if __name__ == "__main__":
    print("=" * 60)
    print("VECTOR STORE TEST")
    print("=" * 60)

    if not Config.OPENAI_API_KEY:
        print("\n✗ OPENAI_API_KEY bulunamadı!")
        exit(1)

    vs = VectorStoreManager()

    # Stats
    stats = vs.get_store_stats()
    print(f"\nVector Store İstatistikleri:")
    print(f"  Toplam Doküman: {stats.get('total_documents', 0)}")
    print(f"  Index Var mı: {stats.get('index_exists', False)}")

    # Test search
    test_query = "izin talebi nasıl yapılır"
    print(f"\nTest Sorgu: '{test_query}'")
    results = vs.similarity_search(test_query, k=3)
    print(f"Bulunan Sonuç: {len(results)}")

    for i, result in enumerate(results, 1):
        print(f"\n  {i}. Sonuç:")
        print(f"     Dosya: {result.get('file_name')}")
        print(f"     Similarity: {result.get('similarity_score', 0):.3f}")
        print(f"     İçerik: {result.get('content', '')[:100]}...")

    print("\n✓ Vector Store modülü hazır!")
