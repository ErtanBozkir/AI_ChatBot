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
from auth import AuthManager, token_required, admin_required
from chatbot import ChatBot
from document_reader import DocumentReader

# RAG modülleri
from document_processor import DocumentProcessor
from vector_store import VectorStoreManager
from rag_engine import RAGEngine

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

# RAG modülleri
doc_processor = DocumentProcessor()
vector_store = VectorStoreManager()
rag_engine = RAGEngine()


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

        tc_kimlik_no = data.get('tc_kimlik_no') or data.get('kullanici_adi')  # Backward compatibility
        password = data.get('password')

        if not all([tc_kimlik_no, password]):
            return jsonify({
                'success': False,
                'message': 'TC Kimlik No ve şifre zorunludur'
            }), 400

        result = auth.login(tc_kimlik_no, password)

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
            'tc_kimlik_no': current_user['TcKimlikNo'],
            'ad_soyad': current_user.get('AdSoyad'),
            'eposta': current_user.get('Eposta'),
            'departman': current_user.get('Departman')
        }
    }), 200


# ============================================
# CHATBOT ENDPOINTS
# ============================================

@app.route('/api/chat/ask', methods=['POST'])
@token_required
def ask_question(current_user):
    """Chatbot'a soru sor - RAG + SQL Hybrid"""
    try:
        data = request.get_json()
        soru = data.get('soru')
        session_id = data.get('session_id')

        if not soru:
            return jsonify({
                'success': False,
                'message': 'Soru zorunludur'
            }), 400

        tc_kimlik_no = current_user['TcKimlikNo']

        # Akıllı Routing: SQL mi Doküman mı?
        use_documents = rag_engine.should_use_documents(soru)

        if use_documents:
            # Dokümanlardan cevapla (RAG)
            result = rag_engine.answer_from_documents(soru, tc_kimlik_no, session_id)
        else:
            # SQL'den cevapla (mevcut sistem)
            if session_id:
                sohbet_gecmisi = db.get_sohbet_gecmisi_by_session(tc_kimlik_no, session_id, limit=5)
            else:
                sohbet_gecmisi = chatbot.get_sohbet_gecmisi(tc_kimlik_no, limit=5)

            result = chatbot.get_answer(tc_kimlik_no, soru, sohbet_gecmisi, session_id)

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
        tc_kimlik_no = current_user['TcKimlikNo']
        limit = request.args.get('limit', 50, type=int)

        history = chatbot.get_sohbet_gecmisi(tc_kimlik_no, limit)

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


@app.route('/api/chat/sessions', methods=['GET'])
@token_required
def get_sessions(current_user):
    """Sohbet session'larını listele"""
    try:
        tc_kimlik_no = current_user['TcKimlikNo']
        limit = request.args.get('limit', 20, type=int)

        sessions = db.get_sessions_list(tc_kimlik_no, limit)

        # Datetime objelerini string'e çevir
        for session in sessions:
            if 'IlkMesajTarihi' in session and isinstance(session['IlkMesajTarihi'], datetime):
                session['IlkMesajTarihi'] = session['IlkMesajTarihi'].isoformat()
            if 'SonMesajTarihi' in session and isinstance(session['SonMesajTarihi'], datetime):
                session['SonMesajTarihi'] = session['SonMesajTarihi'].isoformat()

        return jsonify({
            'success': True,
            'sessions': sessions
        }), 200

    except Exception as e:
        logger.error(f"Session listesi getirme hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


@app.route('/api/chat/sessions/<session_id>', methods=['GET'])
@token_required
def get_session_messages(current_user, session_id):
    """Belirli bir session'ın tüm mesajlarını getir"""
    try:
        tc_kimlik_no = current_user['TcKimlikNo']
        limit = request.args.get('limit', 100, type=int)

        messages = db.get_sohbet_gecmisi_by_session(tc_kimlik_no, session_id, limit)

        # Datetime objelerini string'e çevir ve ters çevir (kronolojik sıra)
        for msg in messages:
            if 'Tarih' in msg and isinstance(msg['Tarih'], datetime):
                msg['Tarih'] = msg['Tarih'].isoformat()

        # Mesajları kronolojik sıraya çevir (en eski önce)
        messages = list(reversed(messages))

        return jsonify({
            'success': True,
            'messages': messages,
            'session_id': session_id
        }), 200

    except Exception as e:
        logger.error(f"Session mesajları getirme hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Bir hata oluştu'
        }), 500


@app.route('/api/chat/clear', methods=['DELETE'])
@token_required
def clear_chat_history(current_user):
    """Sohbet geçmişini temizle"""
    try:
        tc_kimlik_no = current_user['TcKimlikNo']
        success = chatbot.clear_sohbet_gecmisi(tc_kimlik_no)

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


