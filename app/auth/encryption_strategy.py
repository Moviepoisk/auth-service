import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes


@dataclass
class EncryptedMessage:
    nonce: bytes
    digest: bytes
    message: bytes


async def get_session_key_async():
    loop = asyncio.get_running_loop()
    session_key = await loop.run_in_executor(None, get_random_bytes, 16)
    return session_key


class KeyPairGenerator(ABC):
    @abstractmethod
    async def generate_key_pair(self) -> (RSA.RsaKey, RSA.RsaKey):
        pass


class SessionKeyEncryptor(ABC):
    @abstractmethod
    async def encrypt_session_key(
        self, session_key: bytes, public_key: RSA.RsaKey
    ) -> bytes:
        pass

    @abstractmethod
    async def decrypt_session_key(
        self, encrypted_session_key: bytes, private_key: RSA.RsaKey
    ) -> bytes:
        pass


class DataEncryptor(ABC):
    @abstractmethod
    async def encrypt(self, data: str, session_key: bytes) -> EncryptedMessage:
        pass

    @abstractmethod
    async def decrypt(self, encrypted: EncryptedMessage, session_key: bytes) -> str:
        pass


class RSAKeyPairGenerator(KeyPairGenerator):
    async def generate_key_pair(self) -> (RSA.RsaKey, RSA.RsaKey):
        loop = asyncio.get_running_loop()
        key_pair = await loop.run_in_executor(None, RSA.generate, 2048)
        return key_pair, key_pair.public_key()


class RSAEncryptor(SessionKeyEncryptor):
    async def encrypt_session_key(
        self, session_key: bytes, public_key: RSA.RsaKey
    ) -> bytes:
        loop = asyncio.get_running_loop()
        enc_session_key = await loop.run_in_executor(
            None, PKCS1_OAEP.new(public_key).encrypt, session_key
        )
        return enc_session_key

    async def decrypt_session_key(
        self, encrypted_session_key: bytes, private_key: RSA.RsaKey
    ) -> bytes:
        loop = asyncio.get_running_loop()
        session_key = await loop.run_in_executor(
            None, PKCS1_OAEP.new(private_key).decrypt, encrypted_session_key
        )
        return session_key


class AESEncryptor(DataEncryptor):
    async def encrypt(self, data: str, session_key: bytes) -> EncryptedMessage:
        loop = asyncio.get_running_loop()
        encrypted_message = await loop.run_in_executor(
            None, lambda: self._encrypt_data(data, session_key)
        )
        return encrypted_message

    @staticmethod
    def _encrypt_data(data: str, session_key: bytes) -> EncryptedMessage:
        cipher_aes = AES.new(session_key, AES.MODE_EAX)
        ciphertext, digest = cipher_aes.encrypt_and_digest(data.encode())
        return EncryptedMessage(
            nonce=cipher_aes.nonce, digest=digest, message=ciphertext
        )

    async def decrypt(self, encrypted: EncryptedMessage, session_key: bytes) -> str:
        loop = asyncio.get_running_loop()
        decrypted_data = await loop.run_in_executor(
            None, lambda: self._decrypt_data(encrypted, session_key)
        )
        return decrypted_data

    @staticmethod
    def _decrypt_data(encrypted: EncryptedMessage, session_key: bytes) -> str:
        cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce=encrypted.nonce)
        data = cipher_aes.decrypt_and_verify(
            encrypted.message, encrypted.digest)
        return data.decode()


# Пример использования
# async def main():
#     session_key = await get_session_key_async()
#     key_generator = RSAKeyPairGenerator()
#     session_key_encryptor = RSAEncryptor()
#     data_encryptor = AESEncryptor()

#     private_key, public_key = await key_generator.generate_key_pair()
#     encrypted_session_key = await session_key_encryptor.encrypt_session_key(session_key, public_key)
#     decrypted_session_key = await session_key_encryptor.decrypt_session_key(encrypted_session_key, private_key)

#     original_data = "Secret Data"
#     encrypted_data = await data_encryptor.encrypt(original_data, session_key)
#     decrypted_data = await data_encryptor.decrypt(encrypted_data, session_key)

#     print(f"Original Data: {original_data}")
#     print(f"Encrypted Data: {encrypted_data}")
#     print(f"Decrypted Data: {decrypted_data}")

# asyncio.run(main())
