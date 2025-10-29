"""
Test Flask Uygulaması
SQLite ve mock ChatGPT ile çalışır
"""

import os
import sqlite3
import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from contextlib import contextmanager

# Konfigürasyon
class TestConfig:
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret'
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    DATABASE = 'test_chatbot.db'
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000

# Flask app
app = Flask(__name__, static_folder='frontend', static_url_path='')
app.config.from_object(TestConfig)
CORS(app, origins=['*'])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Helper
@contextmanager
def get_db():
    """SQLite bağlantısı"""
    conn = sqlite3.connect(TestConfig.DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Mock ChatGPT Responses
MOCK_RESPONSES = {
    'IZIN_HAKKI_SORGULA': 'İzin hakkınız toplamda 15 gündür. Bu yıl 5 gün kullandınız, kalan: 10 gün. İyi tatiller!',
    'MAAS_BORDRO_SORGULA': 'Maaşlar her ayın 28\'inde hesaplara yatmaktadır. Bordronuzu İK portalından indirebilirsiniz.',
    'ZIMMET_SORGULA': 'Zimmetinizde kayıtlı ekipmanlar: 1 Laptop (Dell XPS 15), 1 Telefon (iPhone 13). Detaylı bilgi için BT departmanı: dahili 1234',
    'EGITIM_TALEP': 'Eğitim talebiniz için İnsan Kaynakları departmanına başvurabilirsiniz. E-posta: egitim@firma.com veya dahili: 5678',
    'GENEL': 'Size yardımcı olmaya çalışıyorum. Sorunuzu biraz daha detaylandırır mısınız?'
}

def mock_chatgpt_response(soru, soru_tur_kod=None):
    """Mock ChatGPT yanıtı"""
    if soru_tur_kod and soru_tur_kod in MOCK_RESPONSES:
        return MOCK_RESPONSES[soru_tur_kod]

    # Anahtar kelime bazlı yanıtlar
    soru_lower = soru.lower()
    if 'izin' in soru_lower or 'tatil' in soru_lower:
        return MOCK_RESPONSES['IZIN_HAKKI_SORGULA']
    elif 'maaş' in soru_lower or 'bordro' in soru_lower:
        return MOCK_RESPONSES['MAAS_BORDRO_SORGULA']
    elif 'zimmet' in soru_lower or 'ekipman' in soru_lower:
        return MOCK_RESPONSES['ZIMMET_SORGULA']
    elif 'eğitim' in soru_lower or 'kurs' in soru_lower:
        return MOCK_RESPONSES['EGITIM_TALEP']
    else:
        return f"Sorunuz '{soru}' ile ilgili size yardımcı olmaya çalışıyorum. Firma içi prosedürlerimize göre ilgili departmana yönlendirebilirim. Daha fazla detay verir misiniz?"

# Auth Helpers
def create_token(kullanici_id, kullanici_adi):
    """JWT token oluştur"""
    payload = {
        'kullanici_id': kullanici_id,
        'kullanici_adi': kullanici_adi,
        'exp': datetime.utcnow() + timedelta(hours=TestConfig.JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, TestConfig.JWT_SECRET_KEY, algorithm=TestConfig.JWT_ALGORITHM)

def verify_token(token):
    """JWT token doğrula"""
    try:
        return jwt.decode(token, TestConfig.JWT_SECRET_KEY, algorithms=[TestConfig.JWT_ALGORITHM])
    except:
        return None

def token_required(f):
    """Token decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except:
                return jsonify({'message': 'Token formatı hatalı'}), 401

        if not token:
            return jsonify({'message': 'Token bulunamadı'}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Geçersiz token'}), 401

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM KULLANICILAR WHERE Id = ?", (payload['kullanici_id'],))
            current_user = cursor.fetchone()

        if not current_user:
            return jsonify({'message': 'Kullanıcı bulunamadı'}), 401

        return f(dict(current_user), *args, **kwargs)
    return decorated

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'mode': 'TEST', 'database': 'SQLite'}), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    kullanici_adi = data.get('kullanici_adi')
    password = data.get('password')

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM KULLANICILAR WHERE KullaniciAdi = ?", (kullanici_adi,))
        user = cursor.fetchone()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['SifreHash'].encode('utf-8')):
        return jsonify({'success': False, 'message': 'Kullanıcı adı veya şifre hatalı'}), 401

    token = create_token(user['Id'], user['KullaniciAdi'])

    return jsonify({
        'success': True,
        'token': token,
        'kullanici': {
            'id': user['Id'],
            'kullanici_adi': user['KullaniciAdi'],
            'eposta': user['Eposta']
        }
    }), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    kullanici_adi = data.get('kullanici_adi')
    password = data.get('password')
    eposta = data.get('eposta')

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO KULLANICILAR (KullaniciAdi, SifreHash, Eposta, KayitTarihi, AktifMi)
                VALUES (?, ?, ?, ?, 1)
            """, (kullanici_adi, hashed, eposta, datetime.now().isoformat()))
            conn.commit()

        return jsonify({'success': True, 'message': 'Kayıt başarılı'}), 201
    except:
        return jsonify({'success': False, 'message': 'Bu kullanıcı adı zaten kullanılıyor'}), 400

@app.route('/api/chat/ask', methods=['POST'])
@token_required
def ask_question(current_user):
    data = request.get_json()
    soru = data.get('soru')

    # Soru türü eşleştir
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ST.Id, ST.Kod
            FROM SORU_ESLESMELERI SE
            JOIN SORU_TURLERI ST ON SE.SoruTurId = ST.Id
            WHERE ? LIKE '%' || SE.OrnekSoru || '%'
            LIMIT 1
        """, (soru.lower(),))
        result = cursor.fetchone()

        soru_tur_id = result['Id'] if result else None
        soru_tur_kod = result['Kod'] if result else 'GENEL'

        # Mock yanıt oluştur
        cevap = mock_chatgpt_response(soru, soru_tur_kod)

        # Kaydet
        cursor.execute("""
            INSERT INTO SOHBETLER (KullaniciId, Soru, Cevap, SoruTurId, Tarih, IslemSuresi)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (current_user['Id'], soru, cevap, soru_tur_id, datetime.now().isoformat(), 50))
        conn.commit()

    return jsonify({
        'success': True,
        'cevap': cevap,
        'kaynak': f'Mock ChatGPT ({soru_tur_kod})',
        'soru_tur_kod': soru_tur_kod
    }), 200

