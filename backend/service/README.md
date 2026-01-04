# Transaction Aggregation Service

Multi-signature transaction aggregation service for ERC-4337 Account Abstraction smart accounts.

## Overview

This service enables **multi-signature transactions** for smart accounts by:
- Collecting signatures from multiple account owners
- Automatically submitting to bundler when threshold is reached
- Providing REST API for signature management
- Caching frequently accessed data with Redis

## Architecture

```
backend/service/
├── __init__.py           # Module initialization
├── config.py             # Configuration management
├── database.py           # PostgreSQL connection
├── schema.py             # Database models (SQLAlchemy)
├── redis_client.py       # Redis caching
├── verification.py       # Signature & nonce verification
├── aggregator.py         # Core aggregation logic
├── api.py                # FastAPI REST endpoints
└── init_db.py            # Database initialization script
```

## Features

✅ **Multi-signature Support**: Collect signatures from N-of-M owners
✅ **Auto-submission**: Automatically submit to bundler when threshold reached
✅ **Access Control**: Only account owners can view and sign transactions
✅ **Redis Caching**: Fast lookups for pending transactions and account owners
✅ **PostgreSQL Storage**: Persistent transaction history
✅ **REST API**: Easy integration with frontend applications
✅ **Signature Verification**: Cryptographic verification of all signatures
✅ **Nonce Validation**: Prevents replay attacks

## Prerequisites

### 1. PostgreSQL

Install PostgreSQL 12 or later:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (using Homebrew)
brew install postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

Create database:
```bash
sudo -u postgres psql
CREATE DATABASE nexus_aa;
CREATE USER nexus_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE nexus_aa TO nexus_user;
\q
```

### 2. Redis

Install Redis:
```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS (using Homebrew)
brew install redis

# Windows
# Download from https://redis.io/download or use WSL
```

Start Redis:
```bash
# Linux
sudo systemctl start redis

# macOS
brew services start redis

# Or run directly
redis-server
```

### 3. Python Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# PostgreSQL
DATABASE_URL=postgresql://nexus_user:your_password@localhost:5432/nexus_aa

# Redis
REDIS_URL=redis://localhost:6379/0

# Pimlico API Key (for bundler submissions)
PIMLICO_API_KEY=your_api_key_here

# API Server
API_HOST=0.0.0.0
API_PORT=8000
```

### 2. Database Initialization

Create database tables:
```bash
python backend/service/init_db.py
```

Expected output:
```
============================================================
Transaction Aggregation Service - Database Initialization
============================================================

1. Checking database connection...
✓ Database connection successful

2. Creating database tables...
✓ Database tables created successfully

============================================================
✅ Database initialization complete!
============================================================
```

## Running the Service

### Start the API Server

```bash
python backend/service/api.py
```

Or using uvicorn directly:
```bash
uvicorn backend.service.api:app --host 0.0.0.0 --port 8000 --reload
```

The service will be available at: `http://localhost:8000`

### API Documentation

