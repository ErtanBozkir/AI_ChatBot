"""
Konfigürasyon Modülü
Veritabanı, API ve uygulama ayarlarını yönetir
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# .env dosyasını yükle
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Ana konfigürasyon sınıfı"""

    # Flask ayarları
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

    # MSSQL Veritabanı ayarları
    DB_SERVER = os.getenv('DB_SERVER', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'ChatBotDB')
    DB_USERNAME = os.getenv('DB_USERNAME', 'sa')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'YourPassword123!')
    DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    DB_PORT = os.getenv('DB_PORT', '1433')

    # Bağlantı string'i oluştur
    @property
    def get_connection_string(self):
        """MSSQL bağlantı string'ini döndürür"""
        return (
            f"DRIVER={{{self.DB_DRIVER}}};"
            f"SERVER={self.DB_SERVER},{self.DB_PORT};"
            f"DATABASE={self.DB_NAME};"
            f"UID={self.DB_USERNAME};"
            f"PWD={self.DB_PASSWORD};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
        )

    # OpenAI API ayarları
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0.7))
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 1000))

    # JWT Token ayarları
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))

    # Doküman ayarları
    DOCUMENTS_PATH = os.getenv('DOCUMENTS_PATH', os.path.join(
        Path(__file__).parent.parent, 'documents'
    ))
    SUPPORTED_DOCUMENT_TYPES = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt', '.pptx']

    # Chatbot ayarları
    MAX_HISTORY_LENGTH = int(os.getenv('MAX_HISTORY_LENGTH', 10))
    ENABLE_DOCUMENT_SEARCH = os.getenv('ENABLE_DOCUMENT_SEARCH', 'True').lower() == 'true'
    ENABLE_SP_SEARCH = os.getenv('ENABLE_SP_SEARCH', 'True').lower() == 'true'

    # Logging ayarları
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'chatbot.log')

    # CORS ayarları
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    @classmethod
    def validate(cls):
        """Konfigürasyon doğrulama"""
        errors = []
        warnings = []

        if not cls.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY bulunamadı - ChatGPT özellikleri çalışmayacak")

        if not cls.DB_SERVER:
            errors.append("DB_SERVER bulunamadı!")

        if not os.path.exists(cls.DOCUMENTS_PATH):
            try:
                os.makedirs(cls.DOCUMENTS_PATH)
                print(f"Dokümanlar klasörü oluşturuldu: {cls.DOCUMENTS_PATH}")
            except Exception as e:
                errors.append(f"Dokümanlar klasörü oluşturulamadı: {str(e)}")

        if warnings:
            for warning in warnings:
                print(f"⚠️  WARNING: {warning}")

        if errors:
            raise ValueError("\n".join(errors))

        return True

    @classmethod
    def get_info(cls):
        """Konfigürasyon bilgilerini yazdır (hassas bilgiler gizli)"""
        info = {
            "Flask": {
                "DEBUG": cls.DEBUG,
                "HOST": cls.HOST,
                "PORT": cls.PORT,
            },
            "Database": {
                "SERVER": cls.DB_SERVER,
                "DATABASE": cls.DB_NAME,
                "USERNAME": cls.DB_USERNAME,
                "PASSWORD": "***" if cls.DB_PASSWORD else "YOK",
            },
            "OpenAI": {
                "MODEL": cls.OPENAI_MODEL,
                "API_KEY": "***" if cls.OPENAI_API_KEY else "YOK",
                "TEMPERATURE": cls.OPENAI_TEMPERATURE,
                "MAX_TOKENS": cls.OPENAI_MAX_TOKENS,
            },
            "Documents": {
                "PATH": cls.DOCUMENTS_PATH,
                "SEARCH_ENABLED": cls.ENABLE_DOCUMENT_SEARCH,
            },
            "Chatbot": {
                "MAX_HISTORY": cls.MAX_HISTORY_LENGTH,
                "SP_SEARCH": cls.ENABLE_SP_SEARCH,
            }
        }
        return info


# Test fonksiyonu
if __name__ == "__main__":
    print("=" * 50)
    print("CHATBOT KONFİGÜRASYON BİLGİLERİ")
    print("=" * 50)

    try:
        Config.validate()
        print("\n✓ Konfigürasyon doğrulandı!")

        import json
        print("\n" + json.dumps(Config.get_info(), indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n✗ Hata: {str(e)}")
