from unittest.mock import MagicMock, patch

import pytest

from app.utils.encryption import TokenEncryption


class TestTokenEncryption:
    """Unit tests for the TokenEncryption class"""

    def test_is_encrypted(self):
        """Test the is_encrypted method for different token formats"""
        # Valid JWE token format (fake example)
        fake_jwe = "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..aaaaa.bbbbb.ccccc"
        assert TokenEncryption.is_encrypted(fake_jwe) is True

        # Facebook token format (not JWE)
        fb_token = "EAAQHgrXRCI4BOwU7J9OwNSKbtQJ0xlKpEu8feZB1tWCXcAOOIy1BRtarYHoKGpOz9nB65vItsVa"
        assert TokenEncryption.is_encrypted(fb_token) is False

        # JSON string
        json_string = '{"access_token": "1234567890", "expires_at": "2023-12-31T23:59:59"}'
        assert TokenEncryption.is_encrypted(json_string) is False

        # Empty string
        assert TokenEncryption.is_encrypted("") is False

        # None
        assert TokenEncryption.is_encrypted(None) is False

    @patch("app.utils.encryption.jwe.encrypt")
    def test_encrypt_token(self, mock_encrypt):
        """Test token encryption"""
        # Setup mock
        mock_encrypt.return_value = "encrypted_token_123"

        # Test with valid token
        token = '{"key": "value"}'
        result = TokenEncryption.encrypt_token(token)
        assert result == "encrypted_token_123"
        mock_encrypt.assert_called_once()

        # Test with empty token
        assert TokenEncryption.encrypt_token("") is None
        # Count should still be 1 because we're not calling the mock again
        assert mock_encrypt.call_count == 1

        # Test with None
        assert TokenEncryption.encrypt_token(None) is None
        assert mock_encrypt.call_count == 1

    @patch("app.utils.encryption.jwe.encrypt")
    @patch("app.utils.encryption.TokenEncryption.is_encrypted")
    def test_encrypt_token_already_encrypted(
        self, mock_is_encrypted, mock_encrypt
    ):
        """Test that already encrypted tokens aren't re-encrypted"""
        # Setup mock
        mock_is_encrypted.return_value = True

        # Test with token that looks encrypted
        token = "encrypted_token_123"
        result = TokenEncryption.encrypt_token(token)

        # Should return token as is and not call encrypt
        assert result == token
        mock_encrypt.assert_not_called()

    @patch("app.utils.encryption.jwe.encrypt")
    def test_encrypt_token_error(self, mock_encrypt):
        """Test error handling during encryption"""
        # Setup mock to raise exception
        mock_encrypt.side_effect = Exception("Test encryption error")

        # Test with token
        token = '{"key": "value"}'
        result = TokenEncryption.encrypt_token(token)

        # Should return None on error
        assert result is None
        mock_encrypt.assert_called_once()

    @patch("app.utils.encryption.jwe.decrypt")
    def test_decrypt_token(self, mock_decrypt):
        """Test token decryption"""
        # Setup mock
        mock_decrypt_result = MagicMock()
        mock_decrypt_result.decode.return_value = '{"key": "value"}'
        mock_decrypt.return_value = mock_decrypt_result

        # Test with encrypted token
        with patch(
            "app.utils.encryption.TokenEncryption.is_encrypted",
            return_value=True,
        ):
            encrypted = "encrypted_token_123"
            result = TokenEncryption.decrypt_token(encrypted)
            assert result == '{"key": "value"}'
            mock_decrypt.assert_called_once()

        # Test with empty token
        assert TokenEncryption.decrypt_token("") is None
        # Count should still be 1 because we're not calling the mock again
        assert mock_decrypt.call_count == 1

        # Test with None
        assert TokenEncryption.decrypt_token(None) is None
        assert mock_decrypt.call_count == 1

    @patch("app.utils.encryption.jwe.decrypt")
    def test_decrypt_token_not_encrypted(self, mock_decrypt):
        """Test decryption of non-encrypted tokens"""
        # Mock is_encrypted to return False
        with patch(
            "app.utils.encryption.TokenEncryption.is_encrypted",
            return_value=False,
        ):
            token = "not_encrypted_token"
            result = TokenEncryption.decrypt_token(token)

            # Should return token as is without calling decrypt
            assert result == token
            mock_decrypt.assert_not_called()

    @patch("app.utils.encryption.jwe.decrypt")
    def test_decrypt_token_error(self, mock_decrypt):
        """Test error handling during decryption"""
        # Mock is_encrypted to return True
        with patch(
            "app.utils.encryption.TokenEncryption.is_encrypted",
            return_value=True,
        ):
            # Setup mock to raise exception
            mock_decrypt.side_effect = Exception("Test decryption error")

            # Test with token
            token = "encrypted_token_123"
            result = TokenEncryption.decrypt_token(token)

            # Should return None on error
            assert result is None
            mock_decrypt.assert_called_once()

    def test_encrypt_if_needed(self):
        """Test the encrypt_if_needed method"""
        # Test with already encrypted token
        with patch(
            "app.utils.encryption.TokenEncryption.is_encrypted",
            return_value=True,
        ):
            token = "already_encrypted_token"
            result, status = TokenEncryption.encrypt_if_needed(token)
            assert result == token
            assert status is True

        # Test with token that needs encryption
        with patch(
            "app.utils.encryption.TokenEncryption.is_encrypted",
            return_value=False,
        ):
            with patch(
                "app.utils.encryption.TokenEncryption.encrypt_token",
                return_value="newly_encrypted_token",
            ):
                token = "unencrypted_token"
                result, status = TokenEncryption.encrypt_if_needed(token)
                assert result == "newly_encrypted_token"
                assert status is True

        # Test with encryption failure
        with patch(
            "app.utils.encryption.TokenEncryption.is_encrypted",
            return_value=False,
        ):
            with patch(
                "app.utils.encryption.TokenEncryption.encrypt_token",
                return_value=None,
            ):
                token = "unencrypted_token"
                result, status = TokenEncryption.encrypt_if_needed(token)
                assert result == token  # Should return original token
                assert status is False

        # Test with empty token
        result, status = TokenEncryption.encrypt_if_needed("")
        assert result is None
        assert status is False

        # Test with None
        result, status = TokenEncryption.encrypt_if_needed(None)
        assert result is None
        assert status is False
