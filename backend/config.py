"""
Global configuration for multi-chain support.
Manages RPC endpoints and network configurations.
"""
from typing import Dict, Optional
from dataclasses import dataclass, asdict
import json
import os


@dataclass
class NetworkConfig:
    """Configuration for a single network."""
    chain_id: int
    rpc_url: str
    entrypoint_address: Optional[str] = None
    factory_address: Optional[str] = None
    name: Optional[str] = None

    def __post_init__(self):
        if not self.rpc_url:
            raise ValueError("RPC URL cannot be empty")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'NetworkConfig':
        """Create from dictionary."""
        return cls(**data)


class Config:
    """
    Global configuration singleton for managing network settings.
    Automatically loads from and saves to config.json.

    Usage:
        config = Config()  # Auto-loads from config.json if exists
        config.add_network("sepolia", NetworkConfig(...))
        rpc = config.get_rpc_url("sepolia")
    """

    _instance = None
    DEFAULT_CONFIG_PATH = "config.json"

    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return

        self._networks: Dict[str, NetworkConfig] = {}
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._initialized = True

        # Auto-load from JSON if exists
        if os.path.exists(self.config_path):
            self.load_from_json()

    def add_network(self, network_name: str, network_config: NetworkConfig, save: bool = True):
        """
        Add or update a network configuration.

        Args:
            network_name: Unique identifier for the network (e.g., "mainnet", "sepolia")
            network_config: NetworkConfig object with network details
            save: Whether to save to config.json immediately (default: True)
        """
        self._networks[network_name] = network_config

        if save:
            self.save_to_json()

    def get_network(self, network_name: str) -> NetworkConfig:
        """
        Get network configuration by name.

        Args:
            network_name: Name of the network

        Returns:
            NetworkConfig object

        Raises:
            KeyError: If network not found
        """
        if network_name not in self._networks:
            raise KeyError(f"Network '{network_name}' not configured")
        return self._networks[network_name]

    def get_rpc_url(self, network_name: str) -> str:
        """Get RPC URL for a network."""
        return self.get_network(network_name).rpc_url

    def get_chain_id(self, network_name: str) -> int:
        """Get chain ID for a network."""
        return self.get_network(network_name).chain_id

    def get_entry_point(self, network_name: str) -> Optional[str]:
        """Get EntryPoint address for a network."""
        return self.get_network(network_name).entrypoint_address

    def get_factory(self, network_name: str) -> Optional[str]:
        """Get Factory address for a network."""
        return self.get_network(network_name).factory_address

    def set_entry_point(self, network_name: str, entrypoint_address: str, save: bool = True):
        """
        Set EntryPoint address for a network after deployment.

        Args:
            network_name: Network name
            entrypoint_address: Deployed EntryPoint address
            save: Whether to save to config.json immediately
        """
        network = self.get_network(network_name)
        network.entrypoint_address = entrypoint_address

        if save:
            self.save_to_json()

    def set_factory(self, network_name: str, factory_address: str, save: bool = True):
        """
        Set Factory address for a network after deployment.

        Args:
            network_name: Network name
            factory_address: Deployed Factory address
            save: Whether to save to config.json immediately
        """
        network = self.get_network(network_name)
        network.factory_address = factory_address

        if save:
            self.save_to_json()

    def has_network(self, network_name: str) -> bool:
        """Check if network is configured."""
        return network_name in self._networks

    def list_networks(self) -> list:
        """List all configured network names."""
        return list(self._networks.keys())

    def remove_network(self, network_name: str, save: bool = True):
        """
        Remove a network configuration.

        Args:
            network_name: Network name to remove
            save: Whether to save to config.json immediately
        """
        if network_name in self._networks:
            del self._networks[network_name]

            if save:
                self.save_to_json()

    # ============================================
    # JSON Persistence
    # ============================================

    def save_to_json(self, path: Optional[str] = None):
        """
        Save configuration to JSON file.

        Args:
            path: Custom path (uses self.config_path if not provided)
        """
        save_path = path or self.config_path

        config_data = {
            'networks': {
                name: network.to_dict()
                for name, network in self._networks.items()
            }
        }

        with open(save_path, 'w') as f:
            json.dump(config_data, f, indent=2)

    def load_from_json(self, path: Optional[str] = None):
        """
        Load configuration from JSON file.

        Args:
            path: Custom path (uses self.config_path if not provided)

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        load_path = path or self.config_path

        if not os.path.exists(load_path):
            raise FileNotFoundError(f"Config file not found: {load_path}")

        with open(load_path, 'r') as f:
            config_data = json.load(f)

        # Clear existing networks
        self._networks.clear()

        # Load networks
        for network_name, network_data in config_data.get('networks', {}).items():
            network_config = NetworkConfig.from_dict(network_data)
            self._networks[network_name] = network_config

    def load_default_networks(self, save: bool = True):
        """
        Load default network configurations.
        This is a convenience method for common networks.

        Args:
            save: Whether to save to config.json after loading
        """
        # Ethereum Sepolia testnet
        self.add_network("sepolia", NetworkConfig(
            chain_id=11155111,
            rpc_url="https://rpc.sepolia.org",
            name="Sepolia Testnet"
        ), save=False)

        # Ethereum Mainnet
        self.add_network("mainnet", NetworkConfig(
            chain_id=1,
            rpc_url="https://eth.llamarpc.com",
            name="Ethereum Mainnet"
        ), save=False)

        # Polygon Mumbai testnet
        self.add_network("mumbai", NetworkConfig(
            chain_id=80001,
            rpc_url="https://rpc-mumbai.maticvigil.com",
            name="Polygon Mumbai"
        ), save=False)

        if save:
            self.save_to_json()

    def __repr__(self):
        return f"<Config networks={list(self._networks.keys())} path={self.config_path}>"
