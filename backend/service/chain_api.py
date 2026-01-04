"""
Chain Interaction API for Nexus AA Service

Provides REST API endpoints for:
- Wallet initialization and authentication
- Account management
- Transaction operations
- Chain queries
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.service.auth import verify_session_token
from backend.service.session import SessionManager
from backend.service import singleton
from backend.config.config import Config, NetworkConfig


# ============================================
# Pydantic Models
# ============================================

# Authentication Models
class UnlockRequest(BaseModel):
    password: str = Field(..., description="Wallet password")


class CreateWalletRequest(BaseModel):
    password: str = Field(..., description="Password to encrypt keystore")


class ImportPrivateKeyRequest(BaseModel):
    private_key: str = Field(..., description="Private key hex string")
    password: str = Field(..., description="Password to encrypt keystore")


class ImportKeystoreRequest(BaseModel):
    keystore_path: str = Field(..., description="Path to keystore file")
    password: str = Field(..., description="Password to decrypt keystore")

class ImportNetConfigRequest(BaseModel):
    config_path: str = Field(default=None, description="Path to config file")
# Account Models
class CreateAccountRequest(BaseModel):
    network_name: str = Field(..., description="Network name (e.g., 'sepolia')")
    owners: Optional[List[str]] = Field(None, description="Owner addresses (uses EOA if not provided)")
    threshold: int = Field(1, description="Signature threshold")
    name: Optional[str] = Field(None, description="User-friendly name for the account")
    guardians: Optional[List[str]] = Field(None, description="Guardian addresses")
    guardian_threshold: int = Field(0, description="Guardian signature threshold")
    salt: int = Field(0, description="Salt for CREATE2 deployment")


class RemoveAccountRequest(BaseModel):
    network_name: str = Field(..., description="Network name")
    account_address: str = Field(..., description="Account address to remove")


class UpdateAccountRequest(BaseModel):
    network_name: str = Field(..., description="Network name")
    account_address: str = Field(..., description="Account address to update")
    name: Optional[str] = Field(None, description="New account name")
    bundler_url: Optional[str] = Field(None, description="New bundler URL")
    paymaster_url: Optional[str] = Field(None, description="New paymaster URL")


# Transaction Models
class SendUserOpRequest(BaseModel):
    network_name: str = Field(..., description="Network name")
    account_address: str = Field(..., description="Smart account address")
    target: str = Field(..., description="Target address")
    value: int = Field(0, description="ETH value in wei")
    data: str = Field("0x", description="Call data (hex string)")


class SendEOATransactionRequest(BaseModel):
    network_name: str = Field(..., description="Network name")
    to: str = Field(..., description="Recipient address")
    value: int = Field(0, description="ETH value in wei")
    data: str = Field("0x", description="Transaction data (hex string)")
    gas: Optional[int] = Field(None, description="Gas limit")


class SignMessageRequest(BaseModel):
    message: str = Field(..., description="Message to sign")


# Query Models
class BalanceQuery(BaseModel):
    network_name: str = Field(..., description="Network name")
    address: str = Field(..., description="Address to query")


# Network Config Models
class AddNetworkRequest(BaseModel):
    network_name: str = Field(..., description="Unique network identifier (e.g., 'sepolia')")
    chain_id: int = Field(..., description="Chain ID (e.g., 11155111 for Sepolia)")
    rpc_url: str = Field(..., description="RPC endpoint URL")
    entrypoint_address: Optional[str] = Field(None, description="EntryPoint contract address")
    factory_address: Optional[str] = Field(None, description="Factory contract address")
    name: Optional[str] = Field(None, description="Human-readable network name")


class UpdateNetworkRequest(BaseModel):
    network_name: str = Field(..., description="Network identifier to update")
    rpc_url: Optional[str] = Field(None, description="New RPC endpoint URL")
    entrypoint_address: Optional[str] = Field(None, description="New EntryPoint address")
    factory_address: Optional[str] = Field(None, description="New Factory address")
    name: Optional[str] = Field(None, description="New network name")


class RemoveNetworkRequest(BaseModel):
    network_name: str = Field(..., description="Network identifier to remove")


# ============================================
# Router
# ============================================

router = APIRouter()


# ============================================
# Authentication Endpoints (No session required)
# ============================================

@router.get("/auth/status")
async def auth_status():
    """
    Check wallet initialization and unlock status.

    Returns:
        - initialized: Whether keystore exists
        - unlocked: Whether wallet is currently unlocked
        - eoa_address: EOA address if initialized
    """
    return {
        "initialized": singleton.is_initialized(),
        "unlocked": singleton.is_unlocked(),
        "eoa_address": singleton.get_eoa_address()
    }


@router.post("/auth/unlock")
async def unlock_wallet(request: UnlockRequest):
    """
    Unlock wallet with password and create session.

    Returns session token for subsequent requests.
    """
    try:
        address = singleton.init_from_keystore(request.password)
        session_token = SessionManager.create_session(request.password)

        wallet = singleton.get_wallet()

        return {
            "success": True,
            "session_token": session_token,
            "eoa_address": address,
            "expires_in": 1800,  # 30 minutes
            "networks": wallet.list_networks()
        }
    except FileNotFoundError:
        raise HTTPException(404, "Keystore not found. Please initialize wallet first.")
    # except Exception as e:
    #     raise HTTPException(400, f"Failed to unlock wallet: {str(e)}")


@router.post("/auth/lock")
async def lock_wallet(session_token: str = Depends(verify_session_token)):
    """
    Lock wallet and destroy session.
    """
    SessionManager.destroy_session(session_token)
    singleton.lock_wallet_singleton()

    return {
        "success": True,
        "message": "Wallet locked successfully"
    }


@router.get("/auth/session-info")
async def session_info(session_token: str = Depends(verify_session_token)):
    """
    Get current session information.
    """
    info = SessionManager.get_session_info(session_token)

    if not info:
        raise HTTPException(401, "Session not found")

    return {
        "success": True,
        "session_info": info
    }


# ============================================
# Initialization Endpoints (No session required)
# ============================================

@router.post("/init/create")
async def create_new_wallet(request: CreateWalletRequest):
    """
    Create new wallet with new private key.

    Automatically unlocks and returns session token.
    """
    try:
        address = singleton.init_create_new(request.password)
        print(singleton.get_wallet().get_config())
        session_token = SessionManager.create_session(request.password)

        return {
            "success": True,
            "eoa_address": address,
            "session_token": session_token,
            "message": "Wallet created successfully"
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to create wallet: {str(e)}")


@router.post("/init/import-private-key")
async def import_private_key(request: ImportPrivateKeyRequest):
    """
    Import wallet from private key.

    ⚠️ SECURITY WARNING:
    This endpoint transmits private key over the network and should ONLY be used:
    - In development/testing environments
    - Over HTTPS in production
    - For local deployment where API and client are on the same machine

    For production use, consider:
    - Using keystore file import instead
    - Implementing client-side encryption
    - Running Agent layer locally with signature-only API calls

    Automatically unlocks and returns session token.
    """
    import os

    # Check if running in production
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(
            403,
            "Private key import is disabled in production for security. "
            "Use keystore import or local Agent instead."
        )

    try:
        address = singleton.init_import_private_key(request.private_key, request.password)
        session_token = SessionManager.create_session(request.password)

        return {
            "success": True,
            "eoa_address": address,
            "session_token": session_token,
            "message": "Private key imported successfully",
            "warning": "⚠️ Private key transmitted over network - use only for testing!"
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to import private key: {str(e)}")
@router.post("/init/import-keystore")
async def import_keystore(request: ImportKeystoreRequest):
    """
    Import wallet from keystore file.

    Automatically unlocks and returns session token.
    """
    try:
        address = singleton.init_import_keystore(request.keystore_path, request.password)
        session_token = SessionManager.create_session(request.password)

        return {
            "success": True,
            "eoa_address": address,
            "session_token": session_token,
            "message": "Keystore imported successfully"
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to import keystore: {str(e)}")


# ============================================
# Account Management Endpoints (Session required)
# ============================================

@router.post("/accounts")
async def create_account(
    request: CreateAccountRequest,
    session_token: str = Depends(verify_session_token)
):
    """
    Create new smart contract account.

    If contract_address not provided, calculates counterfactual address.
    Account is not deployed until first UserOperation.
    """
    try:
        wallet = singleton.get_wallet()

        account = wallet.add_account(
            network_name=request.network_name,
            owners=request.owners,
            threshold=request.threshold,
            name=request.name,
            guardians=request.guardians,
            guardian_threshold=request.guardian_threshold,
            salt=request.salt
        )

        return {
            "success": True,
            "account_address": account.contract_address,
            "network_name": request.network_name,
            "name": account.name,
            "owners": account.owners,
            "threshold": account.threshold,
            "deployed": account.is_deployed(),
            "balance": account.get_balance()
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to create account: {str(e)}")


@router.get("/accounts")
async def list_accounts(session_token: str = Depends(verify_session_token)):
    """
    List all accounts in wallet.
    """
    try:
        wallet = singleton.get_wallet()
        summary = wallet.summary()

        return {
            "success": True,
            "eoa_address": summary["eoa_address"],
            "networks": wallet.list_networks(),
            "accounts": summary["aa_accounts"],
            "eoa_balances": summary["eoa_balances"]
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to list accounts: {str(e)}")


@router.get("/accounts/{network_name}/{account_address}")
async def get_account_details(
    network_name: str,
    account_address: str,
    session_token: str = Depends(verify_session_token)
):
    """
    Get detailed information about a specific account.
    """
    try:
        wallet = singleton.get_wallet()
        account = wallet.get_account(network_name, account_address)

        return {
            "success": True,
            "account_address": account.contract_address,
            "network_name": network_name,
            "name": account.name,
            "owners": account.owners,
            "threshold": account.threshold,
            "guardians": account.guardians,
            "guardian_threshold": account.guardian_threshold,
            "deployed": account.is_deployed(),
            "balance": account.get_balance(),
            "nonce": account.get_nonce(),
            "chain_id": account.get_chain_id()
        }
    except KeyError:
        raise HTTPException(404, f"Account {account_address} not found on {network_name}")
    except Exception as e:
        raise HTTPException(500, f"Failed to get account details: {str(e)}")


@router.delete("/accounts")
async def remove_account(
    request: RemoveAccountRequest,
    session_token: str = Depends(verify_session_token)
):
    """
    Remove account from wallet.
    """
    try:
        wallet = singleton.get_wallet()
        wallet.remove_account(request.network_name, request.account_address)

        return {
            "success": True,
            "message": f"Account {request.account_address} removed from {request.network_name}"
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to remove account: {str(e)}")


@router.patch("/accounts")
async def update_account(
    request: UpdateAccountRequest,
    session_token: str = Depends(verify_session_token)
):
    """
    Update account configuration (name, bundler_url, paymaster_url, etc).

    Only non-None fields will be updated.
    """
    try:
        wallet = singleton.get_wallet()

        # Build update dict with only non-None values
        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.bundler_url is not None:
            update_data['bundler_url'] = request.bundler_url
        if request.paymaster_url is not None:
            update_data['paymaster_url'] = request.paymaster_url

        if not update_data:
            raise HTTPException(400, "No fields to update")

        # Update account
        updated_account = wallet.update_account(
            network_name=request.network_name,
            contract_address=request.account_address,
            **update_data
        )

        return {
            "success": True,
            "message": "Account updated successfully",
            "account": {
                "address": updated_account.contract_address,
                "name": updated_account.name,
                "network_name": updated_account.network_name,
                "bundler_url": updated_account.bundler_url,
                "paymaster_url": updated_account.paymaster_url
            }
        }
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, f"Failed to update account: {str(e)}")


# ============================================
# Transaction Endpoints (Session required)
# ============================================

@router.post("/userop/send")
async def send_user_operation(
    request: SendUserOpRequest,
    session_token: str = Depends(verify_session_token)
):
    """
    Send UserOperation (automatically routes to bundler or aggregator).

    For single-sig accounts: sends directly to bundler
    For multi-sig accounts: sends to aggregation service
    """
    try:
        wallet = singleton.get_wallet()
        km = singleton.get_key_manager()

        # Get account
        account = wallet.get_account(request.network_name, request.account_address)

        # Build callData
        data_bytes = bytes.fromhex(request.data[2:]) if request.data and request.data != "0x" else b''
        call_data = account.encode_execute_call(
            target=request.target,
            value=request.value,
            data=data_bytes
        )

        # Build UserOp
        user_op = account.build_user_operation(call_data=call_data)

        # Sign
        user_op_hash = account.get_user_op_hash(user_op)
        signature = km.sign_userop(user_op_hash)
        user_op['signature'] = '0x' + signature.hex()

        # Send (auto-routes)
        tx_hash = account.send_user_operation(user_op)

        return {
            "success": True,
            "transaction_hash": tx_hash,
            "is_multisig": account.threshold > 1,
            "account_address": account.contract_address,
            "network_name": request.network_name
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to send UserOperation: {str(e)}")


@router.post("/transaction/send")
async def send_eoa_transaction(
    request: SendEOATransactionRequest,
    session_token: str = Depends(verify_session_token)
):
    """
    Send EOA transaction (regular Ethereum transaction).
    """
    try:
        wallet = singleton.get_wallet()

        data_bytes = bytes.fromhex(request.data[2:]) if request.data and request.data != "0x" else b''

        receipt = wallet.send_transaction(
            network_name=request.network_name,
            to=request.to,
            value=request.value,
            data=data_bytes,
            gas=request.gas
        )

        return {
            "success": True,
            "transaction_hash": receipt['transactionHash'].hex(),
            "block_number": receipt['blockNumber'],
            "gas_used": receipt['gasUsed'],
            "status": receipt['status']
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to send transaction: {str(e)}")


@router.post("/message/sign")
async def sign_message(
    request: SignMessageRequest,
    session_token: str = Depends(verify_session_token)
):
    """
    Sign a message with EOA private key.
    """
    try:
        wallet = singleton.get_wallet()
        signature = wallet.send_message(request.message)

        return {
            "success": True,
            "message": request.message,
            "signature": signature.signature.hex(),
            "signer": wallet.get_eoa_address()
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to sign message: {str(e)}")


# ============================================
# Query Endpoints (Session required)
# ============================================

@router.get("/balance/{network_name}/{address}")
async def get_balance(
    network_name: str,
    address: str,
    session_token: str = Depends(verify_session_token)
):
    """
    Get ETH balance of any address.
    """
    try:
        wallet = singleton.get_wallet()

        # Check if it's an AA account
        try:
            account = wallet.get_account(network_name, address)
            balance = account.get_balance()
            is_aa = True
            deployed = account.is_deployed()
        except:
            # Not an AA account, query as regular address
            from web3 import Web3
            config = Config()
            rpc_url = config.get_rpc_url(network_name)
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            balance = w3.eth.get_balance(address)
            is_aa = False
            deployed = None

        return {
            "success": True,
            "address": address,
            "network_name": network_name,
            "balance_wei": balance,
            "balance_eth": balance / 10**18,
            "is_aa_account": is_aa,
            "deployed": deployed
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to get balance: {str(e)}")


@router.get("/nonce/{network_name}/{account_address}")
async def get_nonce(
    network_name: str,
    account_address: str,
    session_token: str = Depends(verify_session_token)
):
    """
    Get nonce for smart account.
    """
    try:
        wallet = singleton.get_wallet()
        account = wallet.get_account(network_name, account_address)
        nonce = account.get_nonce()

        return {
            "success": True,
            "account_address": account_address,
            "network_name": network_name,
            "nonce": nonce
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to get nonce: {str(e)}")


@router.get("/wallet/summary")
async def wallet_summary(session_token: str = Depends(verify_session_token)):
    """
    Get complete wallet summary.
    """
    try:
        wallet = singleton.get_wallet()
        summary = wallet.summary()

        return {
            "success": True,
            **summary
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get wallet summary: {str(e)}")


# ============================================
# Network Configuration Endpoints
# ============================================

@router.get("/networks")
async def list_networks():
    """
    List all configured networks.

    No session required - public endpoint.
    """
    try:
        config = singleton.get_wallet().get_config()
        networks = config.list_networks()

        network_info = []
        for network in networks:
            network_config = config.get_network(network)
            network_info.append({
                "network_name": network,
                "name": network_config.name,
                "chain_id": network_config.chain_id,
                "rpc_url": network_config.rpc_url,
                "entry_point": network_config.entrypoint_address,
                "factory": network_config.factory_address
            })

        return {
            "success": True,
            "networks": network_info
        }
    except Exception as e:
        print(f"Failed to get networks: {str(e)}")
        raise HTTPException(500, f"Failed to list networks: {str(e)}")


@router.post("/networks")
async def add_network(
    request: AddNetworkRequest,
    session_token: str = Depends(verify_session_token)
):
    """
    Add a new network configuration.

    Automatically saves to config.json.
    """
    try:
        config = singleton.get_wallet().get_config()

        # Create network config
        network_config = NetworkConfig(
            chain_id=request.chain_id,
            rpc_url=request.rpc_url,
            entrypoint_address=request.entrypoint_address,
            factory_address=request.factory_address,
            name=request.name
        )

        # Add and save
        config.add_network(request.network_name, network_config, save=True)

        return {
            "success": True,
            "message": f"Network '{request.network_name}' added successfully",
            "network": {
                "network_name": request.network_name,
                "name": network_config.name,
                "chain_id": network_config.chain_id,
                "rpc_url": network_config.rpc_url,
                "entry_point": network_config.entrypoint_address,
                "factory": network_config.factory_address
            }
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to add network: {str(e)}")


@router.patch("/networks")
async def update_network(
    request: UpdateNetworkRequest,
    session_token: str = Depends(verify_session_token)
):
    """
    Update network configuration.

    Only non-None fields will be updated.
    Automatically saves to config.json.
    """
    try:
        config = singleton.get_wallet().get_config()

        # Get existing network
        network = config.get_network(request.network_name)

        # Update fields
        if request.rpc_url is not None:
            network.rpc_url = request.rpc_url
        if request.entrypoint_address is not None:
            network.entrypoint_address = request.entrypoint_address
        if request.factory_address is not None:
            network.factory_address = request.factory_address
        if request.name is not None:
            network.name = request.name

        # Save changes
        config.save_to_json()

        return {
            "success": True,
            "message": f"Network '{request.network_name}' updated successfully",
            "network": {
                "network_name": request.network_name,
                "name": network.name,
                "chain_id": network.chain_id,
                "rpc_url": network.rpc_url,
                "entry_point": network.entrypoint_address,
                "factory": network.factory_address
            }
        }
    except KeyError:
        raise HTTPException(404, f"Network '{request.network_name}' not found")
    except Exception as e:
        raise HTTPException(400, f"Failed to update network: {str(e)}")


@router.delete("/networks")
async def remove_network(
    request: RemoveNetworkRequest,
    session_token: str = Depends(verify_session_token)
):
    """
    Remove a network configuration.

    Automatically saves to config.json.
    """
    try:
        config = singleton.get_wallet().get_config()

        # Check if network exists
        if not config.has_network(request.network_name):
            raise HTTPException(404, f"Network '{request.network_name}' not found")

        # Remove and save
        config.remove_network(request.network_name, save=True)

        return {
            "success": True,
            "message": f"Network '{request.network_name}' removed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Failed to remove network: {str(e)}")

