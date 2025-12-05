import os
import base64
import hmac
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class CryptoError(Exception):
    pass


class HMACVerificationFailed(CryptoError):
    pass


class WrongPassword(CryptoError):
    pass


def derive_key(password: str, salt: bytes, length=32) -> bytes:
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=length,
            salt=salt,
            iterations=390000,
        )
        return kdf.derive(password.encode())
    except Exception as e:
        raise CryptoError(f"KDF key derivation failed: {e}")


def aes_encrypt(data: bytes, password: str) -> bytes:
    try:
        salt = os.urandom(16)
        key = derive_key(password, salt, length=32)
        hmac_key = derive_key(password, salt, length=32)  # same salt, diff key

        iv = os.urandom(16)

        cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()

        # HMAC = HMAC(salt + iv + ciphertext)
        mac = hmac.new(hmac_key, salt + iv + ciphertext, hashlib.sha256).digest()

        return base64.b64encode(salt + iv + ciphertext + mac)
    except Exception as e:
        raise CryptoError(f"AES encrypt failed: {e}")


def aes_decrypt(enc_data: bytes, password: str) -> bytes:
    try:
        raw = base64.b64decode(enc_data)
    except Exception:
        raise CryptoError("Base64 decode failed (corrupted keystore).")

    if len(raw) < 16 + 16 + 32:  # salt + iv + HMAC
        raise CryptoError("Encrypted data too short or invalid.")

    try:
        salt = raw[:16]
        iv = raw[16:32]
        ciphertext = raw[32:-32]
        mac = raw[-32:]

        key = derive_key(password, salt, 32)
        hmac_key = derive_key(password, salt, 32)

        # HMAC 验证
        real_mac = hmac.new(hmac_key, salt + iv + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, real_mac):
            raise HMACVerificationFailed("HMAC check failed — data integrity violation.")

        cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    except HMACVerificationFailed:
        raise
    except Exception:
        raise WrongPassword("Wrong password or corrupted keystore.")
