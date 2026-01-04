"""
Configuration module for Transaction Aggregation Service

Manages PostgreSQL and Redis connection settings from environment variables.
"""
import os
from typing import Optional


class ServiceConfig:
    """Configuration for aggregation service"""

    def __init__(self):
        """Initialize configuration from environment variables"""
        # PostgreSQL configuration
        self.database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/nexus_aa'
        )

        # Redis configuration
        self.redis_url = os.getenv(
            'REDIS_URL',
            'redis://localhost:6379/0'
        )

        # Pimlico API key for bundler submissions
        self.pimlico_api_key = os.getenv('PIMLICO_API_KEY', '')

        # Cache TTL settings (in seconds)
        self.cache_ttl_pending_txs = int(os.getenv('CACHE_TTL_PENDING_TXS', '300'))  # 5 minutes
        self.cache_ttl_tx_detail = int(os.getenv('CACHE_TTL_TX_DETAIL', '600'))  # 10 minutes
        self.cache_ttl_account_owners = int(os.getenv('CACHE_TTL_ACCOUNT_OWNERS', '1800'))  # 30 minutes

        # Database connection pool settings
        self.db_pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.db_max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        self.db_pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))

        # API settings
        self.api_host = os.getenv('API_HOST', '0.0.0.0')
        self.api_port = int(os.getenv('API_PORT', '8000'))

    def validate(self) -> bool:
        """
        Validate configuration

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If required configuration is missing
        """
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        if not self.redis_url:
            raise ValueError("REDIS_URL environment variable is required")

        if not self.pimlico_api_key:
            import warnings
            warnings.warn(
                "PIMLICO_API_KEY not set. Bundler submissions will fail for single-sig accounts."
            )

        return True

    @property
    def redis_host(self) -> str:
        """Extract Redis host from URL"""
        # Parse redis://host:port/db format
        if '://' in self.redis_url:
            host_part = self.redis_url.split('://')[1]
            host = host_part.split(':')[0]
            return host
        return 'localhost'

    @property
    def redis_port(self) -> int:
        """Extract Redis port from URL"""
        if '://' in self.redis_url:
            host_part = self.redis_url.split('://')[1]
            if ':' in host_part:
                port_part = host_part.split(':')[1]
                port = port_part.split('/')[0]
                return int(port)
        return 6379

    @property
    def redis_db(self) -> int:
        """Extract Redis database number from URL"""
        if '/' in self.redis_url:
            db = self.redis_url.split('/')[-1]
            return int(db)
        return 0


# Global config instance
config = ServiceConfig()
