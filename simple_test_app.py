"""
Basitleştirilmiş Test Flask Uygulaması
SQLite, basit auth, mock ChatGPT
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from contextlib import contextmanager

# Konfigürasyon
class TestConfig:
    SECRET_KEY = secrets.token_hex(16)
    DATABASE = 'test_chatbot.db'
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000

# Flask app
app = Flask(__name__, static_folder='frontend', static_url_path='')
app.config.from_object(TestConfig)
CORS(app, origins=['*'], supports_credentials=True)

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

# Simple password hash (sha256 for simplicity)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# Mock ChatGPT Responses
MOCK_RESPONSES = {
    'IZIN_HAKKI_SORGULA': 'İzin hakkınız toplamda 15 gündür. Bu yıl 5 gün kullandınız, kalan: 10 gün. İyi tatiller! 🌴',
    'MAAS_BORDRO_SORGULA': 'Maaşlar her ayın 28\'inde hesaplara yatmaktadır. Bordronuzu İK portalından indirebilirsiniz. 💰',
    'ZIMMET_SORGULA': 'Zimmetinizde kayıtlı ekipmanlar:\n• 1 Laptop (Dell XPS 15)\n• 1 Telefon (iPhone 13)\n\nDetaylı bilgi için BT departmanı: dahili 1234 📱',
    'EGITIM_TALEP': 'Eğitim talebiniz için İnsan Kaynakları departmanına başvurabilirsiniz.\n\n📧 E-posta: egitim@firma.com\n📞 Dahili: 5678',
    'GENEL': 'Size yardımcı olmaya çalışıyorum. Sorunuzu biraz daha detaylandırır mısınız? 🤔'
}

def mock_chatgpt_response(soru, soru_tur_kod=None):
    """Mock ChatGPT yanıtı"""
    if soru_tur_kod and soru_tur_kod in MOCK_RESPONSES:
        return MOCK_RESPONSES[soru_tur_kod]

    soru_lower = soru.lower()
    if 'izin' in soru_lower or 'tatil' in soru_lower:
        return MOCK_RESPONSES['IZIN_HAKKI_SORGULA']
    elif 'maaş' in soru_lower or 'bordro' in soru_lower or 'ücret' in soru_lower:
        return MOCK_RESPONSES['MAAS_BORDRO_SORGULA']
    elif 'zimmet' in soru_lower or 'ekipman' in soru_lower:
        return MOCK_RESPONSES['ZIMMET_SORGULA']
    elif 'eğitim' in soru_lower or 'kurs' in soru_lower:
        return MOCK_RESPONSES['EGITIM_TALEP']
    elif 'merhaba' in soru_lower or 'selam' in soru_lower or 'hello' in soru_lower:
        return f"Merhaba! Ben KNS Otomotiv Dijital asistanınızım. Size nasıl yardımcı olabilirim? 👋"
    elif 'teşekkür' in soru_lower or 'sağol' in soru_lower:
        return "Rica ederim! Başka bir sorunuz olursa yardımcı olmaktan mutluluk duyarım. 😊"
    else:
        return f"'{soru}' konusunda size yardımcı olmak isterim. İlgili departmana yönlendirebilirim veya daha fazla bilgi verebilirim. Ne yapmamı istersiniz?"

# Auth Helper
def login_required(f):
    """Login decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check token in header
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return jsonify({'message': 'Token bulunamadı'}), 401

        # Simple token format: "user_id:timestamp:hash"
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return jsonify({'message': 'Geçersiz token'}), 401

            user_id = int(parts[0])

            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM KULLANICILAR WHERE Id = ?", (user_id,))
                current_user = cursor.fetchone()

            if not current_user:
                return jsonify({'message': 'Kullanıcı bulunamadı'}), 401

            return f(dict(current_user), *args, **kwargs)
        except:
            return jsonify({'message': 'Token doğrulanamadı'}), 401

    return decorated

