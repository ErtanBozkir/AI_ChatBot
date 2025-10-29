"""
Kimlik Doğrulama ve Yetkilendirme Modülü
Kullanıcı giriş, şifre hash, JWT token yönetimi
"""

import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify
from config import Config
from database import DatabaseManager

# Logging ayarları
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class AuthManager:
    """Kimlik doğrulama yönetim sınıfı"""

    def __init__(self):
        self.db = DatabaseManager()
        self.jwt_secret = Config.JWT_SECRET_KEY
        self.jwt_algorithm = Config.JWT_ALGORITHM
        self.jwt_expiration_hours = Config.JWT_EXPIRATION_HOURS

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Şifreyi bcrypt ile hash'ler

        Args:
            password: Düz metin şifre

        Returns:
            Hash'lenmiş şifre
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Şifreyi hash ile doğrular

        Args:
            password: Düz metin şifre
            hashed: Hash'lenmiş şifre

        Returns:
            Doğruysa True
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Şifre doğrulama hatası: {str(e)}")
            return False

    def create_token(self, tc_kimlik_no: str, ad_soyad: str = None) -> str:
        """
        JWT token oluşturur ve SESSIONS tablosuna kaydeder

        Args:
            tc_kimlik_no: TC Kimlik No
            ad_soyad: Ad Soyad (opsiyonel)

        Returns:
            JWT token
        """
        try:
            payload = {
                'tc_kimlik_no': tc_kimlik_no,
                'ad_soyad': ad_soyad,
                'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
                'iat': datetime.utcnow()
            }

            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

            # Token'ı SESSIONS tablosuna kaydet
            expiration_date = datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
            query = """
                INSERT INTO SESSIONS (TcKimlikNo, Token, OlusturmaTarihi, SonKullanim, AktifMi)
                VALUES (?, ?, GETDATE(), ?, 1)
            """
            self.db.execute_non_query(query, (tc_kimlik_no, token, expiration_date))

            logger.info(f"Token oluşturuldu: {tc_kimlik_no}")
            return token

        except Exception as e:
            logger.error(f"Token oluşturma hatası: {str(e)}")
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        JWT token'ı doğrular

        Args:
            token: JWT token

        Returns:
            Token payload veya None
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            logger.debug(f"Token doğrulandı: {payload.get('kullanici_adi')}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token süresi dolmuş")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Geçersiz token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token doğrulama hatası: {str(e)}")
            return None

    def login(self, tc_kimlik_no: str, password: str) -> Dict[str, Any]:
        """
        Kullanıcı girişi yapar (KNS_IK.dbo.Calisan tablosu üzerinden)

        Args:
            tc_kimlik_no: TC Kimlik No
            password: Şifre

        Returns:
            Giriş sonucu (başarılı ise token içerir)
        """
        try:
            # SP_KullaniciGiris stored procedure'ünü çağır
            basarili = self.db.call_sp_kullanici_giris(tc_kimlik_no, password)

            if not basarili:
                logger.warning(f"Başarısız giriş denemesi: {tc_kimlik_no}")
                self.db.add_islem_log(
                    tc_kimlik_no,
                    'Başarısız Giriş',
                    f'TC: {tc_kimlik_no}',
                    hata_mi=True
                )
                return {
                    'success': False,
                    'message': 'TC Kimlik No veya şifre hatalı'
                }

            # Kullanıcı bilgilerini al
            calisan = self.db.get_calisan_by_tc(tc_kimlik_no)

            if not calisan:
                logger.error(f"Giriş başarılı ama çalışan bulunamadı: {tc_kimlik_no}")
                return {
                    'success': False,
                    'message': 'Bir hata oluştu, lütfen tekrar deneyin'
                }

            # Token oluştur
            token = self.create_token(tc_kimlik_no, calisan.get('AdSoyad'))

            # Başarılı giriş logu
            self.db.add_islem_log(
                tc_kimlik_no,
                'Başarılı Giriş',
                f"TC: {tc_kimlik_no}"
            )

            logger.info(f"Başarılı giriş: {tc_kimlik_no}")

            return {
                'success': True,
                'message': 'Giriş başarılı',
                'token': token,
                'kullanici': {
                    'tc_kimlik_no': calisan['TcKimlikNo'],
                    'ad_soyad': calisan.get('AdSoyad'),
                    'eposta': calisan.get('Eposta'),
                    'departman': calisan.get('Departman'),
                    'AdminMi': calisan.get('AdminMi', False)
                }
            }

        except Exception as e:
            logger.error(f"Giriş hatası: {str(e)}")
            return {
                'success': False,
                'message': 'Bir hata oluştu, lütfen tekrar deneyin'
            }

    def register(self, kullanici_adi: str, password: str, eposta: str) -> Dict[str, Any]:
        """
        Yeni kullanıcı kaydı - DEVRE DIŞI
        (Çalışanlar KNS_IK.dbo.Calisan tablosunda tanımlıdır)

        Args:
            kullanici_adi: Kullanıcı adı
            password: Şifre
            eposta: E-posta

        Returns:
            Kayıt sonucu
        """
        logger.warning("Register fonksiyonu devre dışı bırakıldı")
        return {
            'success': False,
            'message': 'Kullanıcı kaydı yapılamıyor. Lütfen İnsan Kaynakları departmanı ile iletişime geçin.'
        }


