"""
FastAPI REST API for Nexus AA Service

Provides endpoints for:
- Multi-signature transaction management
- Chain interaction (accounts, transactions, queries)
- Wallet management and authentication
"""
# IMPORTANT: Load environment variables first, before any other imports
import backend.config.env_loader  # This will auto-load .env file

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.service import aggregator, chain_api
from backend.service.verification import get_account_owners, get_network_name_by_chain_id
from backend.service.config import config as service_config


# ============================================
# Pydantic Models
# ============================================

class SubmitTransactionRequest(BaseModel):
    """Request model for submitting new transaction"""
    smart_account_address: str = Field(..., description="Smart account address")
    chain_id: int = Field(..., description="Chain ID (e.g., 11155111 for Sepolia)")
    chain_name: str = Field(..., description="Chain name (e.g., 'sepolia')")
    user_operation: dict = Field(..., description="Complete UserOperation (unpacked format)")
    threshold: int = Field(..., description="Number of signatures required")
    initial_signature: str = Field(..., description="First signer's signature (hex string)")
    signer_address: str = Field(..., description="First signer's address")


class AddSignatureRequest(BaseModel):
    """Request model for adding signature"""
    signature: str = Field(..., description="Signer's signature (hex string)")
    signer_address: str = Field(..., description="Signer's address")


class SubmitTransactionResponse(BaseModel):
    """Response model for transaction submission"""
    success: bool
    transaction_hash: str
    signatures_collected: int
    threshold: int
    status: str


class AddSignatureResponse(BaseModel):
    """Response model for adding signature"""
    success: bool
    transaction_hash: str
    signatures_collected: int
    threshold: int
    status: str
    bundler_tx_hash: Optional[str] = None


class PendingTransaction(BaseModel):
    """Model for pending transaction in list"""
    transaction_hash: str
    user_operation: dict
    signatures_collected: int
    threshold: int
    creation_time: str
    already_signed: bool


class PendingTransactionsResponse(BaseModel):
    """Response model for pending transactions query"""
    success: bool
    transactions: List[PendingTransaction]


class TransactionStatusResponse(BaseModel):
    """Response model for transaction status"""
    success: bool
    transaction_hash: str
    status: str
    signatures_collected: int
    threshold: int
    bundler_tx_hash: Optional[str] = None
    creation_time: str
    last_signature_time: Optional[str] = None


# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="Nexus AA Service",
    description="Complete Account Abstraction service with multi-signature support and chain interaction",
    version="1.0.0"
)

# CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount chain interaction router
app.include_router(
    chain_api.router,
    prefix="/api/v1/chain",
    tags=["Chain Interaction"]
)


# ============================================
# API Endpoints
# ============================================

