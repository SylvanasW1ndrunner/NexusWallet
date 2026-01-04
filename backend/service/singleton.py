"""
Singleton Management for KeyManager and Wallet

Provides global singleton instances for KeyManager and Wallet.
Ensures only one instance exists throughout the service lifecycle.
"""
import configparser
import os
from typing import Optional

from backend.config import config
from backend.config.config import Config
from backend.keymanager.keyManager import KeyManager
from backend.utils.wallet import Wallet


# Global singleton instances
_key_manager: Optional[KeyManager] = None
_wallet: Optional[Wallet] = None
_netConfig:Optional[config.Config] = None
_initialized: bool = False
_unlocked: bool = False


def is_initialized() -> bool:
    """
    Check if wallet has been initialized.

    Returns:
        True if keystore exists, False otherwise
    """
    return os.path.exists("keystore.json")


def is_unlocked() -> bool:
    """
    Check if wallet is currently unlocked.

    Returns:
        True if wallet is unlocked, False otherwise
    """
    return _unlocked


def init_from_keystore(password: str) -> str:
    """
    Initialize wallet from existing keystore.

    Args:
        password: Password to unlock keystore

    Returns:
        EOA address

    Raises:
        FileNotFoundError: If keystore doesn't exist
        WrongPassword: If password is incorrect
    """
    global _key_manager, _wallet, _initialized, _unlocked

    _key_manager = KeyManager()
    address = _key_manager.unlock(password)
    _wallet = Wallet(key_manager=_key_manager, auto_load=True)
    _initialized = True
    _unlocked = True

    return address


def init_create_new(password: str) -> str:
    """
    Create new wallet with new private key.

    Args:
        password: Password to encrypt keystore

    Returns:
        EOA address

    Raises:
        CryptoError: If key creation fails
    """
    global _key_manager, _wallet, _initialized, _unlocked

    _key_manager = KeyManager()
    address = _key_manager.create_new_key(password)
    _key_manager.unlock(password)
    _wallet = Wallet(key_manager=_key_manager)
    _initialized = True
    _unlocked = True

    return address


def init_import_private_key(private_key: str, password: str) -> str:
    """
    Import wallet from private key.

    Args:
        private_key: Private key hex string (with or without 0x prefix)
        password: Password to encrypt keystore

    Returns:
        EOA address

    Raises:
        CryptoError: If import fails
    """
    global _key_manager, _wallet, _initialized, _unlocked

    _key_manager = KeyManager()
    address = _key_manager.import_private_key(private_key, password)
    _key_manager.unlock(password)
    _wallet = Wallet(key_manager=_key_manager)
    _initialized = True
    _unlocked = True

    return address


def init_import_keystore(keystore_path: str, password: str) -> str:
    """
    Import wallet from keystore file.

    Args:
        keystore_path: Path to keystore file
        password: Password to decrypt keystore

    Returns:
        EOA address

    Raises:
        FileNotFoundError: If keystore file doesn't exist
        WrongPassword: If password is incorrect
    """
    global _key_manager, _wallet, _initialized, _unlocked

    _key_manager = KeyManager()
    address = _key_manager.import_keystore(keystore_path, password)
    _key_manager.unlock(password)
    _wallet = Wallet(key_manager=_key_manager, auto_load=True)
    _initialized = True
    _unlocked = True

    return address


def lock_wallet_singleton():
    """
    Lock the wallet (clear private key from memory).

    After locking, all operations requiring signing will fail.
    """
    global _unlocked

    if _key_manager:
        _key_manager.lock()

    _unlocked = False


def get_key_manager() -> KeyManager:
    """
    Get the global KeyManager instance.

    Returns:
        KeyManager instance

    Raises:
        RuntimeError: If wallet is not unlocked
    """
    if not _unlocked:
        raise RuntimeError("Wallet is locked. Please unlock first.")

    if _key_manager is None:
        raise RuntimeError("KeyManager not initialized.")

    return _key_manager


def get_wallet() -> Wallet:
    """
    Get the global Wallet instance.

    Returns:
        Wallet instance

    Raises:
        RuntimeError: If wallet is not unlocked
    """
    if not _unlocked:
        raise RuntimeError("Wallet is locked. Please unlock first.")

    if _wallet is None:
        raise RuntimeError("Wallet not initialized.")

    return _wallet


def get_eoa_address() -> Optional[str]:
    """
    Get EOA address without requiring unlock.

    Returns:
        EOA address if initialized, None otherwise
    """
    if _key_manager:
        return _key_manager.address
    return None

def get_networkConfig() -> Optional[Config]:
    if not _netConfig:
        raise RuntimeError("NetworkConfig not initialized.")
    return _netConfig
