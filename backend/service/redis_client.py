"""
Redis client for Transaction Aggregation Service

Provides Redis caching functionality with key management and TTL settings.
"""
import json
from typing import Optional, List, Any
import redis

from backend.service.config import config


class RedisClient:
    """Redis client wrapper for caching operations"""

    def __init__(self):
        """Initialize Redis client"""
        self.client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=True,  # Automatically decode responses to strings
            socket_connect_timeout=5,
            socket_keepalive=True
        )

    def ping(self) -> bool:
        """
        Check if Redis connection is working

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            return self.client.ping()
        except Exception as e:
            print(f"Redis connection check failed: {e}")
            return False

    # ============================================
    # Pending Transactions Cache
    # ============================================

    def get_pending_txs(self, account_address: str, chain_id: int) -> Optional[List[str]]:
        """
        Get pending transaction hashes for an account

        Args:
            account_address: Smart account address
            chain_id: Chain ID

        Returns:
            List of transaction hashes, or None if not cached
        """
        key = f"pending_txs:{account_address}:{chain_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set_pending_txs(self, account_address: str, chain_id: int, tx_hashes: List[str]):
        """
        Cache pending transaction hashes for an account

        Args:
            account_address: Smart account address
            chain_id: Chain ID
            tx_hashes: List of transaction hashes
        """
        key = f"pending_txs:{account_address}:{chain_id}"
        self.client.setex(
            key,
            config.cache_ttl_pending_txs,
            json.dumps(tx_hashes)
        )

    def invalidate_pending_txs(self, account_address: str, chain_id: int):
        """
        Invalidate pending transactions cache for an account

        Args:
            account_address: Smart account address
            chain_id: Chain ID
        """
        key = f"pending_txs:{account_address}:{chain_id}"
        self.client.delete(key)

    # ============================================
    # Transaction Detail Cache
    # ============================================

    def get_tx_detail(self, transaction_hash: str) -> Optional[dict]:
        """
        Get cached transaction details

        Args:
            transaction_hash: UserOperation hash

        Returns:
            Transaction details dict, or None if not cached
        """
        key = f"tx_detail:{transaction_hash}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set_tx_detail(self, transaction_hash: str, tx_data: dict):
        """
        Cache transaction details

        Args:
            transaction_hash: UserOperation hash
            tx_data: Transaction details dictionary
        """
        key = f"tx_detail:{transaction_hash}"
        self.client.setex(
            key,
            config.cache_ttl_tx_detail,
            json.dumps(tx_data)
        )

    def invalidate_tx_detail(self, transaction_hash: str):
        """
        Invalidate transaction detail cache

        Args:
            transaction_hash: UserOperation hash
        """
        key = f"tx_detail:{transaction_hash}"
        self.client.delete(key)

    # ============================================
    # Account Owners Cache
    # ============================================

    def get_account_owners(self, account_address: str, chain_id: int) -> Optional[List[str]]:
        """
        Get cached account owners list

        Args:
            account_address: Smart account address
            chain_id: Chain ID

        Returns:
            List of owner addresses, or None if not cached
        """
        key = f"account_owners:{account_address}:{chain_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set_account_owners(self, account_address: str, chain_id: int, owners: List[str]):
        """
        Cache account owners list

        Args:
            account_address: Smart account address
            chain_id: Chain ID
            owners: List of owner addresses
        """
        key = f"account_owners:{account_address}:{chain_id}"
        self.client.setex(
            key,
            config.cache_ttl_account_owners,
            json.dumps(owners)
        )

    def invalidate_account_owners(self, account_address: str, chain_id: int):
        """
        Invalidate account owners cache

        Args:
            account_address: Smart account address
            chain_id: Chain ID
        """
        key = f"account_owners:{account_address}:{chain_id}"
        self.client.delete(key)

    # ============================================
    # Generic Cache Operations
    # ============================================

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set a cache value with optional TTL

        Args:
            key: Cache key
            value: Value to cache (will be JSON-encoded)
            ttl: Time to live in seconds (optional)
        """
        data = json.dumps(value)
        if ttl:
            self.client.setex(key, ttl, data)
        else:
            self.client.set(key, data)

    def get(self, key: str) -> Optional[Any]:
        """
        Get a cache value

        Args:
            key: Cache key

        Returns:
            Cached value (JSON-decoded), or None if not found
        """
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def delete(self, key: str):
        """
        Delete a cache key

        Args:
            key: Cache key to delete
        """
        self.client.delete(key)

    def setex(self, key: str, seconds: int, value: str):
        """
        Set key with expiration time (for session management)

        Args:
            key: Cache key
            seconds: Expiration time in seconds
            value: Value to set
        """
        self.client.setex(key, seconds, value)

    def ttl(self, key: str) -> int:
        """
        Get time to live for a key

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if key has no expiry, -2 if key doesn't exist
        """
        return self.client.ttl(key)

    def clear_all(self):
        """
        Clear all cache entries

        WARNING: Use only for development/testing
        """
        self.client.flushdb()
        print("⚠️  All Redis cache cleared")


# Global Redis client instance
redis_client = RedisClient()
