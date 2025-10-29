"""
Doküman Okuma Modülü
PDF, Word, Excel, PowerPoint ve metin dosyalarını okur
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

# Doküman okuma kütüphaneleri
import PyPDF2
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

from config import Config

# Logging ayarları
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class DocumentReader:
    """Doküman okuma sınıfı"""

    def __init__(self, documents_path: str = None):
        self.documents_path = documents_path or Config.DOCUMENTS_PATH
        self.supported_types = Config.SUPPORTED_DOCUMENT_TYPES

    def read_pdf(self, file_path: str) -> str:
        """
        PDF dosyasını okur

        Args:
            file_path: PDF dosya yolu

        Returns:
            PDF içeriği (metin)
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"

            logger.info(f"PDF okundu: {file_path} ({num_pages} sayfa)")
            return text.strip()

        except Exception as e:
            logger.error(f"PDF okuma hatası ({file_path}): {str(e)}")
            return ""

    def read_docx(self, file_path: str) -> str:
        """
        Word (.docx) dosyasını okur

        Args:
            file_path: Word dosya yolu

        Returns:
            Word içeriği (metin)
        """
        try:
            doc = Document(file_path)
            text = ""

            # Paragrafları oku
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"

            # Tabloları oku
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + " "
                    text += "\n"

            logger.info(f"Word dosyası okundu: {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Word okuma hatası ({file_path}): {str(e)}")
            return ""

    def read_xlsx(self, file_path: str) -> str:
        """
        Excel (.xlsx) dosyasını okur

        Args:
            file_path: Excel dosya yolu

        Returns:
            Excel içeriği (metin)
        """
        try:
            workbook = load_workbook(file_path, data_only=True)
            text = ""

            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                text += f"\n=== {sheet_name} ===\n"

                for row in sheet.iter_rows(values_only=True):
                    # None değerleri filtrele
                    row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                    if row_text.strip():
                        text += row_text + "\n"

            logger.info(f"Excel dosyası okundu: {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Excel okuma hatası ({file_path}): {str(e)}")
            return ""

    def read_pptx(self, file_path: str) -> str:
        """
        PowerPoint (.pptx) dosyasını okur

        Args:
            file_path: PowerPoint dosya yolu

        Returns:
            PowerPoint içeriği (metin)
        """
        try:
            prs = Presentation(file_path)
            text = ""

            for slide_num, slide in enumerate(prs.slides, start=1):
                text += f"\n=== Slayt {slide_num} ===\n"

                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"

            logger.info(f"PowerPoint dosyası okundu: {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"PowerPoint okuma hatası ({file_path}): {str(e)}")
            return ""

    def read_txt(self, file_path: str) -> str:
        """
        Metin (.txt) dosyasını okur

        Args:
            file_path: Metin dosya yolu

        Returns:
            Dosya içeriği
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            logger.info(f"Metin dosyası okundu: {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Metin okuma hatası ({file_path}): {str(e)}")
            return ""

    def read_document(self, file_path: str) -> str:
        """
        Dosya uzantısına göre uygun okuyucuyu seçer ve dosyayı okur

        Args:
            file_path: Dosya yolu

        Returns:
            Dosya içeriği
        """
        extension = os.path.splitext(file_path)[1].lower()

        readers = {
            '.pdf': self.read_pdf,
            '.docx': self.read_docx,
            '.doc': self.read_docx,
            '.xlsx': self.read_xlsx,
            '.xls': self.read_xlsx,
            '.txt': self.read_txt,
            '.pptx': self.read_pptx,
            '.ppt': self.read_pptx,
        }

        reader = readers.get(extension)
        if reader:
            return reader(file_path)
        else:
            logger.warning(f"Desteklenmeyen dosya türü: {extension}")
            return ""

    def get_all_documents(self) -> List[Dict[str, str]]:
        """
        Dokümanlar klasöründeki tüm dosyaları listeler

        Returns:
            Dosya bilgileri listesi
        """
        documents = []

        if not os.path.exists(self.documents_path):
            logger.warning(f"Dokümanlar klasörü bulunamadı: {self.documents_path}")
            return documents

        for root, dirs, files in os.walk(self.documents_path):
            for file in files:
                file_path = os.path.join(root, file)
                extension = os.path.splitext(file)[1].lower()

                if extension in self.supported_types:
                    documents.append({
                        'name': file,
                        'path': file_path,
                        'extension': extension,
                        'size': os.path.getsize(file_path)
                    })

        logger.info(f"{len(documents)} doküman bulundu")
        return documents

    def search_in_documents(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Tüm dokümanlarda anahtar kelime araması yapar

        Args:
            query: Arama sorgusu
            max_results: Maksimum sonuç sayısı

        Returns:
            Eşleşen dokümanlar ve içerikler
        """
        results = []
        documents = self.get_all_documents()
        query_lower = query.lower()

        for doc in documents:
            try:
                content = self.read_document(doc['path'])
                content_lower = content.lower()

                # Sorgu içerikte var mı?
                if query_lower in content_lower:
                    # İlgili bölümü bul (query etrafında 200 karakter)
                    index = content_lower.find(query_lower)
                    start = max(0, index - 100)
                    end = min(len(content), index + len(query) + 100)
                    snippet = content[start:end].strip()

                    results.append({
                        'document': doc['name'],
                        'path': doc['path'],
                        'snippet': snippet,
                        'relevance': content_lower.count(query_lower)
                    })

                    # Maksimum sonuç sayısına ulaşıldı mı?
                    if len(results) >= max_results:
                        break

            except Exception as e:
                logger.error(f"Doküman arama hatası ({doc['name']}): {str(e)}")
                continue

        # İlgililik skoruna göre sırala
        results.sort(key=lambda x: x['relevance'], reverse=True)

        logger.info(f"'{query}' için {len(results)} sonuç bulundu")
        return results

    def get_document_summary(self, file_path: str, max_length: int = 500) -> str:
        """
        Dokümanın özetini döndürür

        Args:
            file_path: Dosya yolu
            max_length: Maksimum özet uzunluğu

        Returns:
            Doküman özeti
        """
        try:
            content = self.read_document(file_path)

            if len(content) <= max_length:
                return content

            # İlk max_length karakteri al
            summary = content[:max_length].rsplit(' ', 1)[0] + "..."

            return summary

        except Exception as e:
            logger.error(f"Özet oluşturma hatası ({file_path}): {str(e)}")
            return ""

    def read_all_documents(self) -> str:
        """
        Tüm dokümanları okur ve tek bir metin olarak birleştirir

        Returns:
            Tüm dokümanların içeriği
        """
        all_content = ""
        documents = self.get_all_documents()

        for doc in documents:
            try:
                content = self.read_document(doc['path'])
                all_content += f"\n\n=== {doc['name']} ===\n\n{content}"
            except Exception as e:
                logger.error(f"Doküman okuma hatası ({doc['name']}): {str(e)}")
                continue

        logger.info(f"Toplam {len(documents)} doküman okundu")
        return all_content.strip()


# Test fonksiyonu
if __name__ == "__main__":
    print("=" * 50)
    print("DOKÜMAN OKUMA TESTİ")
    print("=" * 50)

    reader = DocumentReader()

    # Dokümanları listele
    documents = reader.get_all_documents()
    print(f"\nBulunan doküman sayısı: {len(documents)}")

    for doc in documents:
        print(f"\n  - {doc['name']} ({doc['extension']}, {doc['size']} byte)")

    # Arama testi
    if documents:
        print("\n" + "=" * 50)
        print("ARAMA TESTİ")
        print("=" * 50)

        test_query = "izin"
        results = reader.search_in_documents(test_query)

        print(f"\n'{test_query}' araması için {len(results)} sonuç:")
        for result in results:
            print(f"\n  Doküman: {result['document']}")
            print(f"  Snippet: {result['snippet'][:100]}...")
