"""
Database schema for Transaction Aggregation Service

Defines SQLAlchemy ORM models for multi-signature transaction storage.
"""
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON,
    Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


Base = declarative_base()


class MultisigTransaction(Base):
    """
    Multi-signature transaction model

    Stores pending and completed multi-signature transactions with
    incremental signature collection.
    """
    __tablename__ = 'multisig_transactions'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Account and network information
    smart_account_address = Column(String(42), nullable=False, index=True)
    chain_id = Column(Integer, nullable=False)
    chain_name = Column(String(50), nullable=False)

    # Transaction identification
    transaction_hash = Column(String(66), nullable=False, unique=True, index=True)

    # UserOperation data (unpacked format)
    user_operation = Column(JSON, nullable=False)

    # Signature requirements
    threshold = Column(Integer, nullable=False)

    # Collected signatures: {"signer_address": "0x...signature"}
    signatures = Column(JSON, nullable=False, default=dict)

    # Status tracking
    creation_time = Column(DateTime, nullable=False, default=func.now())
    status = Column(String(20), nullable=False, default='Pending', index=True)
    last_signature_time = Column(DateTime, nullable=True)

    # Bundler submission result
    bundler_tx_hash = Column(String(66), nullable=True)

    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_account_status', 'smart_account_address', 'status'),
        UniqueConstraint('transaction_hash', name='uq_transaction_hash'),
    )

    def __repr__(self):
        return (
            f"<MultisigTransaction "
            f"id={self.id} "
            f"account={self.smart_account_address} "
            f"status={self.status} "
            f"signatures={len(self.signatures)}/{self.threshold}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization

        Returns:
            Dictionary representation of the transaction
        """
        return {
            'id': self.id,
            'smart_account_address': self.smart_account_address,
            'chain_id': self.chain_id,
            'chain_name': self.chain_name,
            'transaction_hash': self.transaction_hash,
            'user_operation': self.user_operation,
            'threshold': self.threshold,
            'signatures': self.signatures,
            'signatures_collected': len(self.signatures),
            'creation_time': self.creation_time.isoformat() if self.creation_time else None,
            'status': self.status,
            'last_signature_time': self.last_signature_time.isoformat() if self.last_signature_time else None,
            'bundler_tx_hash': self.bundler_tx_hash
        }

    @property
    def signatures_collected(self) -> int:
        """Number of signatures collected"""
        return len(self.signatures) if self.signatures else 0

    @property
    def is_ready_for_submission(self) -> bool:
        """Check if transaction has enough signatures for submission"""
        return self.signatures_collected >= self.threshold

    @property
    def is_pending(self) -> bool:
        """Check if transaction is still pending"""
        return self.status == 'Pending'

    def has_signer(self, signer_address: str) -> bool:
        """
        Check if a specific address has already signed

        Args:
            signer_address: Address to check (checksum format)

        Returns:
            True if address has signed, False otherwise
        """
        if not self.signatures:
            return False
        return signer_address in self.signatures

    def add_signature(self, signer_address: str, signature: str):
        """
        Add a signature to the transaction

        Args:
            signer_address: Address of the signer (checksum format)
            signature: Hex-encoded signature (0x...)

        Raises:
            ValueError: If signer has already signed
        """
        if self.has_signer(signer_address):
            raise ValueError(f"Address {signer_address} has already signed this transaction")

        if self.signatures is None:
            self.signatures = {}

        self.signatures[signer_address] = signature
        self.last_signature_time = datetime.utcnow()

    def get_concatenated_signatures(self) -> str:
        """
        Get all signatures concatenated in sorted order

        Returns:
            Hex string of concatenated signatures (sorted by signer address)
        """
        if not self.signatures:
            return '0x'

        # Sort by signer address for deterministic ordering
        sorted_signers = sorted(self.signatures.keys())

        # Concatenate signatures (each is 65 bytes)
        all_sigs = []
        for signer in sorted_signers:
            sig = self.signatures[signer]
            # Remove 0x prefix if present
            if sig.startswith('0x'):
                sig = sig[2:]
            all_sigs.append(sig)

        concatenated = '0x' + ''.join(all_sigs)
        return concatenated
