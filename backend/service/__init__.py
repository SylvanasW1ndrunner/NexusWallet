"""
Transaction Aggregation Service Module

This module provides multi-signature transaction aggregation functionality
for ERC-4337 Account Abstraction smart accounts.

Components:
- schema: PostgreSQL database models
- database: Database connection management
- redis_client: Redis caching layer
- verification: Signature and nonce verification
- aggregator: Core transaction aggregation logic
- api: FastAPI REST endpoints
"""

__all__ = [
    'schema',
    'database',
    'redis_client',
    'verification',
    'aggregator',
    'api'
]
