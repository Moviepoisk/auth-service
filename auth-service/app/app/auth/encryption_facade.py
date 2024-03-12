import json
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Union
from uuid import UUID

from app.auth.encryption_strategy import (
    AESEncryptor,
    EncryptedMessage,
    RSAEncryptor,
    RSAKeyPairGenerator,
    get_session_key_async,
)
# Вспомогательные классы и функции определены выше
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA

class EncryptionFacade:
    def __init__(self):
        self.rsa_key_par_generator = RSAKeyPairGenerator()
        self.rsa_encryptor = RSAEncryptor()
        self.aes_encryptor = AESEncryptor()

    async def generate_keys(self) -> Dict[str, Union[RSA.RsaKey, RSA.RsaKey, bytes, str]]:
        session_key = await get_session_key_async()
        private_key, public_key = await self.rsa_key_par_generator.generate_key_pair()
        encrypted_session_key = await self.rsa_encryptor.encrypt_session_key(session_key, public_key)

        return {
            "private_key": private_key,
            "public_key": public_key,
            "encrypted_session_key": encrypted_session_key,
            "session_key": session_key,
        }
    
    async def convert_keys_to_storage_format(
            self, private_key: RSA.RsaKey,
            public_key: RSA.RsaKey,
            encrypted_session_key: bytes
    ) -> Dict[str, Union[bytes, str]]:
        return {
            "private_key": private_key.exportKey(),
            "public_key": public_key.exportKey(),
            "encrypted_session_key": encrypted_session_key,
        }

    async def encrypt_data(self, data: str, session_key: bytes) -> str:
        encrypted_message = await self.aes_encryptor.encrypt(data, session_key)
        encrypted_data_json = json.dumps({
            "nonce": encrypted_message.nonce.hex(),
            "digest": encrypted_message.digest.hex(),
            "message": encrypted_message.message.hex(),
        })
        return encrypted_data_json

    async def decrypt_data(self, encrypted_data_json: str, session_key: bytes) -> str:
        encrypted_data = json.loads(encrypted_data_json)
        encrypted_message = EncryptedMessage(
            nonce=bytes.fromhex(encrypted_data["nonce"]),
            digest=bytes.fromhex(encrypted_data["digest"]),
            message=bytes.fromhex(encrypted_data["message"])
        )
        decrypted_data = await self.aes_encryptor.decrypt(encrypted_message, session_key)
        return decrypted_data
    
    async def import_rsa_key(self, pem_key: bytes) -> RSA.RsaKey:
        return RSA.import_key(pem_key)
    
    async def decrypt_session_key(
        self, encrypted_session_key: bytes, private_key: RSA.RsaKey
    ):
        return await self.rsa_encryptor.decrypt_session_key(encrypted_session_key, private_key)
    