def create_simple_token(user_id):
    """Basit token oluştur"""
    timestamp = str(int(datetime.now().timestamp()))
    data = f"{user_id}:{timestamp}"
    hash_val = hashlib.sha256(data.encode()).hexdigest()[:16]
    return f"{user_id}:{timestamp}:{hash_val}"

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'mode': 'TEST MODE',
        'database': 'SQLite',
        'chatgpt': 'Mock (OpenAI API gerektirmez)'
    }), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    kullanici_adi = data.get('kullanici_adi')
    password = data.get('password')

    # Simple hash check (not bcrypt for compatibility)
    password_hash = hash_password(password)

    with get_db() as conn:
        cursor = conn.cursor()
        # Try both hashed formats
        cursor.execute("""
            SELECT * FROM KULLANICILAR
            WHERE KullaniciAdi = ?
            AND AktifMi = 1
        """, (kullanici_adi,))
        user = cursor.fetchone()

    if not user:
        return jsonify({'success': False, 'message': 'Kullanıcı bulunamadı'}), 401

    # For test: accept "12345" as password
    if password != "12345":
        return jsonify({'success': False, 'message': 'Şifre hatalı'}), 401

    token = create_simple_token(user['Id'])

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

    hashed = hash_password(password)

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO KULLANICILAR (KullaniciAdi, SifreHash, Eposta, KayitTarihi, AktifMi)
                VALUES (?, ?, ?, ?, 1)
            """, (kullanici_adi, hashed, eposta, datetime.now().isoformat()))
            conn.commit()

        return jsonify({'success': True, 'message': 'Kayıt başarılı! Şifreniz: ' + password}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': 'Kullanıcı adı zaten kullanılıyor'}), 400

@app.route('/api/chat/ask', methods=['POST'])
@login_required
def ask_question(current_user):
    data = request.get_json()
    soru = data.get('soru', '').strip()

    if not soru:
        return jsonify({'success': False, 'message': 'Soru boş olamaz'}), 400

    # Soru türü eşleştir
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ST.Id, ST.Kod
            FROM SORU_ESLESMELERI SE
            JOIN SORU_TURLERI ST ON SE.SoruTurId = ST.Id
            WHERE ? LIKE '%' || SE.OrnekSoru || '%'
            ORDER BY LENGTH(SE.OrnekSoru) DESC
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
        'kaynak': f'Test AI ({soru_tur_kod})',
        'soru_tur_kod': soru_tur_kod
    }), 200

@app.route('/api/chat/history', methods=['GET'])
@login_required
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

@app.route('/api/chat/clear', methods=['DELETE'])
@login_required
def clear_history(current_user):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM SOHBETLER WHERE KullaniciId = ?", (current_user['Id'],))
        conn.commit()

    return jsonify({'success': True, 'message': 'Geçmiş temizlendi'}), 200

@app.route('/api/documents', methods=['GET'])
@login_required
def get_documents(current_user):
    return jsonify({
        'success': True,
        'documents': [
            {'name': 'demo_izin_politikasi.pdf', 'size': 1024, 'extension': '.pdf', 'path': '/documents/demo1.pdf'},
            {'name': 'calisan_el_kitabi.docx', 'size': 2048, 'extension': '.docx', 'path': '/documents/demo2.docx'},
            {'name': 'maas_cetveli.xlsx', 'size': 4096, 'extension': '.xlsx', 'path': '/documents/demo3.xlsx'},
        ]
    }), 200

@app.route('/api/admin/soru-turleri', methods=['GET'])
@login_required
def get_soru_turleri(current_user):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SORU_TURLERI WHERE AktifMi = 1 ORDER BY Kod")
        turleri = [dict(row) for row in cursor.fetchall()]

    return jsonify({'success': True, 'soru_turleri': turleri}), 200

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Endpoint bulunamadı'}), 404

if __name__ == '__main__':
    if not os.path.exists(TestConfig.DATABASE):
        print("\n❌ Test veritabanı bulunamadı!")
        print("Lütfen önce şunu çalıştırın: python test_setup.py\n")
    else:
        print("\n" + "="*70)
        print("🚀 KNS OTOMOTIV TEST SUNUCUSU BAŞLATILIYOR")
        print("="*70)
        print("\n📌 Test Ortamı Bilgileri:")
        print(f"   🌐 URL: http://localhost:{TestConfig.PORT}")
        print(f"   👤 Test Kullanıcısı: ahmet.yilmaz")
        print(f"   🔑 Şifre: 12345")
        print(f"   💾 Veritabanı: SQLite (test_chatbot.db)")
        print(f"   🤖 ChatGPT: Mock yanıtlar (gerçek API gerektirmez)")
        print("\n✅ Özellikler:")
        print("   • Kullanıcı girişi ve kaydı")
        print("   • Akıllı soru-cevap sistemi")
        print("   • Sohbet geçmişi")
        print("   • Soru türü eşleştirme")
        print("   • Mock AI yanıtları")
        print("\n💡 İpucu: Tarayıcınızda yukarıdaki URL'yi açın!")
        print("="*70 + "\n")

        app.run(host=TestConfig.HOST, port=TestConfig.PORT, debug=False, use_reloader=False)
