from eth_account.messages import encode_defunct

from .crypto_utils import (
    aes_encrypt, aes_decrypt,
    CryptoError, WrongPassword, HMACVerificationFailed
)
from web3 import Web3
from eth_account import Account
import os


class KeyManager:

    def __init__(self, storage_path="keystore.json"):
        self.storage_path = storage_path
        self._private_key = None
        self.address = None
        self.unlocked = False

    # ---------------- 基础逻辑 ----------------

    def create_new_key(self, password: str):
        try:
            acct = Account.create()
            encrypted = aes_encrypt(acct.key, password)

            with open(self.storage_path, "wb") as f:
                f.write(encrypted)

            self.address = acct.address
            return acct.address
        except Exception as e:
            raise CryptoError(f"Create key failed: {e}")

    def import_private_key(self, private_key_hex: str, password: str):
        try:
            private_key_bytes = bytes.fromhex(private_key_hex.replace("0x", ""))
            encrypted = aes_encrypt(private_key_bytes, password)

            with open(self.storage_path, "wb") as f:
                f.write(encrypted)

            self.address = Account.from_key(private_key_bytes).address
            return self.address
        except Exception as e:
            raise CryptoError(f"Import private key failed: {e}")

    def unlock(self, password: str):
        if not os.path.exists(self.storage_path):
            raise FileNotFoundError("Keystore not found.")

        try:
            data = open(self.storage_path, "rb").read()
            private_key_bytes = aes_decrypt(data, password)
        except WrongPassword:
            raise WrongPassword("Incorrect password.")
        except HMACVerificationFailed:
            raise HMACVerificationFailed("Keystore integrity check failed — file tampered.")
        except Exception as e:
            raise CryptoError(f"Unlock failed: {e}")

        self._private_key = private_key_bytes
        self.address = Account.from_key(private_key_bytes).address
        self.unlocked = True
        return self.address

    def lock(self):
        self._private_key = None
        self.unlocked = False

    # ---------------- JSON 导入/导出 ----------------

    def export_keystore(self, dest_path: str):
        if not os.path.exists(self.storage_path):
            raise FileNotFoundError("Keystore not found.")

        try:
            data = open(self.storage_path, "rb").read()
            with open(dest_path, "wb") as f:
                f.write(data)
        except Exception as e:
            raise CryptoError(f"Export keystore failed: {e}")

    def import_keystore(self, src_path: str, password: str):
        try:
            with open(src_path, "rb") as f:
                data = f.read()

            # 解密验证密码正确性
            private_key = aes_decrypt(data, password)
            acct = Account.from_key(private_key)

            with open(self.storage_path, "wb") as f:
                f.write(data)

            self.address = acct.address
            return self.address

        except WrongPassword:
            raise WrongPassword("Incorrect password.")
        except HMACVerificationFailed:
            raise HMACVerificationFailed("Keystore has been tampered.")
        except Exception as e:
            raise CryptoError(f"Import keystore failed: {e}")

    # ---------------- 签名接口 ----------------

    def sign_message(self, message: bytes):
        if not self.unlocked:
            raise PermissionError("Wallet is locked.")
        msg = encode_defunct(message)
        try:
            acct = Account.from_key(self._private_key)
            return acct.sign_message(msg)
        except Exception as e:
            raise CryptoError(f"Sign message failed: {e}")

    def sign_transaction(self, tx: dict):
        if not self.unlocked:
            raise PermissionError("Wallet is locked.")

        try:
            acct = Account.from_key(self._private_key)
            return acct.sign_transaction(tx)
        except Exception as e:
            raise CryptoError(f"Sign transaction failed: {e}")
    def sign_userop(self, userop_hash: bytes):
        """
        Sign a UserOperation hash (EIP-712 typed data hash).

        userop_hash should be the 32-byte hash produced by your bundler/entrypoint.
        """
        if not self.unlocked:
            raise PermissionError("Wallet is locked.")

        try:
            acct = Account.from_key(self._private_key)

            # 使用 unsafe_sign_hash，因为 userOpHash 已经是 EIP-712 结构化哈希
            signed = acct.unsafe_sign_hash(userop_hash)

            # 返回 r, s, v 拼接的 65 字节签名
            return signed.signature

        except Exception as e:
            raise CryptoError(f"Sign UserOperation failed: {e}")

    def get_address(self):
        return self.address
