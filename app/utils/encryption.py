import base64
import logging
import re
from typing import Optional, Tuple

from jose import JOSEError, jwe
from jose.constants import ALGORITHMS

from app.core.config import settings


class TokenEncryption:
    """Xử lý mã hóa và giải mã tokens để bảo mật khi lưu trữ"""

    # Prefixes to identify encryption methods
    JWE_PREFIX = "JWE:"
    BASE64_PREFIX = "BASE64:"

    @staticmethod
    def encrypt_token(token_data: str) -> Optional[str]:
        """
        Mã hóa token data để lưu trữ an toàn sử dụng JWE

        Args:
            token_data: Token data dưới dạng chuỗi (thường là JSON string)

        Returns:
            Chuỗi đã mã hóa, hoặc None nếu có lỗi
        """
        if not token_data:
            logging.debug("encrypt_token: Empty token data, returning None")
            return None

        try:
            # Kiểm tra xem token đã mã hóa chưa
            if TokenEncryption.is_encrypted(token_data):
                logging.info(
                    "encrypt_token: Token appears to be already encrypted, skipping encryption"
                )
                return token_data

            # Get encryption key
            secret_key = TokenEncryption._get_properly_sized_key()

            logging.debug(
                f"encrypt_token: Attempting JWE encryption with algorithm={ALGORITHMS.DIR}, encryption={ALGORITHMS.A256GCM}"
            )
            logging.debug(
                f"encrypt_token: Secret key available: {bool(secret_key)}"
            )

            encrypted = jwe.encrypt(
                token_data,
                secret_key,
                algorithm=ALGORITHMS.DIR,
                encryption=ALGORITHMS.A256GCM,
            )

            # Add prefix to identify the encryption method
            encrypted = f"{TokenEncryption.JWE_PREFIX}{encrypted}"

            # Validate that encryption worked properly
            if TokenEncryption.is_encrypted(encrypted):
                logging.debug("encrypt_token: Token JWE encrypted successfully")
                return encrypted
            else:
                logging.warning(
                    "encrypt_token: JWE encryption completed but result doesn't match expected pattern"
                )
                return encrypted
        except JOSEError as e:
            logging.error(f"encrypt_token: JOSE encryption error: {str(e)}")
            return TokenEncryption._encrypt_with_base64(token_data)
        except Exception as e:
            logging.error(f"encrypt_token: Token encryption error: {str(e)}")
            return TokenEncryption._encrypt_with_base64(token_data)

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
            logging.debug("decrypt_token: Empty token data, returning None")
            return None

        try:
            # Check if using Base64 temporary encoding
            if encrypted_data.startswith(TokenEncryption.BASE64_PREFIX):
                logging.debug(
                    "decrypt_token: Decoding BASE64 token (temporary solution)"
                )
                try:
                    encoded_part = encrypted_data[
                        len(TokenEncryption.BASE64_PREFIX) :
                    ]  # Remove the "BASE64:" prefix
                    decoded = base64.b64decode(encoded_part).decode("utf-8")
                    return decoded
                except Exception as e:
                    logging.error(
                        f"decrypt_token: BASE64 decoding error: {str(e)}"
                    )
                    return None

            # Check if using JWE encoding
            if encrypted_data.startswith(TokenEncryption.JWE_PREFIX):
                # Remove the JWE prefix
                jwe_token = encrypted_data[len(TokenEncryption.JWE_PREFIX) :]
                secret_key = TokenEncryption._get_properly_sized_key()

                try:
                    decrypted = jwe.decrypt(
                        jwe_token,
                        secret_key,
                    )
                    return decrypted.decode("utf-8")
                except JOSEError as e:
                    logging.error(f"decrypt_token JWE error: {str(e)}")
                    return None

            # Kiểm tra xem dữ liệu có vẻ như đã mã hóa không
            if not TokenEncryption.is_encrypted(encrypted_data):
                logging.warning(
                    "Attempted to decrypt what appears to be an unencrypted token"
                )
                return encrypted_data

            # Legacy JWE token without prefix
            try:
                decrypted = jwe.decrypt(
                    encrypted_data,
                    TokenEncryption._get_properly_sized_key(),
                )
                return decrypted.decode("utf-8")
            except JOSEError as e:
                logging.error(f"decrypt_token legacy JWE error: {str(e)}")
                return None

        except Exception as e:
            logging.error(f"Token decryption error: {str(e)}")
            return None

    @staticmethod
    def is_encrypted(data: str) -> bool:
        """
        Kiểm tra xem chuỗi dữ liệu có vẻ như đã được mã hóa hay không

        Args:
            data: Chuỗi dữ liệu cần kiểm tra

        Returns:
            True nếu dữ liệu có vẻ đã được mã hóa, False nếu không
        """
        if not data:
            logging.debug("is_encrypted: Empty data, returning False")
            return False

        # Check if using Base64 temporary encoding
        if data.startswith(TokenEncryption.BASE64_PREFIX):
            logging.debug(
                "is_encrypted: Token has BASE64 format (temporary solution)"
            )
            return True

        # Check if using JWE encoding with our prefix
        if data.startswith(TokenEncryption.JWE_PREFIX):
            logging.debug("is_encrypted: Token has JWE prefix format")
            return True

        # JWE tokens typically have 5 parts separated by dots
        # and start with an encoded header
        jwe_pattern = r"^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$"

        # Check if the data matches the JWE pattern
        is_jwe_pattern = bool(re.match(jwe_pattern, data))

        if is_jwe_pattern:
            logging.debug("is_encrypted: Token matches JWE pattern")
            return True

        logging.debug("is_encrypted: Token does not appear to be encrypted")
        return False

    @staticmethod
    def encrypt_if_needed(token_data: str) -> Tuple[str, bool]:
        """
        Mã hóa token nếu nó chưa được mã hóa

        Args:
            token_data: Token data cần mã hóa

        Returns:
            Tuple gồm (token_đã_mã_hóa_hoặc_không, trạng_thái_mã_hóa)
            - token_đã_mã_hóa_hoặc_không: Chuỗi token, đã mã hóa nếu cần
            - trạng_thái_mã_hóa: True nếu token đã được mã hóa (mới hoặc cũ), False nếu không
        """
        if not token_data:
            logging.debug(
                "encrypt_if_needed: Empty token data, returning None, False"
            )
            return None, False

        # Nếu token đã mã hóa, trả về nguyên bản
        if TokenEncryption.is_encrypted(token_data):
            logging.debug(
                "encrypt_if_needed: Token already encrypted, returning as is"
            )
            return token_data, True

        # Nếu chưa mã hóa, thử dùng JWE
        logging.debug(
            "encrypt_if_needed: Token not encrypted, attempting with JWE"
        )
        encrypted = TokenEncryption.encrypt_token(token_data)

        if encrypted and TokenEncryption.is_encrypted(encrypted):
            logging.debug("encrypt_if_needed: JWE encryption successful")
            return encrypted, True
        else:
            logging.warning(
                "encrypt_if_needed: JWE encryption failed, returning original token"
            )
            return token_data, False

    @staticmethod
    def _encrypt_with_base64(token_data: str) -> Optional[str]:
        """
        Fallback method to encrypt with Base64 if JWE fails

        Args:
            token_data: Token data to encrypt

        Returns:
            BASE64 encoded token or None if encoding fails
        """
        try:
            # Add a prefix to indicate this is the temporary encryption format
            encoded = base64.b64encode(token_data.encode("utf-8")).decode(
                "utf-8"
            )
            encoded_token = f"{TokenEncryption.BASE64_PREFIX}{encoded}"
            logging.debug(
                "encrypt_with_base64: BASE64 encoding successful (temporary solution)"
            )
            return encoded_token
        except Exception as e:
            logging.error(
                f"encrypt_with_base64: BASE64 encoding failed: {str(e)}"
            )
            return None

    @staticmethod
    def _get_properly_sized_key() -> str:
        """
        Ensures the secret key is adequate for the encryption algorithm
        A256GCM requires a 32-byte key

        Returns:
            A properly sized key for encryption
        """
        secret_key = settings.SECRET_KEY
        key_bytes = secret_key.encode("utf-8")

        # A256GCM requires a 32-byte key
        required_length = 32

        if len(key_bytes) < required_length:
            logging.warning(
                f"SECRET_KEY too short: {len(key_bytes)} bytes, extending to {required_length} bytes."
            )
            # Extend the key by repeating it
            multiplier = required_length // len(key_bytes) + 1
            extended_key = (key_bytes * multiplier)[:required_length]
            return extended_key
        elif len(key_bytes) > required_length:
            logging.warning(
                f"SECRET_KEY too long: {len(key_bytes)} bytes, truncating to {required_length} bytes."
            )
            # Truncate to required length
            return key_bytes[:required_length]
        else:
            return key_bytes
