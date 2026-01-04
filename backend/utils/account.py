"""
Account class for managing smart contract account operations.
Handles transaction building, UserOp construction, and message signing.
"""
from typing import Optional, List, Dict, Any
from backend.config.abi import factory_abi, account_abi, entrypoint_abi
from eth_utils import to_checksum_address
from web3 import Web3
from backend.config.config import Config

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
        name: Optional[str] = None,
        guardians: Optional[List[str]] = None,
        guardian_threshold: int = 0,
        salt: int = 0,
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
            name: User-friendly name for the account (optional)
            guardians: List of guardian addresses for social recovery
            guardian_threshold: Guardian signature threshold
            salt: Salt value used for CREATE2 deployment
            bundler_url: Custom bundler RPC endpoint (optional)
            paymaster_url: Custom paymaster RPC endpoint (optional)
            rpc_url: Custom RPC URL, overrides Config if provided
        """
        self.network_name = network_name
        self.name = name
        self.contract_address = to_checksum_address(contract_address)
        self.owners = [to_checksum_address(addr) for addr in owners]
        self.threshold = threshold
        self.guardians = [to_checksum_address(addr) for addr in guardians] if guardians else []
        self.guardian_threshold = guardian_threshold
        self.salt = salt

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
            from backend.config.config import Config
            config = Config()

            if self._custom_rpc_url:
                rpc_url = self._custom_rpc_url
            else:
                rpc_url = config.get_rpc_url(self.network_name)

            self._w3 = Web3(Web3.HTTPProvider(rpc_url))

            if not self._w3.is_connected():
                raise ConnectionError(f"Cannot connect to RPC: {rpc_url}")

        return self._w3

    @staticmethod
    def calculate_address(
        network_name: str,
        owners: List[str],
        threshold: int,
        guardians: Optional[List[str]] = None,
        guardian_threshold: int = 0,
        salt: int = 0,
        rpc_url: Optional[str] = None
    ) -> str:
        """
        Calculate the counterfactual address for a smart account

        This method calls the factory contract's getAddress() function to
        compute the CREATE2 address without deploying the account.

        Args:
            network_name: Name of the network (e.g., "sepolia")
            owners: List of owner addresses
            threshold: Signature threshold for multi-sig
            guardians: List of guardian addresses (optional)
            guardian_threshold: Guardian signature threshold
            salt: Salt value for CREATE2 (default: 0)
            rpc_url: Custom RPC URL (optional)

        Returns:
            Counterfactual address (checksum format)

        Raises:
            ConnectionError: If RPC connection fails
            ValueError: If factory contract call fails
        """
        # Load configuration
        config = Config()

        # Get RPC URL
        if rpc_url:
            _rpc_url = rpc_url
        else:
            _rpc_url = config.get_rpc_url(network_name)

        # Create Web3 instance
        w3 = Web3(Web3.HTTPProvider(_rpc_url))
        if not w3.is_connected():
            raise ConnectionError(f"Cannot connect to RPC: {_rpc_url}")

        # Get factory contract address
        factory_address = config.get_factory(network_name)

        # Ensure checksum addresses
        owners_checksum = [to_checksum_address(addr) for addr in owners]
        guardians_checksum = [to_checksum_address(addr) for addr in guardians] if guardians else []

        # Ensure integer types
        threshold_int = int(threshold)
        guardian_threshold_int = int(guardian_threshold)
        salt_int = int(salt)

        # Create factory contract instance
        factory = w3.eth.contract(
            address=to_checksum_address(factory_address),
            abi=factory_abi
        )

        # Call getAddress() to compute counterfactual address
        try:
            counterfactual_address = factory.functions.getAddress(
                owners_checksum,
                threshold_int,
                guardians_checksum,
                guardian_threshold_int,
                salt_int
            ).call()

            return to_checksum_address(counterfactual_address)

        except Exception as e:
            raise ValueError(f"Failed to calculate account address: {e}")

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
        from backend.config.config import Config
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
        call_gas_limit: Optional[int] = None,
        verification_gas_limit: Optional[int] = None,
        pre_verification_gas: Optional[int] = None,
        paymaster_and_data: bytes = b'',
        signature: bytes = b''
    ) -> Dict[str, Any]:
        """
        Build a UserOperation for ERC-4337 in bundler API format.

        Args:
            call_data: Encoded call data for the account
            nonce: Account nonce (fetched if not provided)
            max_fee_per_gas: Max gas price (fetched if not provided)
            max_priority_fee_per_gas: Priority fee (fetched if not provided)
            call_gas_limit: Gas limit for the call (auto-adjusted if None)
            verification_gas_limit: Gas limit for signature verification (auto-adjusted if None)
            pre_verification_gas: Gas overhead (auto-adjusted if None)
            paymaster_and_data: Paymaster data (empty if no paymaster)
            signature: Signature bytes (empty initially, filled after signing)

        Returns:
            UserOperation dict in unpacked format (ready for bundler submission)
        """
        if nonce is None:
            nonce = self.get_nonce()

        # Get gas prices if not provided
        if max_fee_per_gas is None or max_priority_fee_per_gas is None:
            gas_price_data = self._get_gas_prices()
            max_fee_per_gas = max_fee_per_gas or gas_price_data['maxFeePerGas']
            max_priority_fee_per_gas = max_priority_fee_per_gas or gas_price_data['maxPriorityFeePerGas']

        # Check if account is deployed to determine if we need initCode
        is_deployed = self.is_deployed()

        # Auto-adjust gas limits based on deployment status
        # When account needs deployment, we need significantly more gas
        if call_gas_limit is None:
            call_gas_limit = 200000 if not is_deployed else 100000

        if verification_gas_limit is None:
            # Need much more gas for deployment (factory call + account initialization)
            verification_gas_limit = 2000000 if not is_deployed else 150000

        if pre_verification_gas is None:
            # More overhead for deployment transactions
            pre_verification_gas = 100000 if not is_deployed else 50000

        # Construct initCode (factory + factoryData)
        init_code = b''
        if not is_deployed:
            # Load factory ABI
            config = Config()

            factory_address = Web3.to_checksum_address(config.get_factory(self.network_name))
            entrypoint_address =Web3.to_checksum_address(config.get_entry_point(self.network_name))

            factory = self.w3.eth.contract(
                address=factory_address,
                abi=factory_abi
            )


            # Ensure checksum addresses
            owners_checksum = [Web3.to_checksum_address(a) for a in self.owners]
            guardians_checksum = [Web3.to_checksum_address(a) for a in self.guardians]

            # Ensure integer values
            threshold = int(self.threshold)
            guardian_threshold = int(self.guardian_threshold)
            salt = int(self.salt)

            # ⭐ The only correct way to encode the factory calldata
            factory_data = factory.functions.createAccount(
                owners_checksum,
                threshold,
                guardians_checksum,
                guardian_threshold,
                salt
            )._encode_transaction_data()

            # ⭐ initCode = factory_address (20 bytes) + factoryData
            init_code = bytes.fromhex(factory_address[2:]) + bytes.fromhex(factory_data[2:])

        # Parse initCode for unpacked format
        if len(init_code) == 0:
            factory = None
            factory_data_hex = None
        elif len(init_code) >= 20:
            factory = "0x" + init_code[:20].hex()
            factory_data_hex = "0x" + init_code[20:].hex() if len(init_code) > 20 else "0x"
        else:
            factory = None
            factory_data_hex = None

        # Parse paymasterAndData for unpacked format
        if len(paymaster_and_data) == 0:
            paymaster = None
            paymaster_verification_gas_limit = None
            paymaster_post_op_gas_limit = None
            paymaster_data_hex = None
        else:
            # paymasterAndData format: paymaster (20 bytes) + verificationGasLimit (16 bytes) + postOpGasLimit (16 bytes) + data
            if len(paymaster_and_data) >= 52:
                paymaster = "0x" + paymaster_and_data[:20].hex()
                paymaster_verification_gas_limit = hex(int.from_bytes(paymaster_and_data[20:36], 'big'))
                paymaster_post_op_gas_limit = hex(int.from_bytes(paymaster_and_data[36:52], 'big'))
                paymaster_data_hex = "0x" + paymaster_and_data[52:].hex() if len(paymaster_and_data) > 52 else "0x"
            else:
                paymaster = None
                paymaster_verification_gas_limit = None
                paymaster_post_op_gas_limit = None
                paymaster_data_hex = None

        # Return unpacked format (bundler API format)
        return {
            'sender': self.contract_address,
            'nonce': hex(nonce),
            'factory': factory,
            'factoryData': factory_data_hex,
            'callData': '0x' + call_data.hex(),
            'callGasLimit': hex(call_gas_limit),
            'verificationGasLimit': hex(verification_gas_limit),
            'preVerificationGas': hex(pre_verification_gas),
            'maxFeePerGas': hex(max_fee_per_gas),
            'maxPriorityFeePerGas': hex(max_priority_fee_per_gas),
            'paymaster': paymaster,
            'paymasterVerificationGasLimit': paymaster_verification_gas_limit,
            'paymasterPostOpGasLimit': paymaster_post_op_gas_limit,
            'paymasterData': paymaster_data_hex,
            'signature': '0x' + signature.hex() if signature else '0x'
        }

    def get_user_op_hash(self, user_op: Dict[str, Any]) -> bytes:
        """
        Calculate the hash of a UserOperation (for signing).
        Accepts unpacked format and converts to packed format for EntryPoint.

        Args:
            user_op: UserOperation dict (unpacked format from build_user_operation)

        Returns:
            32-byte hash to be signed
        """
        from backend.config.config import Config
        config = Config()
        entry_point_address = config.get_entry_point(self.network_name)

        # Convert unpacked format to packed format for EntryPoint contract call

        # Parse nonce from hex string
        nonce = int(user_op['nonce'], 16)

        # Reconstruct initCode from factory and factoryData
        if user_op['factory'] is None:
            init_code = b''
        else:
            factory_bytes = bytes.fromhex(user_op['factory'][2:])
            factory_data_bytes = bytes.fromhex(user_op['factoryData'][2:]) if user_op['factoryData'] != "0x" else b''
            init_code = factory_bytes + factory_data_bytes

        # Parse callData from hex string
        call_data = bytes.fromhex(user_op['callData'][2:])

        # Pack accountGasLimits = verificationGasLimit || callGasLimit
        verification_gas_limit = int(user_op['verificationGasLimit'], 16)
        call_gas_limit = int(user_op['callGasLimit'], 16)
        account_gas_limits = (verification_gas_limit << 128) | call_gas_limit

        # Parse preVerificationGas from hex string
        pre_verification_gas = int(user_op['preVerificationGas'], 16)

        # Pack gasFees = maxPriorityFeePerGas || maxFeePerGas
        max_priority_fee = int(user_op['maxPriorityFeePerGas'], 16)
        max_fee = int(user_op['maxFeePerGas'], 16)
        gas_fees = (max_priority_fee << 128) | max_fee

        # Reconstruct paymasterAndData
        if user_op['paymaster'] is None:
            paymaster_and_data = b''
        else:
            paymaster_bytes = bytes.fromhex(user_op['paymaster'][2:])
            pv_gas_limit = int(user_op['paymasterVerificationGasLimit'], 16).to_bytes(16, 'big')
            pp_gas_limit = int(user_op['paymasterPostOpGasLimit'], 16).to_bytes(16, 'big')
            pm_data = bytes.fromhex(user_op['paymasterData'][2:]) if user_op['paymasterData'] != "0x" else b''
            paymaster_and_data = paymaster_bytes + pv_gas_limit + pp_gas_limit + pm_data

        # Parse signature from hex string
        signature = bytes.fromhex(user_op['signature'][2:]) if user_op['signature'] != "0x" else b''

        # EntryPoint ABI for getUserOpHash
        entry_point_abi = [{
            "inputs": [{
                "components": [
                    {"name": "sender", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "initCode", "type": "bytes"},
                    {"name": "callData", "type": "bytes"},
                    {"name": "accountGasLimits", "type": "bytes32"},
                    {"name": "preVerificationGas", "type": "uint256"},
                    {"name": "gasFees", "type": "bytes32"},
                    {"name": "paymasterAndData", "type": "bytes"},
                    {"name": "signature", "type": "bytes"}
                ],
                "name": "userOp",
                "type": "tuple"
            }],
            "name": "getUserOpHash",
            "outputs": [{"name": "", "type": "bytes32"}],
            "stateMutability": "view",
            "type": "function"
        }]

        contract = self.w3.eth.contract(
            address=to_checksum_address(entry_point_address),
            abi=entry_point_abi
        )

        # Create packed format tuple for EntryPoint contract call
        user_op_tuple = (
            user_op['sender'],
            nonce,
            init_code,
            call_data,
            account_gas_limits.to_bytes(32, 'big'),
            pre_verification_gas,
            gas_fees.to_bytes(32, 'big'),
            paymaster_and_data,
            signature
        )

        return contract.functions.getUserOpHash(user_op_tuple).call()

    # ============================================
    # Signature Construction (Multi-sig)
    # ============================================

    def encode_multisig_signature(self, signatures: list) -> bytes:
        """
        Encode multiple signatures for multi-sig account.

        Args:
            signatures: List of signature bytes (each 65 bytes)

        Returns:
            Concatenated signatures
        """
        # Validate signatures
        for sig in signatures:
            if len(sig) != 65:
                raise ValueError(f"Invalid signature length: {len(sig)}. Expected 65 bytes.")

        # Simply concatenate all signatures
        return b''.join(signatures)

    # ============================================
    # CallData Construction
    # ============================================

    def encode_execute_call(self, target: str, value: int, data: bytes = b'') -> bytes:
        """
        Encode a call to the account's execute() function.

        Args:
            target: Destination address
            value: ETH value to send
            data: Call data (empty for simple transfers)

        Returns:
            Encoded callData for UserOperation
        """
        # Function signature: execute(address,uint256,bytes)
        function_signature = Web3.keccak(text='execute(address,uint256,bytes)')[:4]

        # ABI encode the parameters
        encoded_params = self.w3.codec.encode(
            ['address', 'uint256', 'bytes'],
            [to_checksum_address(target), value, data]
        )

        return function_signature + encoded_params

    # ============================================
    # Social Recovery CallData Construction
    # ============================================

    def encode_approve_recovery_call(self, new_owners: List[str], new_threshold: int) -> bytes:
        """
        Encode a call to approveRecovery() for guardian approval.

        Args:
            new_owners: New owner addresses
            new_threshold: New threshold

        Returns:
            Encoded callData for UserOperation
        """
        function_signature = Web3.keccak(text='approveRecovery(address[],uint256)')[:4]
        encoded_params = self.w3.codec.encode(
            ['address[]', 'uint256'],
            [[to_checksum_address(addr) for addr in new_owners], new_threshold]
        )
        return function_signature + encoded_params

    def encode_execute_recovery_call(self, new_owners: List[str], new_threshold: int) -> bytes:
        """
        Encode a call to executeRecovery() to complete recovery process.

        Args:
            new_owners: New owner addresses
            new_threshold: New threshold

        Returns:
            Encoded callData for UserOperation
        """
        function_signature = Web3.keccak(text='executeRecovery(address[],uint256)')[:4]
        encoded_params = self.w3.codec.encode(
            ['address[]', 'uint256'],
            [[to_checksum_address(addr) for addr in new_owners], new_threshold]
        )
        return function_signature + encoded_params

    def encode_add_guardian_call(self, new_guardian: str) -> bytes:
        """
        Encode a call to addGuardian().

        Args:
            new_guardian: Guardian address to add

        Returns:
            Encoded callData for UserOperation
        """
        function_signature = Web3.keccak(text='addGuardian(address)')[:4]
        encoded_params = self.w3.codec.encode(
            ['address'],
            [to_checksum_address(new_guardian)]
        )
        return function_signature + encoded_params

    def encode_remove_guardian_call(self, guardian_to_remove: str) -> bytes:
        """
        Encode a call to removeGuardian().

        Args:
            guardian_to_remove: Guardian address to remove

        Returns:
            Encoded callData for UserOperation
        """
        function_signature = Web3.keccak(text='removeGuardian(address)')[:4]
        encoded_params = self.w3.codec.encode(
            ['address'],
            [to_checksum_address(guardian_to_remove)]
        )
        return function_signature + encoded_params

    def encode_add_owner_call(self, new_owner: str) -> bytes:
        """
        Encode a call to addOwner().

        Args:
            new_owner: Owner address to add

        Returns:
            Encoded callData for UserOperation
        """
        function_signature = Web3.keccak(text='addOwner(address)')[:4]
        encoded_params = self.w3.codec.encode(
            ['address'],
            [to_checksum_address(new_owner)]
        )
        return function_signature + encoded_params

    def encode_remove_owner_call(self, owner_to_remove: str) -> bytes:
        """
        Encode a call to removeOwner().

        Args:
            owner_to_remove: Owner address to remove

        Returns:
            Encoded callData for UserOperation
        """
        function_signature = Web3.keccak(text='removeOwner(address)')[:4]
        encoded_params = self.w3.codec.encode(
            ['address'],
            [to_checksum_address(owner_to_remove)]
        )
        return function_signature + encoded_params

    # ============================================
    # Social Recovery View Functions
    # ============================================

    def get_owners(self) -> List[str]:
        """Get current owners of the account from contract."""
        contract_abi = [{
            "inputs": [],
            "name": "getOwners",
            "outputs": [{"name": "", "type": "address[]"}],
            "stateMutability": "view",
            "type": "function"
        }]
        contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=contract_abi
        )
        return contract.functions.getOwners().call()

    def get_guardians(self) -> List[str]:
        """Get current guardians of the account from contract."""
        contract_abi = [{
            "inputs": [],
            "name": "getGuardians",
            "outputs": [{"name": "", "type": "address[]"}],
            "stateMutability": "view",
            "type": "function"
        }]
        contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=contract_abi
        )
        return contract.functions.getGuardians().call()

    def get_recovery_approval_count(self, new_owners: List[str], new_threshold: int) -> int:
        """
        Get the number of guardians who have approved a recovery.

        Args:
            new_owners: Proposed new owner addresses
            new_threshold: Proposed new threshold

        Returns:
            Number of approvals
        """
        contract_abi = [{
            "inputs": [
                {"name": "newOwners", "type": "address[]"},
                {"name": "newThreshold", "type": "uint256"}
            ],
            "name": "getRecoveryApprovalCount",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=contract_abi
        )
        return contract.functions.getRecoveryApprovalCount(
            [to_checksum_address(addr) for addr in new_owners],
            new_threshold
        ).call()

    def is_social_recovery_enabled(self) -> bool:
        """Check if social recovery is enabled (has guardians)."""
        contract_abi = [{
            "inputs": [],
            "name": "isSocialRecoveryEnabled",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        }]
        contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=contract_abi
        )
        return contract.functions.isSocialRecoveryEnabled().call()

    # ============================================
    # Send UserOperation (Placeholder)
    # ============================================

    def send_user_operation(
        self,
        user_op: Dict[str, Any],
        bundler_url: Optional[str] = None
    ) -> str:
        """
        Send UserOperation to bundler or aggregation service.

        For single-sig accounts (threshold == 1): directly send to bundler
        For multi-sig accounts (threshold > 1): send to aggregation service

        Args:
            user_op: Signed UserOperation (unpacked format)
            bundler_url: Optional custom bundler URL

        Returns:
            UserOperation hash (from bundler or aggregator)

        Raises:
            ValueError: If submission fails
        """
        # Determine if this is a multi-sig account
        is_multisig = len(self.owners) > 1 or self.threshold > 1

        if not is_multisig:
            # Single-sig account: send directly to bundler
            from backend.utils.PimlicoBundlerClient import PimlicoBundler
            from backend.config.config import Config

            config = Config()
            entry_point = config.get_entry_point(self.network_name)

            # Use custom bundler URL if provided
            if bundler_url:
                bundler = PimlicoBundler(api_key="", chain_name=self.network_name)
                bundler.bundler_url = bundler_url
            else:
                # Use Pimlico bundler with API key from environment
                import os
                api_key = os.getenv('PIMLICO_API_KEY', '')
                if not api_key:
                    raise ValueError(
                        "PIMLICO_API_KEY environment variable not set. "
                        "Required for single-sig account submission."
                    )
                bundler = PimlicoBundler(api_key=api_key, chain_name=self.network_name)

            return bundler.send_user_operation(user_op, entry_point)

        else:
            # Multi-sig account: send to aggregation service
            from backend.service.aggregator import submit_multisig_transaction

            # Extract signature and recover signer address
            signature_hex = user_op['signature']

            # Signature should be 65 bytes (0x + 130 hex chars) for multi-sig submission
            signature_bytes = bytes.fromhex(signature_hex[2:] if signature_hex.startswith('0x') else signature_hex)

            if len(signature_bytes) != 65:
                raise ValueError(
                    f"For multi-sig submission, provide only the first signature (65 bytes). "
                    f"Got {len(signature_bytes)} bytes. "
                    f"Other signers will add their signatures via the aggregation API."
                )

            # Recover signer address from signature
            user_op_hash = self.get_user_op_hash(user_op)
            from eth_account import Account as EthAccount
            from eth_account.messages import encode_defunct

            # EIP-191 message encoding
            message = encode_defunct(primitive=user_op_hash)
            signer_address = EthAccount.recover_message(message, signature=signature_bytes)

            # Submit to aggregation service
            result = submit_multisig_transaction(
                smart_account_address=self.contract_address,
                chain_id=self.get_chain_id(),
                chain_name=self.network_name,
                user_operation=user_op,
                threshold=self.threshold,
                initial_signature=signature_hex,
                signer_address=signer_address
            )

            return result['transaction_hash']

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
            'name': self.name,
            'contract_address': self.contract_address,
            'owners': self.owners,
            'threshold': self.threshold,
            'guardians': self.guardians,
            'guardian_threshold': self.guardian_threshold,
            'salt': self.salt,
            'bundler_url': self.bundler_url,
            'paymaster_url': self.paymaster_url
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Account':
        """Create Account instance from dict."""
        return cls(**data)
