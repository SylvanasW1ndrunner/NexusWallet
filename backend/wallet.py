"""
Wallet class for managing multiple smart contract accounts across chains.
Integrates with KeyManager for signing operations.
"""
from typing import Dict, List, Optional, Any
from .account import Account
from .config import Config
from .keymanager.keyManager import KeyManager
import json
import os


class Wallet:
    """
    Wallet manages multiple smart contract accounts across different chains.

    The Wallet is designed to:
    - Maintain multiple Account instances (one per chain)
    - Integrate with a singleton KeyManager for signing
    - Support multi-sig workflows through future middleware
    - Persist and load wallet state

    Usage:
        km = KeyManager()
        km.unlock(password)

        wallet = Wallet(key_manager=km)
        wallet.add_account(
            network_name="sepolia",
            contract_address="0x...",
            owners=[...],
            threshold=2
        )

        account = wallet.get_account("sepolia")
        user_op = account.build_user_operation(...)
    """

    def __init__(
        self,
        key_manager: KeyManager,
        wallet_name: str = "default",
        storage_path: Optional[str] = None,
        auto_load: bool = True
    ):
        """
        Initialize Wallet instance.

        Args:
            key_manager: Singleton KeyManager instance for signing
            wallet_name: Unique name for this wallet
            storage_path: Path to persist wallet data (optional)
            auto_load: Whether to automatically load from JSON if exists
        """
        self.key_manager = key_manager
        self.wallet_name = wallet_name

        # Storage
        self.storage_path = storage_path or f"wallet_{wallet_name}.json"

        # AA Accounts: {network_name: List[Account]}
        # One network can have multiple AA accounts
        self._accounts: Dict[str, List[Account]] = {}

        # Config singleton
        self._config = Config()

        # Validate KeyManager
        if not isinstance(key_manager, KeyManager):
            raise TypeError("key_manager must be a KeyManager instance")

        # Auto-load from JSON if exists
        if auto_load and os.path.exists(self.storage_path):
            self.load()

    # ============================================
    # Account Management
    # ============================================

    def add_account(
        self,
        network_name: str,
        contract_address: str,
        owners: List[str],
        threshold: int,
        guardians: Optional[List[str]] = None,
        guardian_threshold: int = 0,
        bundler_url: Optional[str] = None,
        paymaster_url: Optional[str] = None,
        rpc_url: Optional[str] = None,
        save: bool = True
    ) -> Account:
        """
        Add a smart contract account to the wallet.

        Args:
            network_name: Name of the network (must be in Config)
            contract_address: Smart contract account address
            owners: List of owner addresses
            threshold: Multi-sig threshold
            guardians: Optional guardian addresses for social recovery
            guardian_threshold: Guardian threshold
            bundler_url: Custom bundler endpoint
            paymaster_url: Custom paymaster endpoint
            rpc_url: Custom RPC URL (overrides Config)
            save: Whether to save to JSON immediately (default: True)

        Returns:
            Created Account instance

        Raises:
            ValueError: If network not configured or account already exists
        """
        # Validate network exists in Config
        if not rpc_url and not self._config.has_network(network_name):
            raise ValueError(
                f"Network '{network_name}' not configured. "
                f"Add it to Config or provide custom rpc_url"
            )

        # Initialize network's account list if not exists
        if network_name not in self._accounts:
            self._accounts[network_name] = []

        # Check if account with same address already exists on this network
        for existing_account in self._accounts[network_name]:
            if existing_account.contract_address.lower() == contract_address.lower():
                raise ValueError(
                    f"Account {contract_address} already exists on {network_name}. "
                    f"Cannot add duplicate account."
                )

        # Create Account instance
        account = Account(
            network_name=network_name,
            contract_address=contract_address,
            owners=owners,
            threshold=threshold,
            guardians=guardians,
            guardian_threshold=guardian_threshold,
            bundler_url=bundler_url,
            paymaster_url=paymaster_url,
            rpc_url=rpc_url
        )

        # Verify the KeyManager's address is in owners
        if self.key_manager.address and self.key_manager.address not in owners:
            raise ValueError(
                f"KeyManager address {self.key_manager.address} is not in account owners. "
                f"This wallet cannot sign for this account."
            )

        # Add to the network's account list
        self._accounts[network_name].append(account)

        # Auto-save to JSON
        if save:
            self.save()

        return account

    def get_account(self, network_name: str, contract_address: Optional[str] = None, index: int = 0) -> Account:
        """
        Get an account by network name and optional address or index.

        Args:
            network_name: Name of the network
            contract_address: Specific contract address (optional)
            index: Index in the account list (default: 0, used if contract_address not provided)

        Returns:
            Account instance

        Raises:
            KeyError: If network or account not found
            IndexError: If index out of range
        """
        if network_name not in self._accounts or len(self._accounts[network_name]) == 0:
            raise KeyError(
                f"No accounts for network '{network_name}'. "
                f"Available networks: {self.list_networks()}"
            )

        accounts = self._accounts[network_name]

        # If specific address provided, find it
        if contract_address:
            for account in accounts:
                if account.contract_address.lower() == contract_address.lower():
                    return account
            raise KeyError(f"Account {contract_address} not found on {network_name}")

        # Otherwise return by index
        if index >= len(accounts):
            raise IndexError(
                f"Account index {index} out of range. "
                f"{network_name} has {len(accounts)} account(s)"
            )

        return accounts[index]

    def get_accounts(self, network_name: str) -> List[Account]:
        """
        Get all accounts on a specific network.

        Args:
            network_name: Name of the network

        Returns:
            List of Account instances (empty list if none)
        """
        return self._accounts.get(network_name, [])

    def has_account(self, network_name: str) -> bool:
        """Check if wallet has any account on a specific network."""
        return network_name in self._accounts and len(self._accounts[network_name]) > 0

    def list_networks(self) -> List[str]:
        """List all networks with accounts in this wallet."""
        return [network for network, accounts in self._accounts.items() if len(accounts) > 0]

    def remove_account(self, network_name: str, contract_address: Optional[str] = None, save: bool = True):
        """
        Remove an account from the wallet.

        Args:
            network_name: Network name
            contract_address: Specific account address to remove (if None, removes all accounts on this network)
            save: Whether to save to JSON immediately
        """
        if network_name not in self._accounts:
            return

        if contract_address:
            # Remove specific account
            accounts = self._accounts[network_name]
            self._accounts[network_name] = [
                acc for acc in accounts
                if acc.contract_address.lower() != contract_address.lower()
            ]

            # Clean up empty network list
            if len(self._accounts[network_name]) == 0:
                del self._accounts[network_name]
        else:
            # Remove all accounts on this network
            del self._accounts[network_name]

        if save:
            self.save()

    def update_account(
        self,
        network_name: str,
        contract_address: str,
        save: bool = True,
        **kwargs
    ) -> Account:
        """
        Update an existing account's configuration.

        Args:
            network_name: Network name
            contract_address: Account address to update
            save: Whether to save to JSON immediately
            **kwargs: Account parameters to update

        Returns:
            Updated Account instance
        """
        if network_name not in self._accounts:
            raise KeyError(f"No accounts for network '{network_name}'")

        accounts = self._accounts[network_name]
        account_index = None

        # Find the account
        for i, account in enumerate(accounts):
            if account.contract_address.lower() == contract_address.lower():
                account_index = i
                break

        if account_index is None:
            raise KeyError(f"Account {contract_address} not found on {network_name}")

        # Get current account config
        current_account = accounts[account_index]
        account_data = current_account.to_dict()

        # Update with new values
        account_data.update(kwargs)

        # Recreate account
        new_account = Account.from_dict(account_data)
        self._accounts[network_name][account_index] = new_account

        if save:
            self.save()

        return new_account

    # ============================================
    # EOA Operations (Core Functions Only)
    # ============================================

    def get_eoa_address(self) -> str:
        """Get the EOA address (KeyManager address)."""
        if not self.key_manager.address:
            raise ValueError("KeyManager has no address. Create or unlock a key first.")
        return self.key_manager.address

    def get_eoa_balance(self, network_name: str) -> int:
        """
        Get ETH balance of the EOA on a specific network.

        Args:
            network_name: Network name

        Returns:
            Balance in wei
        """
        if not self.key_manager.address:
            raise ValueError("KeyManager has no address")

        rpc_url = self._config.get_rpc_url(network_name)
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            raise ConnectionError(f"Cannot connect to {network_name} RPC: {rpc_url}")

        return w3.eth.get_balance(self.key_manager.address)

    def get_eoa_nonce(self, network_name: str) -> int:
        """
        Get transaction nonce for EOA on a specific network.

        Args:
            network_name: Network name

        Returns:
            Current nonce
        """
        if not self.key_manager.address:
            raise ValueError("KeyManager has no address")

        rpc_url = self._config.get_rpc_url(network_name)
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            raise ConnectionError(f"Cannot connect to {network_name} RPC: {rpc_url}")

        return w3.eth.get_transaction_count(self.key_manager.address)

    def send_transaction(
        self,
        network_name: str,
        to: str,
        value: int = 0,
        data: bytes = b'',
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        nonce: Optional[int] = None
    ) -> str:
        """
        Send a transaction using EOA mode.
        This is the ONLY function for sending EOA transactions.

        Args:
            network_name: Network name
            to: Recipient address
            value: ETH value in wei
            data: Transaction data (for contract calls)
            gas: Gas limit (estimated if not provided)
            gas_price: Gas price (legacy, for non-EIP-1559)
            max_fee_per_gas: Max fee per gas (EIP-1559)
            max_priority_fee_per_gas: Priority fee (EIP-1559)
            nonce: Transaction nonce (fetched if not provided)

        Returns:
            Transaction hash (hex string)

        Raises:
            PermissionError: If KeyManager is locked
        """
        if not self.key_manager.unlocked:
            raise PermissionError("Wallet is locked. Unlock KeyManager first.")

        from web3 import Web3
        from eth_utils import to_checksum_address

        rpc_url = self._config.get_rpc_url(network_name)
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            raise ConnectionError(f"Cannot connect to {network_name} RPC: {rpc_url}")

        chain_id = self._config.get_chain_id(network_name)

        # Build transaction
        tx = {
            'from': self.key_manager.address,
            'to': to_checksum_address(to),
            'value': value,
            'data': data,
            'chainId': chain_id,
            'nonce': nonce if nonce is not None else self.get_eoa_nonce(network_name)
        }

        # Gas estimation
        if gas:
            tx['gas'] = gas
        else:
            try:
                tx['gas'] = w3.eth.estimate_gas(tx)
            except Exception:
                tx['gas'] = 21000 if not data else 100000

        # Gas price (EIP-1559 or legacy)
        if max_fee_per_gas is not None and max_priority_fee_per_gas is not None:
            tx['maxFeePerGas'] = max_fee_per_gas
            tx['maxPriorityFeePerGas'] = max_priority_fee_per_gas
        elif gas_price is not None:
            tx['gasPrice'] = gas_price
        else:
            # Auto-detect
            try:
                latest_block = w3.eth.get_block('latest')
                base_fee = latest_block.get('baseFeePerGas', 0)

                if base_fee > 0:
                    try:
                        max_priority_fee = w3.eth.max_priority_fee
                    except:
                        max_priority_fee = w3.to_wei(1.5, 'gwei')

                    tx['maxFeePerGas'] = base_fee * 2 + max_priority_fee
                    tx['maxPriorityFeePerGas'] = max_priority_fee
                else:
                    tx['gasPrice'] = w3.eth.gas_price
            except:
                tx['gasPrice'] = w3.eth.gas_price

        # Sign transaction
        signed_tx = self.key_manager.sign_transaction(tx)

        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        return tx_hash.hex()

    def send_message(self, message: str) -> bytes:
        """
        Sign a message using EOA.
        This is the ONLY function for signing EOA messages.

        Args:
            message: Human-readable message to sign

        Returns:
            Signature bytes

        Raises:
            PermissionError: If KeyManager is locked
        """
        if not self.key_manager.unlocked:
            raise PermissionError("Wallet is locked. Unlock KeyManager first.")

        return self.key_manager.sign_message(message.encode())

    def wait_for_transaction(
        self,
        network_name: str,
        tx_hash: str,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Wait for an EOA transaction to be mined.

        Args:
            network_name: Network name
            tx_hash: Transaction hash
            timeout: Timeout in seconds

        Returns:
            Transaction receipt
        """
        from web3 import Web3

        rpc_url = self._config.get_rpc_url(network_name)
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            raise ConnectionError(f"Cannot connect to {network_name} RPC: {rpc_url}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        return dict(receipt)

    # ============================================
    # Wallet State Persistence
    # ============================================

    def save(self, path: Optional[str] = None):
        """
        Save wallet configuration to disk.

        Note: This only saves account configurations, not the KeyManager private key.
        KeyManager uses its own encrypted storage.

        Args:
            path: File path (uses self.storage_path if not provided)
        """
        save_path = path or self.storage_path

        wallet_data = {
            'wallet_name': self.wallet_name,
            'key_manager_address': self.key_manager.address,
            'accounts': {
                network: [account.to_dict() for account in account_list]
                for network, account_list in self._accounts.items()
            }
        }

        with open(save_path, 'w') as f:
            json.dump(wallet_data, f, indent=2)

    def load(self, path: Optional[str] = None):
        """
        Load wallet configuration from disk.

        Args:
            path: File path (uses self.storage_path if not provided)

        Raises:
            FileNotFoundError: If wallet file doesn't exist
            ValueError: If KeyManager address doesn't match
        """
        load_path = path or self.storage_path

        if not os.path.exists(load_path):
            raise FileNotFoundError(f"Wallet file not found: {load_path}")

        with open(load_path, 'r') as f:
            wallet_data = json.load(f)

        # Validate KeyManager address matches
        if wallet_data.get('key_manager_address') != self.key_manager.address:
            raise ValueError(
                f"Wallet KeyManager mismatch. "
                f"Expected: {wallet_data.get('key_manager_address')}, "
                f"Got: {self.key_manager.address}"
            )

        # Load accounts
        self._accounts.clear()
        for network_name, account_list_data in wallet_data.get('accounts', {}).items():
            self._accounts[network_name] = []
            for account_data in account_list_data:
                account = Account.from_dict(account_data)
                self._accounts[network_name].append(account)

    # ============================================
    # Utility Methods
    # ============================================

    def get_all_balances(self) -> Dict[str, Any]:
        """
        Get ETH balances for all AA accounts.

        Returns:
            Dict of {network_name: {account_address: balance_wei}}
        """
        balances = {}
        for network_name, account_list in self._accounts.items():
            network_balances = {}
            for account in account_list:
                try:
                    network_balances[account.contract_address] = account.get_balance()
                except Exception as e:
                    network_balances[account.contract_address] = f"Error: {str(e)}"
            balances[network_name] = network_balances

        return balances

    def check_deployment_status(self) -> Dict[str, Any]:
        """
        Check if all accounts are deployed.

        Returns:
            Dict of {network_name: {account_address: is_deployed}}
        """
        status = {}
        for network_name, account_list in self._accounts.items():
            network_status = {}
            for account in account_list:
                try:
                    network_status[account.contract_address] = account.is_deployed()
                except Exception:
                    network_status[account.contract_address] = False
            status[network_name] = network_status

        return status

    def __repr__(self):
        total_accounts = sum(len(accounts) for accounts in self._accounts.values())
        return (
            f"<Wallet name={self.wallet_name} "
            f"total_accounts={total_accounts} "
            f"networks={list(self._accounts.keys())}>"
        )

    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of the wallet state.

        Returns:
            Dict with wallet information including both EOA and AA accounts
        """
        # Get EOA balances across all configured networks
        eoa_balances = {}
        for network_name in self._config.list_networks():
            try:
                eoa_balances[network_name] = self.get_eoa_balance(network_name)
            except:
                eoa_balances[network_name] = 'error'

        # Build AA accounts summary
        aa_accounts_summary = {}
        for network_name, account_list in self._accounts.items():
            aa_accounts_summary[network_name] = []
            for account in account_list:
                try:
                    account_info = {
                        'address': account.contract_address,
                        'owners': len(account.owners),
                        'threshold': account.threshold,
                        'deployed': account.is_deployed() if account.w3.is_connected() else 'unknown',
                        'balance': account.get_balance() if account.w3.is_connected() else 0
                    }
                except Exception as e:
                    account_info = {
                        'address': account.contract_address,
                        'error': str(e)
                    }
                aa_accounts_summary[network_name].append(account_info)

        return {
            'wallet_name': self.wallet_name,
            'eoa_address': self.key_manager.address,
            'key_manager_unlocked': self.key_manager.unlocked,
            'eoa_balances': eoa_balances,  # EOA balances across all networks
            'aa_accounts': aa_accounts_summary  # List of accounts per network
        }