@app.route('/api/chat/feedback', methods=['POST'])
@token_required
def submit_feedback(current_user):
    """Kullanıcı geri bildirimi kaydet"""
    try:
        data = request.get_json()
        message = data.get('message')
        reaction = data.get('reaction')
        timestamp = data.get('timestamp')

        tc_kimlik_no = current_user['TcKimlikNo']

        # Feedback'i veritabanına kaydet
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO KULLANICI_FEEDBACK
                (TcKimlikNo, MesajOzet, Reaksiyon, FeedbackTarihi)
                VALUES (?, ?, ?, ?)
            """, (tc_kimlik_no, message, reaction, timestamp))
            conn.commit()

        logger.info(f"Feedback kaydedildi: {tc_kimlik_no} - {reaction}")

        return jsonify({
            'success': True,
            'message': 'Geri bildiriminiz kaydedildi'
        }), 200

    except Exception as e:
        logger.error(f"Feedback kaydetme hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Geri bildirim kaydedilemedi'
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
# DOKÜMAN YÖNETİMİ ENDPOINTS (ADMIN)
# ============================================

@app.route('/api/admin/upload-document', methods=['POST'])
@admin_required
def upload_document(current_user):
    """Doküman yükle ve işle (Admin only)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Dosya bulunamadı'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Dosya seçilmedi'}), 400

        # Dosya uzantısı kontrolü
        allowed_extensions = ['.pdf', '.docx', '.doc']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'message': f'Desteklenmeyen dosya tipi. İzin verilenler: {", ".join(allowed_extensions)}'}), 400

        # Dosyayı kaydet
        upload_dir = os.path.join(Config.DOCUMENTS_PATH, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)

        # Database'e kaydet - EXPLICIT COMMIT ile
        file_id = None
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO DOSYALAR (DosyaAdi, DosyaYolu, DosyaTipi, Boyut, YukleyenTcKimlikNo)
                OUTPUT INSERTED.DosyaId
                VALUES (?, ?, ?, ?, ?)
            """, (file.filename, file_path, file_ext, os.path.getsize(file_path), current_user['TcKimlikNo']))

            result = cursor.fetchone()
            if result:
                file_id = result[0]

            # COMMIT - Bu çok önemli! Chunk insert'ten önce commit edilmeli
            conn.commit()
            logger.info(f"Dosya database'e kaydedildi ve commit edildi: {file_id}")

        if not file_id:
            return jsonify({'success': False, 'message': 'Dosya kaydedilemedi'}), 500

        # Dokümanı işle (async olabilir ama şimdilik senkron)
        process_result = doc_processor.process_document(file_path, file_id)

        if not process_result['success']:
            return jsonify({'success': False, 'message': 'Dosya işlenemedi', 'error': process_result.get('error')}), 500

        # Embedding oluştur
        embed_result = vector_store.create_embeddings_for_chunks(file_id)

        return jsonify({
            'success': True,
            'message': 'Dosya başarıyla yüklendi ve işlendi',
            'file_id': file_id,
            'chunks': process_result.get('total_chunks', 0),
            'embedded': embed_result.get('embedded_count', 0)
        }), 200

    except Exception as e:
        logger.error(f"Dosya yükleme hatası: {str(e)}")
        return jsonify({'success': False, 'message': 'Bir hata oluştu'}), 500


@app.route('/api/admin/documents', methods=['GET'])
@admin_required
def list_documents_admin(current_user):
    """Tüm dokümanları listele (Admin only)"""
    try:
        query = """
            SELECT d.DosyaId, d.DosyaAdi, d.DosyaTipi, d.Boyut, d.YuklenmeTarihi,
                   d.IslenmeDurumu, d.ChunkSayisi, d.IslenmeHatasi, d.YukleyenTcKimlikNo
            FROM DOSYALAR d
            WHERE d.AktifMi = 1
            ORDER BY d.YuklenmeTarihi DESC
        """
        documents = db.execute_query(query)

        for doc in documents:
            if 'YuklenmeTarihi' in doc and isinstance(doc['YuklenmeTarihi'], datetime):
                doc['YuklenmeTarihi'] = doc['YuklenmeTarihi'].isoformat()

        return jsonify({'success': True, 'documents': documents}), 200

    except Exception as e:
        logger.error(f"Doküman listesi hatası: {str(e)}")
        return jsonify({'success': False, 'message': 'Bir hata oluştu'}), 500


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


@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def get_dashboard_stats(current_user):
    """Dashboard istatistiklerini getir (Sadece adminler)"""
    try:
        # Tüm istatistikleri topla
        usage_stats = db.get_usage_statistics()
        top_questions = db.get_top_questions(limit=10)
        questions_per_user = db.get_questions_per_user(limit=20)
        success_rate = db.get_success_rate()
        peak_times = db.get_peak_usage_times()

        # Datetime objelerini string'e çevir
        for item in top_questions:
            if 'SonSoruTarihi' in item and isinstance(item['SonSoruTarihi'], datetime):
                item['SonSoruTarihi'] = item['SonSoruTarihi'].isoformat()

        for item in questions_per_user:
            if 'SonSoruTarihi' in item and isinstance(item['SonSoruTarihi'], datetime):
                item['SonSoruTarihi'] = item['SonSoruTarihi'].isoformat()

        logger.info(f"Dashboard istatistikleri görüntülendi: {current_user['TcKimlikNo']}")

        return jsonify({
            'success': True,
            'statistics': {
                'usage': usage_stats,
                'top_questions': top_questions,
                'questions_per_user': questions_per_user,
                'success_rate': success_rate,
                'peak_times': peak_times
            }
        }), 200

    except Exception as e:
        logger.error(f"Dashboard istatistikleri hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'İstatistikler alınırken bir hata oluştu'
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
