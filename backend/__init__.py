"""
Nexus - Account Abstraction Wallet Backend

Core modules:
- KeyManager: Encrypted private key management
- Config: Multi-chain network configuration
- Account: Smart contract account operations
- Wallet: Multi-chain wallet management
"""

from .keymanager.keyManager import KeyManager
from .keymanager.crypto_utils import CryptoError, WrongPassword, HMACVerificationFailed
from .config import Config, NetworkConfig
from .account import Account
from .wallet import Wallet

__version__ = "0.1.0"

__all__ = [
    # Key Management
    "KeyManager",
    "CryptoError",
    "WrongPassword",
    "HMACVerificationFailed",

    # Configuration
    "Config",
    "NetworkConfig",

    # Core Classes
    "Account",
    "Wallet",
]