@app.route('/api/chat/history', methods=['GET'])
@token_required
def get_history(current_user):
    limit = request.args.get('limit', 50, type=int)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT S.*, ST.Kod AS SoruTuru
            FROM SOHBETLER S
            LEFT JOIN SORU_TURLERI ST ON S.SoruTurId = ST.Id
            WHERE S.KullaniciId = ?
            ORDER BY S.Tarih DESC
            LIMIT ?
        """, (current_user['Id'], limit))
        history = [dict(row) for row in cursor.fetchall()]

    return jsonify({'success': True, 'history': history}), 200

@app.route('/api/documents', methods=['GET'])
@token_required
def get_documents(current_user):
    return jsonify({
        'success': True,
        'documents': [
            {'name': 'demo_document.pdf', 'size': 1024, 'extension': '.pdf'},
            {'name': 'izin_politikasi.docx', 'size': 2048, 'extension': '.docx'},
        ]
    }), 200

@app.route('/api/admin/soru-turleri', methods=['GET'])
@token_required
def get_soru_turleri(current_user):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SORU_TURLERI WHERE AktifMi = 1")
        turleri = [dict(row) for row in cursor.fetchall()]

    return jsonify({'success': True, 'soru_turleri': turleri}), 200

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

if __name__ == '__main__':
    # Veritabanı kontrolü
    if not os.path.exists(TestConfig.DATABASE):
        print("\n❌ Test veritabanı bulunamadı!")
        print("Lütfen önce şunu çalıştırın: python test_setup.py\n")
    else:
        print("\n" + "="*60)
        print("🚀 FIRMA CHATBOT TEST SUNUCUSU")
        print("="*60)
        print("\n📌 Test Bilgileri:")
        print(f"   URL: http://{TestConfig.HOST}:{TestConfig.PORT}")
        print(f"   Kullanıcı: ahmet.yilmaz / Şifre: 12345")
        print(f"   Veritabanı: SQLite (test_chatbot.db)")
        print(f"   ChatGPT: Mock yanıtlar (OpenAI API gerektirmez)")
        print("\n🎯 Özellikler:")
        print("   ✓ Kullanıcı girişi")
        print("   ✓ Soru-cevap sistemi")
        print("   ✓ Sohbet geçmişi")
        print("   ✓ Mock ChatGPT yanıtları")
        print("\n" + "="*60 + "\n")

        app.run(host=TestConfig.HOST, port=TestConfig.PORT, debug=TestConfig.DEBUG)
