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

    def create_token(self, kullanici_id: int, kullanici_adi: str) -> str:
        """
        JWT token oluşturur

        Args:
            kullanici_id: Kullanıcı ID
            kullanici_adi: Kullanıcı adı

        Returns:
            JWT token
        """
        try:
            payload = {
                'kullanici_id': kullanici_id,
                'kullanici_adi': kullanici_adi,
                'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
                'iat': datetime.utcnow()
            }

            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            logger.info(f"Token oluşturuldu: {kullanici_adi}")
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

    def login(self, kullanici_adi: str, password: str) -> Dict[str, Any]:
        """
        Kullanıcı girişi yapar

        Args:
            kullanici_adi: Kullanıcı adı
            password: Şifre

        Returns:
            Giriş sonucu (başarılı ise token içerir)
        """
        try:
            # Kullanıcıyı veritabanından al
            kullanici = self.db.get_kullanici_by_username(kullanici_adi)

            if not kullanici:
                logger.warning(f"Kullanıcı bulunamadı: {kullanici_adi}")
                self.db.add_islem_log(
                    None,
                    'Başarısız Giriş',
                    f'Kullanıcı bulunamadı: {kullanici_adi}',
                    hata_mi=True
                )
                return {
                    'success': False,
                    'message': 'Kullanıcı adı veya şifre hatalı'
                }

            # Şifreyi doğrula
            if not self.verify_password(password, kullanici['SifreHash']):
                logger.warning(f"Yanlış şifre: {kullanici_adi}")
                self.db.add_islem_log(
                    kullanici['Id'],
                    'Başarısız Giriş',
                    'Yanlış şifre',
                    hata_mi=True
                )
                return {
                    'success': False,
                    'message': 'Kullanıcı adı veya şifre hatalı'
                }

            # Kullanıcı aktif mi kontrol et
            if not kullanici.get('AktifMi'):
                logger.warning(f"Pasif kullanıcı giriş denemesi: {kullanici_adi}")
                self.db.add_islem_log(
                    kullanici['Id'],
                    'Başarısız Giriş',
                    'Pasif kullanıcı',
                    hata_mi=True
                )
                return {
                    'success': False,
                    'message': 'Kullanıcı hesabı aktif değil'
                }

            # Token oluştur
            token = self.create_token(kullanici['Id'], kullanici['KullaniciAdi'])

            # Başarılı giriş logu
            self.db.add_islem_log(
                kullanici['Id'],
                'Başarılı Giriş',
                f"Kullanıcı: {kullanici_adi}"
            )

            logger.info(f"Başarılı giriş: {kullanici_adi}")

            return {
                'success': True,
                'message': 'Giriş başarılı',
                'token': token,
                'kullanici': {
                    'id': kullanici['Id'],
                    'kullanici_adi': kullanici['KullaniciAdi'],
                    'eposta': kullanici['Eposta']
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
        Yeni kullanıcı kaydı

        Args:
            kullanici_adi: Kullanıcı adı
            password: Şifre
            eposta: E-posta

        Returns:
            Kayıt sonucu
        """
        try:
            # Kullanıcı adı kontrolü
            existing_user = self.db.get_kullanici_by_username(kullanici_adi)
            if existing_user:
                return {
                    'success': False,
                    'message': 'Bu kullanıcı adı zaten kullanılıyor'
                }

            # Şifreyi hash'le
            hashed_password = self.hash_password(password)

            # Veritabanına ekle
            query = """
                INSERT INTO KULLANICILAR (KullaniciAdi, SifreHash, Eposta, KayitTarihi, AktifMi)
                VALUES (?, ?, ?, GETDATE(), 1)
            """
            self.db.execute_non_query(query, (kullanici_adi, hashed_password, eposta))

            # Yeni kullanıcıyı al
            new_user = self.db.get_kullanici_by_username(kullanici_adi)

            # Log ekle
            self.db.add_islem_log(
                new_user['Id'],
                'Kullanıcı Kaydı',
                f"Yeni kullanıcı: {kullanici_adi}"
            )

            logger.info(f"Yeni kullanıcı kaydedildi: {kullanici_adi}")

            return {
                'success': True,
                'message': 'Kayıt başarılı',
                'kullanici': {
                    'id': new_user['Id'],
                    'kullanici_adi': new_user['KullaniciAdi'],
                    'eposta': new_user['Eposta']
                }
            }

        except Exception as e:
            logger.error(f"Kayıt hatası: {str(e)}")
            return {
                'success': False,
                'message': 'Bir hata oluştu, lütfen tekrar deneyin'
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
            current_user = db.get_kullanici_by_id(payload['kullanici_id'])

            if not current_user:
                return jsonify({'message': 'Kullanıcı bulunamadı'}), 401

        except Exception as e:
            logger.error(f"Token doğrulama hatası: {str(e)}")
            return jsonify({'message': 'Token doğrulanamadı'}), 401

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