@app.post(
    "/api/v1/multisig/transactions",
    response_model=SubmitTransactionResponse,
    summary="Submit new multi-sig transaction"
)
async def submit_transaction(request: SubmitTransactionRequest):
    """
    Submit a new multi-signature transaction for signature collection

    The first signer submits the transaction with their signature.
    Other signers can then add their signatures via the /sign endpoint.
    """
    try:
        result = aggregator.submit_multisig_transaction(
            smart_account_address=request.smart_account_address,
            chain_id=request.chain_id,
            chain_name=request.chain_name,
            user_operation=request.user_operation,
            threshold=request.threshold,
            initial_signature=request.initial_signature,
            signer_address=request.signer_address
        )
        return SubmitTransactionResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.get(
    "/api/v1/multisig/transactions/pending",
    response_model=PendingTransactionsResponse,
    summary="Get pending transactions for an account"
)
async def get_pending_transactions(
    account_address: str = Query(..., description="Smart account address"),
    chain_id: int = Query(..., description="Chain ID"),
    signer_address: Optional[str] = Query(None, description="Signer address to check if already signed")
):
    """
    Get pending transactions for a specific account

    Only account owners can query pending transactions (access control).
    Returns list of transactions awaiting signatures.
    """
    try:
        # Verify signer_address is an account owner (access control)
        if signer_address:
            network_name = get_network_name_by_chain_id(chain_id)
            owners = get_account_owners(account_address, chain_id, network_name)

            if signer_address not in owners:
                raise HTTPException(
                    status_code=403,
                    detail=f"Signer {signer_address} is not an owner of account {account_address}"
                )

        # Get pending transactions
        transactions = aggregator.get_pending_transactions(
            account_address=account_address,
            chain_id=chain_id,
            signer_address=signer_address
        )

        # Convert to Pydantic models
        tx_list = [PendingTransaction(**tx) for tx in transactions]

        return PendingTransactionsResponse(
            success=True,
            transactions=tx_list
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.post(
    "/api/v1/multisig/transactions/{transaction_hash}/sign",
    response_model=AddSignatureResponse,
    summary="Add signature to existing transaction"
)
async def sign_transaction(
    transaction_hash: str,
    request: AddSignatureRequest
):
    """
    Add a signature to an existing multi-sig transaction

    Access control: Only account owners can sign.
    When threshold is reached, automatically submits to bundler.
    """
    try:
        # Get transaction details
        tx = aggregator.get_transaction(transaction_hash)
        if not tx:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {transaction_hash} not found"
            )

        # Verify signer is an account owner (access control)
        network_name = get_network_name_by_chain_id(tx['chain_id'])
        owners = get_account_owners(
            tx['smart_account_address'],
            tx['chain_id'],
            network_name
        )

        if request.signer_address not in owners:
            raise HTTPException(
                status_code=403,
                detail=f"Signer {request.signer_address} is not an owner of this account"
            )

        # Add signature
        result = aggregator.add_signature_to_transaction(
            transaction_hash=transaction_hash,
            signature=request.signature,
            signer_address=request.signer_address
        )

        return AddSignatureResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.get(
    "/api/v1/multisig/transactions/{transaction_hash}/status",
    response_model=TransactionStatusResponse,
    summary="Get transaction status"
)
async def get_transaction_status(transaction_hash: str):
    """
    Get status of a specific transaction

    Returns transaction status, signatures collected, and bundler hash if submitted.
    """
    try:
        status = aggregator.get_transaction_status(transaction_hash)

        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {transaction_hash} not found"
            )

        return TransactionStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# ============================================
# Health Check
# ============================================

@app.get("/health", summary="Health check")
async def health_check():
    """
    Health check endpoint

    Verifies database and Redis connections are working.
    """
    from backend.service.database import check_connection
    from backend.service.redis_client import redis_client

    db_ok = check_connection()
    redis_ok = redis_client.ping()

    if db_ok and redis_ok:
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected"
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "connected" if db_ok else "disconnected",
                "redis": "connected" if redis_ok else "disconnected"
            }
        )


# ============================================
# Startup and Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    from backend.service.database import init_db
    from backend.service import singleton

    print("=" * 60)
    print("Starting Nexus AA Service...")
    print("=" * 60)

    # Initialize database
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")

    # Verify Redis connection
    from backend.service.redis_client import redis_client
    if redis_client.ping():
        print("✓ Redis connected")
    else:
        print("⚠️  Redis connection failed")

    # Check wallet initialization status
    print()
    print("Wallet Status:")
    if singleton.is_initialized():
        print("✓ Keystore found")
        print("⚠️  Wallet is locked. Call POST /api/v1/chain/auth/unlock to unlock")
    else:
        print("⚠️  No keystore found")
        print("⚠️  Initialize wallet using one of:")
        print("   - POST /api/v1/chain/init/create (create new wallet)")
        print("   - POST /api/v1/chain/init/import-private-key (import private key)")
        print("   - POST /api/v1/chain/init/import-keystore (import keystore)")
    print()
    print()
    print("=" * 60)
    print(f"API running on http://{service_config.api_host}:{service_config.api_port}")
    print(f"API docs: http://{service_config.api_host}:{service_config.api_port}/docs")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down Transaction Aggregation Service...")


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=service_config.api_host,
        port=service_config.api_port,
        log_level="info"
    )
