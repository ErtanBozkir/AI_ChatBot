"""
Doküman İşleme Modülü
PDF ve Word dosyalarından metin çıkarma ve chunking
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path

# PDF ve Word işleme
import pdfplumber
from docx import Document

# Text splitting
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Database
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Doküman işleme ve chunking sınıfı"""

    def __init__(self):
        self.db = DatabaseManager()
        # Chunk ayarları
        self.chunk_size = 1000  # Her chunk max 1000 karakter
        self.chunk_overlap = 200  # Chunklar arası overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        PDF dosyasından metin çıkarır

        Args:
            pdf_path: PDF dosya yolu

        Returns:
            Çıkarılan metin
        """
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"

            logger.info(f"PDF'den {len(text)} karakter çıkarıldı: {pdf_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"PDF okuma hatası ({pdf_path}): {str(e)}")
            raise

    def extract_text_from_word(self, docx_path: str) -> str:
        """
        Word dosyasından metin çıkarır

        Args:
            docx_path: Word dosya yolu

        Returns:
            Çıkarılan metin
        """
        try:
            doc = Document(docx_path)
            paragraphs = []

            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)

            text = "\n\n".join(paragraphs)
            logger.info(f"Word'den {len(text)} karakter çıkarıldı: {docx_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Word okuma hatası ({docx_path}): {str(e)}")
            raise

    def split_text_into_chunks(self, text: str) -> List[str]:
        """
        Metni chunklara ayırır

        Args:
            text: Bölünecek metin

        Returns:
            Chunk listesi
        """
        try:
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Metin {len(chunks)} chunk'a bölündü")
            return chunks

        except Exception as e:
            logger.error(f"Chunk hatası: {str(e)}")
            raise

    def process_document(self, file_path: str, file_id: int) -> Dict[str, Any]:
        """
        Dokümanı işler: metin çıkarma + chunking + database kayıt

        Args:
            file_path: Dosya yolu
            file_id: DOSYALAR tablosundaki dosya ID'si

        Returns:
            İşlem sonucu
        """
        try:
            # Dosya uzantısını kontrol et
            file_ext = Path(file_path).suffix.lower()

            # İşlem durumunu güncelle: İşleniyor
            self.db.execute_non_query(
                "UPDATE DOSYALAR SET IslenmeDurumu = 0 WHERE DosyaId = ?",
                (file_id,)
            )

            # Metin çıkar
            if file_ext == '.pdf':
                text = self.extract_text_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                text = self.extract_text_from_word(file_path)
            else:
                raise ValueError(f"Desteklenmeyen dosya formatı: {file_ext}")

            if not text or len(text) < 50:
                raise ValueError("Dosyadan yeterli metin çıkarılamadı")

            # Chunklara ayır
            chunks = self.split_text_into_chunks(text)

            if not chunks:
                raise ValueError("Chunk oluşturulamadı")

            # Chunkları database'e kaydet - EXPLICIT COMMIT ile
            saved_chunks = []
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                for idx, chunk in enumerate(chunks):
                    cursor.execute("""
                        INSERT INTO DOKUMAN_CHUNKS (DosyaId, ChunkMetni, ChunkIndex, KarakterSayisi)
                        OUTPUT INSERTED.ChunkId
                        VALUES (?, ?, ?, ?)
                    """, (file_id, chunk, idx, len(chunk)))

                    result = cursor.fetchone()
                    if result:
                        chunk_id = result[0]
                        saved_chunks.append({
                            'chunk_id': chunk_id,
                            'chunk_index': idx,
                            'text': chunk,
                            'length': len(chunk)
                        })

                # TÜM CHUNK'LAR İÇİN TEK COMMIT
                conn.commit()
                logger.info(f"{len(saved_chunks)} chunk database'e kaydedildi ve commit edildi")

            # Dosya durumunu güncelle: İşlendi
            self.db.execute_non_query(
                "UPDATE DOSYALAR SET IslenmeDurumu = 1, ChunkSayisi = ? WHERE DosyaId = ?",
                (len(saved_chunks), file_id)
            )

            logger.info(f"Dosya başarıyla işlendi: {file_path} ({len(saved_chunks)} chunk)")

            return {
                'success': True,
                'file_id': file_id,
                'total_chunks': len(saved_chunks),
                'total_characters': len(text),
                'chunks': saved_chunks
            }

        except Exception as e:
            error_msg = f"Doküman işleme hatası: {str(e)}"
            logger.error(error_msg)

            # Hata durumunu kaydet
            self.db.execute_non_query(
                "UPDATE DOSYALAR SET IslenmeDurumu = 2, IslenmeHatasi = ? WHERE DosyaId = ?",
                (error_msg, file_id)
            )

            return {
                'success': False,
                'error': error_msg,
                'file_id': file_id
            }

    def get_document_chunks(self, file_id: int) -> List[Dict[str, Any]]:
        """
        Bir dokümanın tüm chunklarını getirir

        Args:
            file_id: Dosya ID'si

        Returns:
            Chunk listesi
        """
        query = """
            SELECT ChunkId, ChunkMetni, ChunkIndex, KarakterSayisi
            FROM DOKUMAN_CHUNKS
            WHERE DosyaId = ?
            ORDER BY ChunkIndex
        """
        result = self.db.execute_query(query, (file_id,))
        return result if result else []

    def delete_document_chunks(self, file_id: int) -> bool:
        """
        Bir dokümanın tüm chunklarını siler

        Args:
            file_id: Dosya ID'si

        Returns:
            Başarılı ise True
        """
        try:
            self.db.execute_non_query(
                "DELETE FROM DOKUMAN_CHUNKS WHERE DosyaId = ?",
                (file_id,)
            )
            logger.info(f"Dosya {file_id} için chunklar silindi")
            return True
        except Exception as e:
            logger.error(f"Chunk silme hatası: {str(e)}")
            return False


# Test fonksiyonu
if __name__ == "__main__":
    print("=" * 60)
    print("DOCUMENT PROCESSOR TEST")
    print("=" * 60)

    processor = DocumentProcessor()

    # Test PDF (eğer varsa)
    test_pdf = "test.pdf"
    if os.path.exists(test_pdf):
        print(f"\nTest PDF: {test_pdf}")
        text = processor.extract_text_from_pdf(test_pdf)
        print(f"Çıkarılan metin uzunluğu: {len(text)} karakter")

        chunks = processor.split_text_into_chunks(text)
        print(f"Oluşan chunk sayısı: {len(chunks)}")
        print(f"\nİlk chunk (preview):\n{chunks[0][:200]}...")
    else:
        print(f"\n✗ Test dosyası bulunamadı: {test_pdf}")

    print("\n✓ Document Processor modülü hazır!")