def token_required(f):
    """
    Flask route decorator - Token doğrulaması gerektirir

    Kullanım:
        @app.route('/protected')
        @token_required
        def protected_route(current_user):
            return jsonify({'message': 'Success'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Token'ı header'dan al
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # "Bearer TOKEN" formatı
            except IndexError:
                return jsonify({'message': 'Token formatı hatalı'}), 401

        if not token:
            return jsonify({'message': 'Token bulunamadı'}), 401

        try:
            # Token'ı doğrula
            auth = AuthManager()
            payload = auth.verify_token(token)

            if not payload:
                return jsonify({'message': 'Geçersiz veya süresi dolmuş token'}), 401

            # Kullanıcı bilgilerini al
            db = DatabaseManager()
            current_user = db.get_calisan_by_tc(payload['tc_kimlik_no'])

            if not current_user:
                return jsonify({'message': 'Kullanıcı bulunamadı'}), 401

        except Exception as e:
            logger.error(f"Token doğrulama hatası: {str(e)}")
            return jsonify({'message': 'Token doğrulanamadı'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


def admin_required(f):
    """
    Flask route decorator - Admin yetkisi gerektirir

    Kullanım:
        @app.route('/admin')
        @admin_required
        def admin_route(current_user):
            return jsonify({'message': 'Admin panel'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Token'ı header'dan al
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token formatı hatalı'}), 401

        if not token:
            return jsonify({'message': 'Token bulunamadı'}), 401

        try:
            # Token'ı doğrula
            auth = AuthManager()
            payload = auth.verify_token(token)

            if not payload:
                return jsonify({'message': 'Geçersiz veya süresi dolmuş token'}), 401

            # Kullanıcı bilgilerini al
            db = DatabaseManager()
            current_user = db.get_calisan_by_tc(payload['tc_kimlik_no'])

            if not current_user:
                return jsonify({'message': 'Kullanıcı bulunamadı'}), 401

            # Admin kontrolü
            is_admin = current_user.get('AdminMi', False) or current_user.get('Admin', False)
            if not is_admin:
                logger.warning(f"Admin yetkisi olmayan erişim denemesi: {payload['tc_kimlik_no']}")
                return jsonify({
                    'success': False,
                    'message': 'Bu sayfaya erişim yetkiniz bulunmamaktadır'
                }), 403

        except Exception as e:
            logger.error(f"Admin kontrolü hatası: {str(e)}")
            return jsonify({'message': 'Yetkilendirme hatası'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# Test fonksiyonu
if __name__ == "__main__":
    print("=" * 50)
    print("AUTH MODÜLÜ TESTİ")
    print("=" * 50)

    auth = AuthManager()

    # Şifre hash testi
    password = "12345"
    hashed = auth.hash_password(password)
    print(f"\nŞifre: {password}")
    print(f"Hash: {hashed}")
    print(f"Doğrulama: {auth.verify_password(password, hashed)}")

    # Token testi
    token = auth.create_token(1, "test_user")
    print(f"\nToken: {token}")
    payload = auth.verify_token(token)
    print(f"Payload: {payload}")
