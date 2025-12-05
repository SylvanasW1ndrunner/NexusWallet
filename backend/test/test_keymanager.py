import os
import pytest
from hexbytes import HexBytes
from web3 import Web3
from eth_account import Account
from backend.keymanager.keyManager import KeyManager
from backend.keymanager.crypto_utils import (
    WrongPassword,
    HMACVerificationFailed,
    CryptoError,
)

TEST_KEYSTORE = "test_keystore.json"


@pytest.fixture
def km():
    # 删除旧文件，保证测试环境干净
    if os.path.exists(TEST_KEYSTORE):
        os.remove(TEST_KEYSTORE)
    return KeyManager(storage_path=TEST_KEYSTORE)


def test_create_new_key(km):
    addr = km.create_new_key("password123")
    assert addr.startswith("0x")
    assert os.path.exists(TEST_KEYSTORE)


def test_import_private_key(km):
    raw = Account.create().key.hex()
    addr = km.import_private_key(raw, "pwd")
    assert addr.startswith("0x")
    assert os.path.exists(TEST_KEYSTORE)


def test_unlock_success(km):
    km.create_new_key("abc")
    addr = km.unlock("abc")
    assert addr == km.get_address()
    assert km.unlocked is True


def test_unlock_wrong_password(km):
    km.create_new_key("abc")
    with pytest.raises(HMACVerificationFailed):
        km.unlock("wrong")


def test_unlock_hmac_tampered(km):
    km.create_new_key("abc")

    # 破坏密文，触发 HMACVerificationFailed
    with open(TEST_KEYSTORE, "rb") as f:
        data = bytearray(f.read())
    data[-1] ^= 0xFF  # 修改一个字节
    with open(TEST_KEYSTORE, "wb") as f:
        f.write(data)

    with pytest.raises(CryptoError):
        km.unlock("abc")


def test_lock(km):
    km.create_new_key("111")
    km.unlock("111")
    km.lock()
    assert km.unlocked is False
    assert km._private_key is None


def test_sign_message(km):
    km.create_new_key("pwd")
    km.unlock("pwd")

    msg = b'hello'
    sig = km.sign_message(msg)

    # 结构检查（SignedMessage 有这些字段）
    assert hasattr(sig, "r")
    assert hasattr(sig, "s")
    assert hasattr(sig, "v")
    assert hasattr(sig, "signature")
    assert hasattr(sig, "message_hash")

    # 基础有效性检查
    assert isinstance(sig.r, int)
    assert isinstance(sig.s, int)
    assert isinstance(sig.v, int)
    assert len(sig.signature) == 65  # 65 bytes (r||s||v)



def test_sign_message_when_locked(km):
    km.create_new_key("pwd")
    msg = Web3.keccak(text="hello")

    with pytest.raises(PermissionError):
        km.sign_message(msg)


def test_sign_message(km):
    km.create_new_key("pwd")
    km.unlock("pwd")

    msg = b'hello'
    sig = km.sign_message(msg)

    # 检查返回类型
    assert hasattr(sig, "r")
    assert hasattr(sig, "s")
    assert hasattr(sig, "v")
    assert hasattr(sig, "signature")
    assert hasattr(sig, "message_hash")

    assert isinstance(sig.r, int)
    assert isinstance(sig.s, int)
    assert isinstance(sig.v, int)
    assert isinstance(sig.signature, (bytes, HexBytes))
    assert isinstance(sig.message_hash, (bytes, HexBytes))



def test_sign_transaction_locked(km):
    km.create_new_key("pwd")

    with pytest.raises(PermissionError):
        km.sign_transaction({})


def test_sign_userop(km):
    km.create_new_key("pwd")
    km.unlock("pwd")

    # userOpHash 必须是32字节
    userop_hash = Web3.keccak(text="userop-test")

    sig = km.sign_userop(userop_hash)

    assert isinstance(sig, bytes)
    assert len(sig) == 65  # r + s + v


def test_sign_userop_locked(km):
    km.create_new_key("pwd")

    with pytest.raises(PermissionError):
        km.sign_userop(os.urandom(32))


def test_export_keystore(km):
    km.create_new_key("pwd")

    dest = "exported.json"
    if os.path.exists(dest):
        os.remove(dest)

    km.export_keystore(dest)

    assert os.path.exists(dest)

    os.remove(dest)


def test_import_keystore(km):
    km.create_new_key("pwd")

    # 导出
    src = "backup.json"
    if os.path.exists(src):
        os.remove(src)

    km.export_keystore(src)

    # 新 manager 导入
    km2 = KeyManager(storage_path="new.json")
    addr2 = km2.import_keystore(src, "pwd")

    assert addr2.startswith("0x")
    os.remove(src)
    os.remove("new.json")
