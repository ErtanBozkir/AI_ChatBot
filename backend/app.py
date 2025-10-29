"""
Ana Flask Uygulaması
API Endpoints ve Route'lar
"""

import os
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime

# Backend modüllerini import et
from config import Config
from database import DatabaseManager
from auth import AuthManager, token_required
from chatbot import ChatBot
from document_reader import DocumentReader

# Logging ayarları
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask uygulaması
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = Config.SECRET_KEY

# CORS ayarları
CORS(app, origins=Config.CORS_ORIGINS)

# Modülleri başlat
db = DatabaseManager()
auth = AuthManager()
chatbot = ChatBot()
doc_reader = DocumentReader()


# ============================================
# SAĞLIK KONTROL ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    """Sistem sağlık kontrolü"""
    try:
        db_status = db.test_connection()

        return jsonify({
            'status': 'healthy' if db_status else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected' if db_status else 'disconnected',
            'version': '1.0.0'
        }), 200 if db_status else 503

    except Exception as e:
        logger.error(f"Sağlık kontrolü hatası: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@app.route('/config', methods=['GET'])
def get_config():
    """Konfigürasyon bilgilerini döndürür"""
    return jsonify(Config.get_info()), 200


# ============================================
# KİMLİK DOĞRULAMA ENDPOINTS
# ============================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Kullanıcı kaydı"""
    try:
        data = request.get_json()

        kullanici_adi = data.get('kullanici_adi')
        password = data.get('password')
        eposta = data.get('eposta')

        if not all([kullanici_adi, password, eposta]):
            return jsonify({
                'success': False,
                'message': 'Tüm alanlar zorunludur'
            }), 400

        result = auth.register(kullanici_adi, password, eposta)

        return jsonify(result), 201 if result['success'] else 400

    except Exception as e:
        logger.error(f"Kayıt hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Kullanıcı girişi"""
    try:
        data = request.get_json()

        kullanici_adi = data.get('kullanici_adi')
        password = data.get('password')

        if not all([kullanici_adi, password]):
            return jsonify({
                'success': False,
                'message': 'Kullanıcı adı ve şifre zorunludur'
            }), 400

        result = auth.login(kullanici_adi, password)

        return jsonify(result), 200 if result['success'] else 401

    except Exception as e:
        logger.error(f"Giriş hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """Token doğrulama"""
    return jsonify({
        'success': True,
        'kullanici': {
            'id': current_user['Id'],
            'kullanici_adi': current_user['KullaniciAdi'],
            'eposta': current_user['Eposta']
        }
    }), 200


# ============================================
# CHATBOT ENDPOINTS
# ============================================

@app.route('/api/chat/ask', methods=['POST'])
@token_required
def ask_question(current_user):
    """Chatbot'a soru sor"""
    try:
        data = request.get_json()
        soru = data.get('soru')

        if not soru:
            return jsonify({
                'success': False,
                'message': 'Soru zorunludur'
            }), 400

        kullanici_id = current_user['Id']

        # Sohbet geçmişini al (opsiyonel)
        sohbet_gecmisi = chatbot.get_sohbet_gecmisi(kullanici_id, limit=5)

        # Cevabı al
        result = chatbot.get_answer(kullanici_id, soru, sohbet_gecmisi)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Soru cevap hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


@app.route('/api/chat/history', methods=['GET'])
@token_required
def get_chat_history(current_user):
    """Sohbet geçmişini getir"""
    try:
        kullanici_id = current_user['Id']
        limit = request.args.get('limit', 50, type=int)

        history = chatbot.get_sohbet_gecmisi(kullanici_id, limit)

        # Datetime objelerini string'e çevir
        for item in history:
            if 'Tarih' in item and isinstance(item['Tarih'], datetime):
                item['Tarih'] = item['Tarih'].isoformat()

        return jsonify({
            'success': True,
            'history': history
        }), 200

    except Exception as e:
        logger.error(f"Geçmiş getirme hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


@app.route('/api/chat/clear', methods=['DELETE'])
@token_required
def clear_chat_history(current_user):
    """Sohbet geçmişini temizle"""
    try:
        kullanici_id = current_user['Id']
        success = chatbot.clear_sohbet_gecmisi(kullanici_id)

        return jsonify({
            'success': success,
            'message': 'Sohbet geçmişi temizlendi' if success else 'Bir hata oluştu'
        }), 200 if success else 500

    except Exception as e:
        logger.error(f"Geçmiş temizleme hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


# ============================================
# DOKÜMAN ENDPOINTS
# ============================================

@app.route('/api/documents', methods=['GET'])
@token_required
def get_documents(current_user):
    """Doküman listesini getir"""
    try:
        documents = doc_reader.get_all_documents()

        return jsonify({
            'success': True,
            'documents': documents
        }), 200

    except Exception as e:
        logger.error(f"Doküman listeleme hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


@app.route('/api/documents/search', methods=['POST'])
@token_required
def search_documents(current_user):
    """Dokümanlarda arama yap"""
    try:
        data = request.get_json()
        query = data.get('query')

        if not query:
            return jsonify({
                'success': False,
                'message': 'Arama sorgusu zorunludur'
            }), 400

        results = doc_reader.search_in_documents(query, max_results=10)

        return jsonify({
            'success': True,
            'results': results
        }), 200

    except Exception as e:
        logger.error(f"Doküman arama hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


# ============================================
# YÖNETİM ENDPOINTS
# ============================================

@app.route('/api/admin/soru-turleri', methods=['GET'])
@token_required
def get_soru_turleri(current_user):
    """Soru türlerini listele"""
    try:
        soru_turleri = db.get_soru_turleri()

        # Datetime objelerini string'e çevir
        for item in soru_turleri:
            if 'OlusturmaTarihi' in item and isinstance(item['OlusturmaTarihi'], datetime):
                item['OlusturmaTarihi'] = item['OlusturmaTarihi'].isoformat()

        return jsonify({
            'success': True,
            'soru_turleri': soru_turleri
        }), 200

    except Exception as e:
        logger.error(f"Soru türleri getirme hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


@app.route('/api/admin/soru-eslesmeleri', methods=['GET'])
@token_required
def get_soru_eslesmeleri(current_user):
    """Soru eşleştirmelerini listele"""
    try:
        soru_tur_id = request.args.get('soru_tur_id', type=int)
        eslesme = db.get_soru_eslesmeleri(soru_tur_id)

        return jsonify({
            'success': True,
            'eslesme': eslesme
        }), 200

    except Exception as e:
        logger.error(f"Soru eşleşmeleri getirme hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


# ============================================
# FRONTEND ROUTES
# ============================================

@app.route('/')
def index():
    """Ana sayfa"""
    return send_from_directory('../frontend', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Statik dosyaları servis et"""
    return send_from_directory('../frontend', path)


# ============================================
# HATA YAKALAMA
# ============================================

@app.errorhandler(404)
def not_found(error):
    """404 hatası"""
    return jsonify({
        'success': False,
        'message': 'Endpoint bulunamadı'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500 hatası"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'message': 'Sunucu hatası'
    }), 500


# ============================================
# UYGULAMA BAŞLATMA
# ============================================

def initialize_app():
    """Uygulama başlatma kontrolü"""
    try:
        logger.info("Chatbot uygulaması başlatılıyor...")

        # Konfigürasyonu doğrula
        Config.validate()
        logger.info("✓ Konfigürasyon doğrulandı")

        # Veritabanı bağlantısını test et
        if db.test_connection():
            logger.info("✓ Veritabanı bağlantısı başarılı")
        else:
            logger.error("✗ Veritabanı bağlantısı başarısız!")
            return False

        # OpenAI API key kontrolü
        if Config.OPENAI_API_KEY:
            logger.info("✓ OpenAI API key bulundu")
        else:
            logger.warning("! OpenAI API key bulunamadı - ChatGPT özellikleri çalışmayacak")

        logger.info("✓ Chatbot uygulaması başarıyla başlatıldı")
        return True

    except Exception as e:
        logger.error(f"Başlatma hatası: {str(e)}")
        return False


if __name__ == '__main__':
    # Uygulamayı başlat
    if initialize_app():
        logger.info(f"Flask sunucusu başlatılıyor: http://{Config.HOST}:{Config.PORT}")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    else:
        logger.error("Uygulama başlatılamadı!")
        sys.exit(1)
