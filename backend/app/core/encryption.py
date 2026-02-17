"""
AES-256-GCM encryption service for Telegram sessions
"""

import base64
import os
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()


class SessionEncryptionService:
    """
    AES-256-GCM encryption service for secure session storage
    """

    def __init__(self):
        self.key = self._get_encryption_key()

    def _get_encryption_key(self) -> bytes:
        """Get or validate encryption key"""
        key = settings.encryption_key.encode('utf-8')
        if len(key) != 32:
            raise ValueError(
                "Encryption key must be exactly 32 bytes for AES-256"
            )
        return key

    def encrypt(self, data: bytes) -> str:
        """
        Encrypt data using AES-256-GCM

        Args:
            data: Raw session data bytes

        Returns:
            Base64 encoded string containing IV + ciphertext + tag
        """
        try:
            # Generate random 12-byte nonce (IV)
            nonce = os.urandom(12)

            # Create AESGCM cipher
            aesgcm = AESGCM(self.key)

            # Encrypt data
            ciphertext = aesgcm.encrypt(nonce, data, None)

            # Combine nonce + ciphertext
            encrypted = nonce + ciphertext

            # Return base64 encoded string
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Encryption failed: {str(e)}"
            )

    def decrypt(self, encrypted_data: str) -> bytes:
        """
        Decrypt data using AES-256-GCM

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            Decrypted raw bytes
        """
        try:
            # Decode from base64
            encrypted = base64.b64decode(encrypted_data.encode('utf-8'))

            # Extract nonce (first 12 bytes)
            nonce = encrypted[:12]

            # Extract ciphertext (rest)
            ciphertext = encrypted[12:]

            # Create AESGCM cipher
            aesgcm = AESGCM(self.key)

            # Decrypt data
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Decryption failed: {str(e)}"
            )

    def is_valid_encrypted_data(self, data: str) -> bool:
        """
        Check if string appears to be valid encrypted data

        Args:
            data: String to check

        Returns:
            True if valid encrypted format
        """
        try:
            decoded = base64.b64decode(data.encode('utf-8'))
            # Minimum: nonce (12) + tag (16) = 28 bytes
            return len(decoded) >= 28
        except Exception:
            return False


# Singleton instance
encryption_service = SessionEncryptionService()
