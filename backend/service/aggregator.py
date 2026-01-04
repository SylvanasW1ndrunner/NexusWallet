"""
Core aggregation logic for multi-signature transactions

Handles transaction submission, signature collection, and automatic
bundler submission when threshold is reached.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from web3 import Web3

from backend.service.database import get_db_session
from backend.service.schema import MultisigTransaction
from backend.service.redis_client import redis_client
from backend.service.verification import (
    verify_signature,
    verify_nonce,
    check_duplicate_signature,
    get_account_owners,
    get_network_name_by_chain_id,
    validate_user_operation_format
)


def submit_multisig_transaction(
    smart_account_address: str,
    chain_id: int,
    chain_name: str,
    user_operation: dict,
    threshold: int,
    initial_signature: str,
    signer_address: str
) -> dict:
    """
    Submit a new multi-signature transaction to aggregation service

    Workflow:
    1. Calculate transaction_hash (UserOp hash)
    2. Check if already exists (prevent duplicates)
    3. Verify signer is account owner
    4. Verify nonce is correct
    5. Verify signature validity
    6. Insert into database
    7. Update Redis cache
    8. Return transaction hash

    Args:
        smart_account_address: Smart account address (checksum format)
        chain_id: Chain ID
        chain_name: Chain name (e.g., "sepolia")
        user_operation: Complete UserOperation (unpacked format)
        threshold: Number of signatures required
        initial_signature: First signer's signature (hex string)
        signer_address: First signer's address

    Returns:
        Dict with transaction details:
        {
            "success": true,
            "transaction_hash": "0x...",
            "signatures_collected": 1,
            "threshold": 2,
            "status": "Pending"
        }

    Raises:
        ValueError: If validation fails
    """
    # Validate UserOperation format
    validate_user_operation_format(user_operation)

    # Ensure checksum addresses
    smart_account_address = Web3.to_checksum_address(smart_account_address)
    signer_address = Web3.to_checksum_address(signer_address)

    # Calculate transaction hash from UserOp
    from backend.utils.account import Account

    # Create temporary account to calculate hash
    temp_account = Account(
        network_name=chain_name,
        contract_address=smart_account_address,
        owners=[],
        threshold=1
    )
    user_op_hash = temp_account.get_user_op_hash(user_operation)
    transaction_hash = '0x' + user_op_hash.hex()

    # Check if transaction already exists
    with get_db_session() as session:
        existing = session.query(MultisigTransaction).filter_by(
            transaction_hash=transaction_hash
        ).first()

        if existing:
            raise ValueError(
                f"Transaction {transaction_hash} already exists with status: {existing.status}"
            )

        # Get account owners
        network_name = get_network_name_by_chain_id(chain_id)
        account_owners = get_account_owners(smart_account_address, chain_id, network_name)

        # Verify signer is an owner
        if signer_address not in account_owners:
            raise ValueError(
                f"Signer {signer_address} is not an owner of account {smart_account_address}"
            )

        # Verify nonce
        if not verify_nonce(user_operation, smart_account_address, chain_id, network_name):
            raise ValueError(
                f"Invalid nonce in UserOperation. "
                f"Nonce {user_operation['nonce']} does not match on-chain nonce."
            )

        # Verify initial signature
        signature_bytes = bytes.fromhex(initial_signature[2:] if initial_signature.startswith('0x') else initial_signature)

        if not verify_signature(user_op_hash, signature_bytes, signer_address, account_owners):
            raise ValueError(
                f"Invalid signature from {signer_address}"
            )

        # Create new transaction record
        new_tx = MultisigTransaction(
            smart_account_address=smart_account_address,
            chain_id=chain_id,
            chain_name=chain_name,
            transaction_hash=transaction_hash,
            user_operation=user_operation,
            threshold=threshold,
            signatures={signer_address: initial_signature},
            status='Pending',
            creation_time=datetime.utcnow(),
            last_signature_time=datetime.utcnow()
        )

        session.add(new_tx)
        session.commit()

        # Update Redis cache
        redis_client.invalidate_pending_txs(smart_account_address, chain_id)
        redis_client.set_tx_detail(transaction_hash, new_tx.to_dict())

        return {
            "success": True,
            "transaction_hash": transaction_hash,
            "signatures_collected": 1,
            "threshold": threshold,
            "status": "Pending"
        }


def add_signature_to_transaction(
    transaction_hash: str,
    signature: str,
    signer_address: str
) -> dict:
    """
    Add a signature to an existing transaction

    Workflow:
    1. Fetch transaction from database
    2. Verify transaction is Pending
    3. Verify signer is account owner
    4. Check if signer already signed
    5. Verify signature validity
    6. Add signature to database
    7. Check if threshold reached
    8. If threshold reached: auto-submit to bundler
    9. Update Redis cache
    10. Return result

    Args:
        transaction_hash: UserOperation hash
        signature: Signer's signature (hex string)
        signer_address: Signer's address

    Returns:
        Dict with transaction status:
        {
            "success": true,
            "transaction_hash": "0x...",
            "signatures_collected": 2,
            "threshold": 2,
            "status": "Success" or "Pending",
            "bundler_tx_hash": "0x..." (if submitted)
        }

    Raises:
        ValueError: If validation fails or transaction not found
    """
    # Ensure checksum address
    signer_address = Web3.to_checksum_address(signer_address)

    with get_db_session() as session:
        # Fetch transaction
        tx = session.query(MultisigTransaction).filter_by(
            transaction_hash=transaction_hash
        ).first()

        if not tx:
            raise ValueError(f"Transaction {transaction_hash} not found")

        # Verify transaction is still pending
        if tx.status != 'Pending':
            raise ValueError(
                f"Transaction {transaction_hash} is not pending (status: {tx.status})"
            )

        # Get account owners
        network_name = get_network_name_by_chain_id(tx.chain_id)
        account_owners = get_account_owners(tx.smart_account_address, tx.chain_id, network_name)

        # Verify signer is an owner
        if signer_address not in account_owners:
            raise ValueError(
                f"Signer {signer_address} is not an owner of account {tx.smart_account_address}"
            )

        # Check for duplicate signature
        if check_duplicate_signature(tx.signatures, signer_address):
            raise ValueError(
                f"Signer {signer_address} has already signed this transaction"
            )

        # Verify signature validity
        user_op_hash = bytes.fromhex(transaction_hash[2:])
        signature_bytes = bytes.fromhex(signature[2:] if signature.startswith('0x') else signature)

        if not verify_signature(user_op_hash, signature_bytes, signer_address, account_owners):
            raise ValueError(
                f"Invalid signature from {signer_address}"
            )

        # Add signature
        tx.add_signature(signer_address, signature)

        # Check if threshold reached
        bundler_tx_hash = None
        if tx.is_ready_for_submission:
            try:
                # Auto-submit to bundler
                bundler_tx_hash = auto_submit_when_threshold_reached(
                    tx=tx,
                    chain_name=tx.chain_name
                )
                tx.status = 'Success'
                tx.bundler_tx_hash = bundler_tx_hash
            except Exception as e:
                print(f"Auto-submit failed: {e}")
                tx.status = 'Fail'
                raise ValueError(f"Failed to submit to bundler: {e}")

        session.commit()

        # Update Redis cache
        redis_client.invalidate_tx_detail(transaction_hash)
        redis_client.invalidate_pending_txs(tx.smart_account_address, tx.chain_id)

        return {
            "success": True,
            "transaction_hash": transaction_hash,
            "signatures_collected": tx.signatures_collected,
            "threshold": tx.threshold,
            "status": tx.status,
            "bundler_tx_hash": bundler_tx_hash
        }


def auto_submit_when_threshold_reached(
    tx: MultisigTransaction,
    chain_name: str
) -> str:
    """
    Automatically submit transaction to bundler when threshold is reached

    Workflow:
    1. Verify signatures count >= threshold
    2. Get all signatures sorted by signer address
    3. Concatenate signatures
    4. Update user_operation['signature']
    5. Submit to Pimlico bundler
    6. Return bundler transaction hash

    Args:
        tx: MultisigTransaction instance
        chain_name: Chain name for bundler

    Returns:
        Bundler transaction hash

    Raises:
        ValueError: If submission fails
    """
    if not tx.is_ready_for_submission:
        raise ValueError(
            f"Transaction not ready: {tx.signatures_collected}/{tx.threshold} signatures"
        )

    # Get concatenated signatures (sorted by signer address)
    concatenated_signatures = tx.get_concatenated_signatures()

    # Update UserOperation signature
    user_operation = tx.user_operation.copy()
    user_operation['signature'] = concatenated_signatures

    # Submit to bundler
    from backend.utils.PimlicoBundlerClient import PimlicoBundler
    from backend.service.config import config
    from backend.config.config import Config

    # Get EntryPoint address
    config_obj = Config()
    entry_point = config_obj.get_entry_point(chain_name)

    # Create bundler client
    bundler = PimlicoBundler(
        api_key=config.pimlico_api_key,
        chain_name=chain_name
    )

    try:
        # Send UserOperation to bundler
        bundler_tx_hash = bundler.send_user_operation(
            user_op=user_operation,
            entry_point=entry_point
        )

        print(f"✓ Transaction submitted to bundler: {bundler_tx_hash}")
        return bundler_tx_hash

    except Exception as e:
        print(f"✗ Bundler submission failed: {e}")
        raise ValueError(f"Bundler submission failed: {e}")


# ============================================
# Query Functions
# ============================================

def get_transaction(transaction_hash: str) -> Optional[dict]:
    """
    Get transaction details by hash

    Args:
        transaction_hash: UserOperation hash

    Returns:
        Transaction details dict, or None if not found
    """
    # Check cache first
    cached = redis_client.get_tx_detail(transaction_hash)
    if cached:
        return cached

    # Query from database
    with get_db_session() as session:
        tx = session.query(MultisigTransaction).filter_by(
            transaction_hash=transaction_hash
        ).first()

        if tx:
            tx_dict = tx.to_dict()
            redis_client.set_tx_detail(transaction_hash, tx_dict)
            return tx_dict

    return None


def get_pending_transactions(
    account_address: str,
    chain_id: int,
    signer_address: Optional[str] = None
) -> List[dict]:
    """
    Get pending transactions for an account

    Args:
        account_address: Smart account address
        chain_id: Chain ID
        signer_address: Optional signer address to check if already signed

    Returns:
        List of pending transaction dicts
    """
    account_address = Web3.to_checksum_address(account_address)

    with get_db_session() as session:
        txs = session.query(MultisigTransaction).filter_by(
            smart_account_address=account_address,
            chain_id=chain_id,
            status='Pending'
        ).order_by(MultisigTransaction.creation_time.desc()).all()

        result = []
        for tx in txs:
            tx_dict = tx.to_dict()

            # Add 'already_signed' flag if signer_address provided
            if signer_address:
                signer_checksum = Web3.to_checksum_address(signer_address)
                tx_dict['already_signed'] = tx.has_signer(signer_checksum)

            result.append(tx_dict)

        return result


def get_transaction_status(transaction_hash: str) -> Optional[dict]:
    """
    Get transaction status summary

    Args:
        transaction_hash: UserOperation hash

    Returns:
        Status dict with key fields, or None if not found
    """
    tx = get_transaction(transaction_hash)
    if not tx:
        return None

    return {
        "success": True,
        "transaction_hash": transaction_hash,
        "status": tx['status'],
        "signatures_collected": tx['signatures_collected'],
        "threshold": tx['threshold'],
        "bundler_tx_hash": tx['bundler_tx_hash'],
        "creation_time": tx['creation_time'],
        "last_signature_time": tx['last_signature_time']
    }
