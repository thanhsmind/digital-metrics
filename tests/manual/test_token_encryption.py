#!/usr/bin/env python
"""
Manual test script for token encryption with JWE

Usage:
    python -m tests.manual.test_token_encryption
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, Optional, Tuple

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

from app.core.config import settings
from app.utils.encryption import TokenEncryption

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("token_encryption_test")

# Test token for encryption
TEST_TOKEN = "EAAQHgrXRCI4BOwU7J9OwNSKbtQJ0xlKpEu8feZB1tWCXcAOOIy1BRtarYHoKGpOz9nB65vItsVa"


def test_token_encryption() -> Dict[str, Any]:
    """Test token encryption with both JWE and BASE64 methods"""
    results = {
        "jwe_success": False,
        "base64_success": False,
        "jwe_correctly_identified": False,
        "base64_correctly_identified": False,
        "decryption_success": {
            "jwe": False,
            "base64": False,
        },
        "encrypt_if_needed": {
            "success": False,
            "returns_correct_status": False,
        },
    }

    logger.info("=== STARTING TOKEN ENCRYPTION TESTS ===")

    # Test 1: Direct JWE encryption
    logger.info("Test 1: Direct JWE encryption")
    encrypted_jwe = encrypt_with_jwe(TEST_TOKEN)
    results["jwe_success"] = encrypted_jwe is not None

    if encrypted_jwe:
        logger.info(f"JWE Encrypted token: {encrypted_jwe[:30]}... (truncated)")
        # Test if correctly identified as encrypted
        is_encrypted = TokenEncryption.is_encrypted(encrypted_jwe)
        results["jwe_correctly_identified"] = is_encrypted
        logger.info(
            f"JWE token correctly identified as encrypted: {is_encrypted}"
        )

        # Test JWE decryption
        decrypted = TokenEncryption.decrypt_token(encrypted_jwe)
        results["decryption_success"]["jwe"] = decrypted == TEST_TOKEN
        logger.info(
            f"JWE decryption success: {results['decryption_success']['jwe']}"
        )

    # Test 2: BASE64 encryption
    logger.info("\nTest 2: BASE64 encryption (fallback)")
    encrypted_base64 = encrypt_with_base64(TEST_TOKEN)
    results["base64_success"] = encrypted_base64 is not None

    if encrypted_base64:
        logger.info(
            f"BASE64 Encrypted token: {encrypted_base64[:30]}... (truncated)"
        )
        # Test if correctly identified as encrypted
        is_encrypted = TokenEncryption.is_encrypted(encrypted_base64)
        results["base64_correctly_identified"] = is_encrypted
        logger.info(
            f"BASE64 token correctly identified as encrypted: {is_encrypted}"
        )

        # Test BASE64 decryption
        decrypted = TokenEncryption.decrypt_token(encrypted_base64)
        results["decryption_success"]["base64"] = decrypted == TEST_TOKEN
        logger.info(
            f"BASE64 decryption success: {results['decryption_success']['base64']}"
        )

    # Test 3: encrypt_if_needed
    logger.info("\nTest 3: encrypt_if_needed")
    encrypted, status = TokenEncryption.encrypt_if_needed(TEST_TOKEN)
    results["encrypt_if_needed"]["success"] = encrypted is not None
    results["encrypt_if_needed"]["returns_correct_status"] = status == (
        encrypted is not None
    )

    if encrypted:
        logger.info(
            f"encrypt_if_needed result: {encrypted[:30]}... (truncated)"
        )
        logger.info(f"encrypt_if_needed status: {status}")

        # Verify decryption of result
        decrypted = TokenEncryption.decrypt_token(encrypted)
        decrypt_success = decrypted == TEST_TOKEN
        logger.info(f"encrypt_if_needed decryption success: {decrypt_success}")

        # Test that re-encryption doesn't double encrypt
        reencrypted, restatus = TokenEncryption.encrypt_if_needed(encrypted)
        logger.info(
            f"Re-encryption attempted: Same token returned: {reencrypted == encrypted}"
        )

    # Print final results
    logger.info("\n=== TOKEN ENCRYPTION TEST RESULTS ===")
    for key, value in results.items():
        if isinstance(value, dict):
            logger.info(f"{key}:")
            for subkey, subvalue in value.items():
                logger.info(f"  - {subkey}: {subvalue}")
        else:
            logger.info(f"{key}: {value}")

    return results


def encrypt_with_jwe(token: str) -> Optional[str]:
    """Encrypt token directly with JWE"""
    try:
        from jose import jwe
        from jose.constants import ALGORITHMS

        # Get properly sized key
        secret_key = TokenEncryption._get_properly_sized_key()

        # Encrypt with JWE
        encrypted = jwe.encrypt(
            token,
            secret_key,
            algorithm=ALGORITHMS.DIR,
            encryption=ALGORITHMS.A256GCM,
        )

        # Add prefix
        return f"{TokenEncryption.JWE_PREFIX}{encrypted}"
    except Exception as e:
        logger.error(f"JWE encryption error: {str(e)}")
        return None


def encrypt_with_base64(token: str) -> Optional[str]:
    """Encrypt token with BASE64 (fallback method)"""
    return TokenEncryption._encrypt_with_base64(token)


if __name__ == "__main__":
    test_token_encryption()