Interactive API docs (Swagger UI): `http://localhost:8000/docs`
Alternative docs (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

### Base URL

```
http://localhost:8000/api/v1/multisig
```

### 1. Submit New Transaction

**POST** `/transactions`

Submit a new multi-signature transaction with the first signature.

**Request**:
```json
{
  "smart_account_address": "0x...",
  "chain_id": 11155111,
  "chain_name": "sepolia",
  "user_operation": { /* UnpackedUserOp */ },
  "threshold": 2,
  "initial_signature": "0x...",
  "signer_address": "0x..."
}
```

**Response**:
```json
{
  "success": true,
  "transaction_hash": "0x...",
  "signatures_collected": 1,
  "threshold": 2,
  "status": "Pending"
}
```

### 2. Query Pending Transactions

**GET** `/transactions/pending?account_address=0x...&chain_id=11155111&signer_address=0x...`

Get pending transactions for an account (access control: only owners).

**Response**:
```json
{
  "success": true,
  "transactions": [
    {
      "transaction_hash": "0x...",
      "user_operation": { /* UnpackedUserOp */ },
      "signatures_collected": 1,
      "threshold": 2,
      "creation_time": "2025-01-15T10:30:00Z",
      "already_signed": false
    }
  ]
}
```

### 3. Add Signature

**POST** `/transactions/{transaction_hash}/sign`

Add a signature to an existing transaction.

**Request**:
```json
{
  "signature": "0x...",
  "signer_address": "0x..."
}
```

**Response**:
```json
{
  "success": true,
  "transaction_hash": "0x...",
  "signatures_collected": 2,
  "threshold": 2,
  "status": "Success",
  "bundler_tx_hash": "0x..."
}
```

### 4. Get Transaction Status

**GET** `/transactions/{transaction_hash}/status`

Get current status of a transaction.

**Response**:
```json
{
  "success": true,
  "transaction_hash": "0x...",
  "status": "Pending",
  "signatures_collected": 1,
  "threshold": 2,
  "bundler_tx_hash": null,
  "creation_time": "2025-01-15T10:30:00Z",
  "last_signature_time": "2025-01-15T10:30:00Z"
}
```

## Usage Examples

### Python Client Example

```python
from backend.utils.account import Account
from backend.keymanager.keyManager import KeyManager

# 1. Create multi-sig account (2-of-3)
account = Account(
    network_name='sepolia',
    contract_address='0x...',
    owners=['0xOwner1', '0xOwner2', '0xOwner3'],
    threshold=2
)

# 2. Build UserOperation
call_data = account.encode_execute_call(
    target='0xRecipient',
    value=1000000000000000000,  # 1 ETH
    data=b''
)

user_op = account.build_user_operation(call_data=call_data)

# 3. First owner signs
km1 = KeyManager()
km1.unlock('password1')
user_op_hash = account.get_user_op_hash(user_op)
signature1 = km1.sign_userop(user_op_hash)
user_op['signature'] = '0x' + signature1.hex()

# 4. Send to aggregation service (auto-routed because threshold > 1)
tx_hash = account.send_user_operation(user_op)
print(f"Transaction submitted: {tx_hash}")
print(f"Status: Pending (1/2 signatures)")

# 5. Second owner signs via API
import requests

# Query pending transactions
response = requests.get(
    'http://localhost:8000/api/v1/multisig/transactions/pending',
    params={
        'account_address': account.contract_address,
        'chain_id': account.get_chain_id(),
        'signer_address': '0xOwner2'
    }
)
pending_txs = response.json()['transactions']

# Sign the transaction
km2 = KeyManager()
km2.unlock('password2')
signature2 = km2.sign_userop(user_op_hash)

# Submit signature
response = requests.post(
    f'http://localhost:8000/api/v1/multisig/transactions/{tx_hash}/sign',
    json={
        'signature': '0x' + signature2.hex(),
        'signer_address': '0xOwner2'
    }
)

result = response.json()
print(f"Transaction status: {result['status']}")  # Success
print(f"Bundler tx: {result['bundler_tx_hash']}")  # 0x...
```

## Database Schema

### multisig_transactions Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| smart_account_address | VARCHAR(42) | NOT NULL, INDEX | Account address |
| chain_id | INTEGER | NOT NULL | Chain ID |
| chain_name | VARCHAR(50) | NOT NULL | Chain name |
| transaction_hash | VARCHAR(66) | UNIQUE, NOT NULL | UserOp hash |
| user_operation | JSONB | NOT NULL | Full UserOp |
| threshold | INTEGER | NOT NULL | Required signatures |
| signatures | JSONB | NOT NULL | {address: signature} |
| creation_time | TIMESTAMP | NOT NULL | Creation time |
| status | VARCHAR(20) | NOT NULL | Pending/Success/Fail |
| last_signature_time | TIMESTAMP | NULL | Last signature time |
| bundler_tx_hash | VARCHAR(66) | NULL | Bundler tx hash |

**Indexes**:
- `idx_account_address`: Fast account lookups
- `idx_status`: Fast status queries
- `idx_account_status`: Composite index for pending transactions

## Redis Cache Keys

| Key Pattern | TTL | Description |
|-------------|-----|-------------|
| `pending_txs:{address}:{chain_id}` | 5 min | Pending tx list |
| `tx_detail:{tx_hash}` | 10 min | Transaction details |
| `account_owners:{address}:{chain_id}` | 30 min | Account owners list |

## Security Considerations

### Signature Verification
All signatures are verified against:
1. **Account ownership**: Signer must be in owners list
2. **UserOp hash**: Signature must be for correct UserOperation
3. **Replay protection**: Nonce validation prevents replay attacks

### Access Control
- **Only owners** can view pending transactions
- **Only owners** can add signatures
- **No unauthorized access** to account data

### Best Practices
1. **Use HTTPS** in production
2. **Configure CORS** appropriately
3. **Set strong database passwords**
4. **Rotate API keys** regularly
5. **Monitor logs** for suspicious activity

## Troubleshooting

### Database Connection Failed
```
✗ Database connection failed!
```
**Solution**: Check DATABASE_URL, ensure PostgreSQL is running

### Redis Connection Failed
```
⚠️  Redis connection failed
```
**Solution**: Check REDIS_URL, ensure Redis is running

### Signature Verification Failed
```
ValueError: Invalid signature from 0x...
```
**Solution**: Ensure signer is an account owner, signature is correct format (65 bytes)

### Nonce Mismatch
```
ValueError: Invalid nonce in UserOperation
```
**Solution**: Fetch fresh nonce from EntryPoint before creating UserOp

## Testing

Run tests:
```bash
pytest backend/service/test_*.py
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### Database Stats
```python
from backend.service.database import get_pool_stats
print(get_pool_stats())
# {'size': 10, 'checked_in': 8, 'overflow': 0, 'checked_out': 2}
```

## License

MIT License - see LICENSE file

## Support

For issues and questions:
- GitHub Issues: [Project Repository]
- Documentation: [Project Docs]

---

**Built with ❤️ for ERC-4337 Account Abstraction**
