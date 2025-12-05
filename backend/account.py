"""
Account class for managing smart contract account operations.
Handles transaction building, UserOp construction, and message signing.
"""
from typing import Optional, List, Dict, Any
from web3 import Web3
from eth_account import Account as EthAccount
from eth_utils import to_checksum_address
import time


class Account:
    """
    Represents a smart contract account on a specific chain.

    Each Account instance manages one smart contract account and can:
    - Build regular transactions
    - Construct UserOperations for ERC-4337
    - Sign messages via KeyManager
    - Configure custom Bundler and Paymaster
    """

    def __init__(
        self,
        network_name: str,
        contract_address: str,
        owners: List[str],
        threshold: int,
        guardians: Optional[List[str]] = None,
        guardian_threshold: int = 0,
        bundler_url: Optional[str] = None,
        paymaster_url: Optional[str] = None,
        rpc_url: Optional[str] = None
    ):
        """
        Initialize an Account instance.

        Args:
            network_name: Name of the network (e.g., "sepolia")
            contract_address: Address of the deployed smart contract account
            owners: List of owner addresses
            threshold: Signature threshold for multi-sig
            guardians: List of guardian addresses for social recovery
            guardian_threshold: Guardian signature threshold
            bundler_url: Custom bundler RPC endpoint (optional)
            paymaster_url: Custom paymaster RPC endpoint (optional)
            rpc_url: Custom RPC URL, overrides Config if provided
        """
        self.network_name = network_name
        self.contract_address = to_checksum_address(contract_address)
        self.owners = [to_checksum_address(addr) for addr in owners]
        self.threshold = threshold
        self.guardians = [to_checksum_address(addr) for addr in guardians] if guardians else []
        self.guardian_threshold = guardian_threshold

        # Custom service URLs
        self.bundler_url = bundler_url
        self.paymaster_url = paymaster_url
        self._custom_rpc_url = rpc_url

        # Web3 instance (lazy initialized)
        self._w3: Optional[Web3] = None

        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """Validate account configuration."""
        if self.threshold <= 0 or self.threshold > len(self.owners):
            raise ValueError(f"Invalid threshold: {self.threshold} for {len(self.owners)} owners")

        if self.guardians and (self.guardian_threshold <= 0 or self.guardian_threshold > len(self.guardians)):
            raise ValueError(f"Invalid guardian threshold: {self.guardian_threshold}")

        if not self.guardians and self.guardian_threshold > 0:
            raise ValueError("Guardian threshold must be 0 when no guardians")

    @property
    def w3(self) -> Web3:
        """Lazy-load Web3 instance."""
        if self._w3 is None:
            from .config import Config
            config = Config()

            if self._custom_rpc_url:
                rpc_url = self._custom_rpc_url
            else:
                rpc_url = config.get_rpc_url(self.network_name)

            self._w3 = Web3(Web3.HTTPProvider(rpc_url))

            if not self._w3.is_connected():
                raise ConnectionError(f"Cannot connect to RPC: {rpc_url}")

        return self._w3

    def get_chain_id(self) -> int:
        """Get chain ID for this account's network."""
        return self.w3.eth.chain_id

    def get_nonce(self, key: int = 0) -> int:
        """
        Get nonce for this account from EntryPoint.

        Args:
            key: Nonce key for parallel transactions (default: 0)

        Returns:
            Current nonce value
        """
        from .config import Config
        config = Config()
        entry_point_address = config.get_entry_point(self.network_name)

        # EntryPoint.getNonce(address sender, uint192 key)
        entry_point_abi = [{
            "inputs": [
                {"name": "sender", "type": "address"},
                {"name": "key", "type": "uint192"}
            ],
            "name": "getNonce",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]

        contract = self.w3.eth.contract(
            address=to_checksum_address(entry_point_address),
            abi=entry_point_abi
        )

        return contract.functions.getNonce(self.contract_address, key).call()

    def get_balance(self) -> int:
        """Get ETH balance of the smart contract account."""
        return self.w3.eth.get_balance(self.contract_address)

    # ============================================
    # UserOperation Construction
    # ============================================

    def build_user_operation(
        self,
        call_data: bytes,
        nonce: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        call_gas_limit: int = 100000,
        verification_gas_limit: int = 150000,
        pre_verification_gas: int = 21000,
        paymaster_and_data: bytes = b'',
        signature: bytes = b''
    ) -> Dict[str, Any]:
        """
        Build a UserOperation for ERC-4337.

        Args:
            call_data: Encoded call data for the account
            nonce: Account nonce (fetched if not provided)
            max_fee_per_gas: Max gas price (fetched if not provided)
            max_priority_fee_per_gas: Priority fee (fetched if not provided)
            call_gas_limit: Gas limit for the call
            verification_gas_limit: Gas limit for signature verification
            pre_verification_gas: Gas overhead
            paymaster_and_data: Paymaster data (empty if no paymaster)
            signature: Signature bytes (empty initially, filled after signing)

        Returns:
            UserOperation dict (PackedUserOperation format)
        """
        if nonce is None:
            nonce = self.get_nonce()

        # Get gas prices if not provided
        if max_fee_per_gas is None or max_priority_fee_per_gas is None:
            gas_price_data = self._get_gas_prices()
            max_fee_per_gas = max_fee_per_gas or gas_price_data['maxFeePerGas']
            max_priority_fee_per_gas = max_priority_fee_per_gas or gas_price_data['maxPriorityFeePerGas']

        # Pack gas limits: accountGasLimits = verificationGasLimit || callGasLimit
        account_gas_limits = (verification_gas_limit << 128) | call_gas_limit

        # Pack gas fees: gasFees = maxPriorityFeePerGas || maxFeePerGas
        gas_fees = (max_priority_fee_per_gas << 128) | max_fee_per_gas

        user_op = {
            'sender': self.contract_address,
            'nonce': nonce,
            'initCode': b'',  # Account already deployed
            'callData': call_data,
            'accountGasLimits': account_gas_limits.to_bytes(32, 'big'),
            'preVerificationGas': pre_verification_gas,
            'gasFees': gas_fees.to_bytes(32, 'big'),
            'paymasterAndData': paymaster_and_data,
            'signature': signature
        }

        return user_op

    def get_user_op_hash(self, user_op: Dict[str, Any]) -> bytes:
        """
        Calculate the hash of a UserOperation (for signing).

        Args:
            user_op: UserOperation dict

        Returns:
            32-byte hash to be signed
        """
        from .config import Config
        config = Config()
        entry_point_address = config.get_entry_point(self.network_name)

        # This should match the EntryPoint.getUserOpHash() logic
        # For now, this is a placeholder - actual implementation needs ABI encoding
        # TODO: Implement proper EIP-712 hashing

        # Simplified version - needs proper implementation
        packed_data = b''.join([
            bytes.fromhex(self.contract_address[2:]),
            user_op['nonce'].to_bytes(32, 'big'),
            user_op['callData'],
            user_op['accountGasLimits'],
            user_op['preVerificationGas'].to_bytes(32, 'big'),
            user_op['gasFees'],
            user_op['paymasterAndData']
        ])

        return Web3.keccak(packed_data)

    # ============================================
    # Send UserOperation (Placeholder)
    # ============================================

    def send_user_operation(self, user_op: Dict[str, Any]) -> str:
        """
        Send UserOperation to bundler.

        This is a placeholder for future implementation.
        Will be completed after middleware layer is ready.

        Args:
            user_op: Signed UserOperation

        Returns:
            UserOperation hash

        Raises:
            NotImplementedError: Middleware not yet implemented
        """
        # TODO: Implement after middleware/aggregator is ready
        raise NotImplementedError(
            "send_user_operation will be implemented with middleware layer for multi-sig aggregation"
        )

    # ============================================
    # Utility Methods
    # ============================================

    def is_deployed(self) -> bool:
        """Check if the account contract is deployed."""
        code = self.w3.eth.get_code(self.contract_address)
        return len(code) > 0

    def _get_gas_prices(self) -> Dict[str, int]:
        """
        Get current gas prices for EIP-1559 transactions.

        Returns:
            Dict with 'maxFeePerGas' and 'maxPriorityFeePerGas'
        """
        try:
            latest_block = self.w3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)

            if base_fee > 0:
                # EIP-1559 network
                try:
                    max_priority_fee = self.w3.eth.max_priority_fee
                except:
                    max_priority_fee = self.w3.to_wei(1.5, 'gwei')

                max_fee = base_fee * 2 + max_priority_fee

                return {
                    'maxFeePerGas': max_fee,
                    'maxPriorityFeePerGas': max_priority_fee
                }
            else:
                # Legacy network
                gas_price = self.w3.eth.gas_price
                return {
                    'maxFeePerGas': gas_price,
                    'maxPriorityFeePerGas': gas_price
                }
        except Exception:
            # Fallback to default values
            default_gas = self.w3.to_wei(2, 'gwei')
            return {
                'maxFeePerGas': default_gas,
                'maxPriorityFeePerGas': default_gas
            }

    def __repr__(self):
        return (
            f"<Account network={self.network_name} "
            f"address={self.contract_address} "
            f"owners={len(self.owners)}/{self.threshold}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export account configuration to dict."""
        return {
            'network_name': self.network_name,
            'contract_address': self.contract_address,
            'owners': self.owners,
            'threshold': self.threshold,
            'guardians': self.guardians,
            'guardian_threshold': self.guardian_threshold,
            'bundler_url': self.bundler_url,
            'paymaster_url': self.paymaster_url
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Account':
        """Create Account instance from dict."""
        return cls(**data)
