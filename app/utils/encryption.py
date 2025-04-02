import logging
from typing import Optional

from jose import JOSEError, jwe
from jose.constants import ALGORITHMS

from app.core.config import settings


class TokenEncryption:
    """Xử lý mã hóa và giải mã tokens để bảo mật khi lưu trữ"""

    @staticmethod
    def encrypt_token(token_data: str) -> Optional[str]:
        """
        Mã hóa token data để lưu trữ an toàn

        Args:
            token_data: Token data dưới dạng chuỗi (thường là JSON string)

        Returns:
            Chuỗi đã mã hóa, hoặc None nếu có lỗi
        """
        if not token_data:
            return None

        try:
            encrypted = jwe.encrypt(
                token_data,
                settings.SECRET_KEY,
                algorithm=ALGORITHMS.DIR,
                encryption=ALGORITHMS.A256GCM,
            )
            return encrypted
        except Exception as e:
            logging.error(f"Token encryption error: {str(e)}")
            return None

    @staticmethod
    def decrypt_token(encrypted_data: str) -> Optional[str]:
        """
        Giải mã token data từ chuỗi đã mã hóa

        Args:
            encrypted_data: Chuỗi đã mã hóa

        Returns:
            Token data gốc, hoặc None nếu có lỗi
        """
        if not encrypted_data:
            return None

        try:
            decrypted = jwe.decrypt(
                encrypted_data,
                settings.SECRET_KEY,
            )
            return decrypted.decode("utf-8")
        except JOSEError as e:
            logging.error(f"Token decryption error (JOSE): {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Token decryption error: {str(e)}")
            return None
