"""
Unit tests for Config, Account, and Wallet classes.
"""
import os
import json
import tempfile
from backend import Config, NetworkConfig, Account, Wallet, KeyManager


def test_config():
    """Test Config functionality."""
    print("\n" + "=" * 60)
    print("Testing Config Class")
    print("=" * 60)

    # Use a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = f.name

    try:
        # Create config
        config = Config(config_path=config_path)

        # Add network
        config.add_network("test_network", NetworkConfig(
            chain_id=12345,
            rpc_url="https://test-rpc.example.com",
            name="Test Network"
        ), save=True)

        print(f"✓ Added test_network")

        # Verify saved
        assert os.path.exists(config_path), "Config file not created"
        print(f"✓ Config saved to {config_path}")

        # Load and verify
        with open(config_path, 'r') as f:
            data = json.load(f)

        assert "test_network" in data['networks'], "Network not in saved data"
        assert data['networks']['test_network']['chain_id'] == 12345
        print(f"✓ Config data verified")

        # Test retrieval
        network = config.get_network("test_network")
        assert network.chain_id == 12345
        assert network.rpc_url == "https://test-rpc.example.com"
        print(f"✓ Network retrieval works")

        # Test set entry point
        config.set_entry_point("test_network", "0x1234567890123456789012345678901234567890")
        assert config.get_entry_point("test_network") == "0x1234567890123456789012345678901234567890"
        print(f"✓ EntryPoint address set")

        # Test set factory
        config.set_factory("test_network", "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd")
        assert config.get_factory("test_network") == "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
        print(f"✓ Factory address set")

        print("\n✅ Config tests passed!")

    finally:
        # Cleanup
        if os.path.exists(config_path):
            os.remove(config_path)


def test_account():
    """Test Account functionality."""
    print("\n" + "=" * 60)
    print("Testing Account Class")
    print("=" * 60)

    # Create a test account (without actual RPC connection)
    owners = [
        "0x1111111111111111111111111111111111111111",
        "0x2222222222222222222222222222222222222222",
        "0x3333333333333333333333333333333333333333"
    ]

    guardians = [
        "0x4444444444444444444444444444444444444444",
        "0x5555555555555555555555555555555555555555"
    ]

    account = Account(
        network_name="test",
        contract_address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        owners=owners,
        threshold=2,
        guardians=guardians,
        guardian_threshold=2,
        rpc_url="https://test-rpc.example.com"  # Won't actually connect in this test
    )

    print(f"✓ Account created: {account.contract_address}")

    # Test validation
    assert account.threshold == 2
    assert len(account.owners) == 3
    assert len(account.guardians) == 2
    print(f"✓ Account configuration validated")

    # Test to_dict / from_dict
    account_dict = account.to_dict()
    assert account_dict['contract_address'] == account.contract_address
    print(f"✓ Account serialization works")

    account2 = Account.from_dict(account_dict)
    assert account2.contract_address == account.contract_address
    assert account2.threshold == account.threshold
    print(f"✓ Account deserialization works")

    # Test invalid configurations
    try:
        invalid_account = Account(
            network_name="test",
            contract_address="0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            owners=owners,
            threshold=5,  # Invalid: threshold > owners
            rpc_url="https://test-rpc.example.com"
        )
        print("✗ Should have raised ValueError for invalid threshold")
    except ValueError:
        print(f"✓ Invalid threshold correctly rejected")

    print("\n✅ Account tests passed!")


def test_wallet():
    """Test Wallet functionality."""
    print("\n" + "=" * 60)
    print("Testing Wallet Class")
    print("=" * 60)

    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        keystore_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        wallet_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = f.name

    try:
        # Create KeyManager
        km = KeyManager(storage_path=keystore_path)
        address = km.create_new_key("test_password")
        km.unlock("test_password")
        print(f"✓ KeyManager created: {address}")

        # Create Config
        config = Config(config_path=config_path)
        config.add_network("test", NetworkConfig(
            chain_id=12345,
            rpc_url="https://test-rpc.example.com",
            name="Test Network"
        ))
        print(f"✓ Config created with test network")

        # Create Wallet
        wallet = Wallet(
            key_manager=km,
            wallet_name="test_wallet",
            storage_path=wallet_path,
            auto_load=False
        )
        print(f"✓ Wallet created: {wallet.wallet_name}")

        # Add account
        owners = [
            km.address,
            "0x2222222222222222222222222222222222222222",
            "0x3333333333333333333333333333333333333333"
        ]

        account = wallet.add_account(
            network_name="test",
            contract_address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            owners=owners,
            threshold=2,
            save=True
        )
        print(f"✓ Account added to wallet")

        # Verify saved
        assert os.path.exists(wallet_path), "Wallet file not created"
        print(f"✓ Wallet saved to {wallet_path}")

        # Load and verify
        with open(wallet_path, 'r') as f:
            data = json.load(f)

        assert "test" in data['accounts'], "Account not in saved data"
        assert data['accounts']['test']['contract_address'] == account.contract_address
        print(f"✓ Wallet data verified")

        # Test retrieval
        retrieved_account = wallet.get_account("test")
        assert retrieved_account.contract_address == account.contract_address
        print(f"✓ Account retrieval works")

        # Test list networks
        networks = wallet.list_networks()
        assert "test" in networks
        print(f"✓ List networks works")

        # Test summary
        summary = wallet.summary()
        assert summary['wallet_name'] == "test_wallet"
        assert summary['key_manager_address'] == km.address
        assert 'test' in summary['accounts']
        print(f"✓ Wallet summary works")

        print("\n✅ Wallet tests passed!")

    finally:
        # Cleanup
        for path in [keystore_path, wallet_path, config_path]:
            if os.path.exists(path):
                os.remove(path)

        # Reset Config singleton for next test
        Config._instance = None


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Running Nexus Wallet Tests")
    print("=" * 60)

    try:
        test_config()
        test_account()
        test_wallet()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
