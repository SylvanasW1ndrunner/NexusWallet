"""
Verification logic for Transaction Aggregation Service

Handles signature verification, nonce validation, and access control.
"""
from typing import List, Optional
from web3 import Web3
from eth_account import Account as EthAccount
from eth_account.messages import encode_defunct

from backend.service.redis_client import redis_client
from backend.config.config import Config


def verify_signature(
    user_op_hash: bytes,
    signature: bytes,
    signer_address: str,
    account_owners: List[str]
) -> bool:
    """
    Verify that a signature is valid for a UserOperation hash

    Args:
        user_op_hash: 32-byte UserOperation hash
        signature: 65-byte ECDSA signature
        signer_address: Expected signer address (checksum format)
        account_owners: List of valid account owner addresses

    Returns:
        True if signature is valid, False otherwise

    Raises:
        ValueError: If signature format is invalid
    """
    # Validate signature length
    if len(signature) != 65:
        raise ValueError(f"Invalid signature length: {len(signature)}. Expected 65 bytes.")

    # Check if signer is an account owner
    signer_checksum = Web3.to_checksum_address(signer_address)
    owners_checksum = [Web3.to_checksum_address(addr) for addr in account_owners]

    if signer_checksum not in owners_checksum:
        return False

    try:
        # EIP-191 message encoding
        message = encode_defunct(primitive=user_op_hash)

        # Recover signer address from signature
        recovered_address = EthAccount.recover_message(message, signature=signature)

        # Verify recovered address matches expected signer
        return Web3.to_checksum_address(recovered_address) == signer_checksum

    except Exception as e:
        print(f"Signature verification error: {e}")
        return False


def verify_nonce(
    user_op: dict,
    smart_account_address: str,
    chain_id: int,
    network_name: str
) -> bool:
    """
    Verify that UserOperation nonce is correct

    Args:
        user_op: UserOperation dict (unpacked format)
        smart_account_address: Smart account address
        chain_id: Chain ID
        network_name: Network name (e.g., "sepolia")

    Returns:
        True if nonce is valid, False otherwise
    """
    try:
        # Get nonce from UserOp
        user_op_nonce = int(user_op['nonce'], 16)

        # Get current nonce from EntryPoint
        from backend.utils.account import Account

        # Create temporary Account instance to query nonce
        # Note: We only need it for nonce query, so minimal init
        temp_account = Account(
            network_name=network_name,
            contract_address=smart_account_address,
            owners=[],  # Not needed for nonce query
            threshold=1  # Not needed for nonce query
        )

        # Get nonce key (upper 192 bits of nonce)
        nonce_key = user_op_nonce >> 64

        # Get current nonce from EntryPoint
        current_nonce = temp_account.get_nonce(key=nonce_key)

        # Verify nonce matches
        return user_op_nonce == current_nonce

    except Exception as e:
        print(f"Nonce verification error: {e}")
        return False


def check_duplicate_signature(
    existing_signatures: dict,
    signer_address: str
) -> bool:
    """
    Check if signer has already signed the transaction

    Args:
        existing_signatures: Dictionary of existing signatures
        signer_address: Address to check

    Returns:
        True if signer has already signed (duplicate), False otherwise
    """
    if not existing_signatures:
        return False

    signer_checksum = Web3.to_checksum_address(signer_address)
    return signer_checksum in existing_signatures


def get_account_owners(
    smart_account_address: str,
    chain_id: int,
    network_name: str
) -> List[str]:
    """
    Get account owners list with Redis caching

    Priority:
    1. Redis cache
    2. Query from on-chain contract
    3. Cache result to Redis

    Args:
        smart_account_address: Smart account address
        chain_id: Chain ID
        network_name: Network name (e.g., "sepolia")

    Returns:
        List of owner addresses (checksum format)
    """
    # Check Redis cache first
    cached_owners = redis_client.get_account_owners(smart_account_address, chain_id)
    if cached_owners is not None:
        return cached_owners

    # Query from on-chain contract
    try:
        from backend.utils.account import Account

        # Create temporary Account instance to query owners
        temp_account = Account(
            network_name=network_name,
            contract_address=smart_account_address,
            owners=[],  # Will be fetched
            threshold=1  # Not needed for query
        )

        # Get owners from contract
        owners = temp_account.get_owners()

        # Ensure checksum format
        owners_checksum = [Web3.to_checksum_address(addr) for addr in owners]

        # Cache to Redis
        redis_client.set_account_owners(smart_account_address, chain_id, owners_checksum)

        return owners_checksum

    except Exception as e:
        print(f"Error fetching account owners: {e}")
        raise ValueError(f"Failed to fetch account owners for {smart_account_address}")


def get_network_name_by_chain_id(chain_id: int) -> str:
    """
    Get network name from chain ID

    Args:
        chain_id: Chain ID

    Returns:
        Network name

    Raises:
        ValueError: If chain ID is not supported
    """
    # Chain ID to network name mapping
    chain_mapping = {
        11155111: 'sepolia',
        1: 'mainnet',
        5: 'goerli',
        137: 'polygon',
        80001: 'mumbai',
        31337: 'local'
    }

    network_name = chain_mapping.get(chain_id)
    if not network_name:
        raise ValueError(f"Unsupported chain ID: {chain_id}")

    return network_name


def validate_user_operation_format(user_op: dict) -> bool:
    """
    Validate UserOperation has all required fields

    Args:
        user_op: UserOperation dict (unpacked format)

    Returns:
        True if format is valid

    Raises:
        ValueError: If required fields are missing
    """
    required_fields = [
        'sender',
        'nonce',
        'callData',
        'callGasLimit',
        'verificationGasLimit',
        'preVerificationGas',
        'maxFeePerGas',
        'maxPriorityFeePerGas',
        'signature'
    ]

    for field in required_fields:
        if field not in user_op:
            raise ValueError(f"Missing required field: {field}")

    return True
