"""
Test script for local Hardhat deployment
This script tests the integration between deployed contracts and the Python backend
"""

import json
import os
from backend.keymanager.keyManager import KeyManager
from backend.config import Config, NetworkConfig
from backend.wallet import Wallet
from web3 import Web3


def load_deployment_info():
    """Load deployment info from local_deployment.json"""
    deployment_path = os.path.join(os.path.dirname(__file__), 'local_deployment.json')

    if not os.path.exists(deployment_path):
        raise FileNotFoundError(
            f"Deployment file not found: {deployment_path}\n"
            "Please deploy contracts first using: npx hardhat run scripts/deploy-local.ts --network localhost"
        )

    with open(deployment_path, 'r') as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("Testing Local Hardhat Deployment Integration")
    print("=" * 60)

    # 1. Load deployment info
    print("\n1. Loading deployment configuration...")
    deployment = load_deployment_info()
    print(f"   Network: {deployment['network']}")
    print(f"   Chain ID: {deployment['chainId']}")
    print(f"   EntryPoint: {deployment['entryPoint']}")
    print(f"   Factory: {deployment['factory']}")
    print(f"   Test Account: {deployment['testAccount']['address']}")

    # 2. Configure network in Config
    print("\n2. Configuring network in Config singleton...")
    config = Config()
    netconfig = NetworkConfig.from_dict({
        'chain_id':deployment['chainId'],
        'rpc_url':'http://127.0.0.1:8545',
        'entrypoint_address':deployment['entryPoint'],
        'factory_address':deployment['factory'],
        'name':'localhost'

    })
    config.add_network(
        network_name='localhost',
        network_config=netconfig,
        save=True
    )
    config.set_entry_point('localhost', deployment['entryPoint'], save=True)
    config.set_factory('localhost', deployment['factory'], save=True)
    print("   ✓ Network configured")

    # 3. Create or load KeyManager
    print("\n3. Setting up KeyManager...")
    km = KeyManager()

    # Use Hardhat's first test account private key
    # Hardhat default mnemonic: "test test test test test test test test test test test junk"
    # First account: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
    # Private key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
    hardhat_test_key = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'

    if not km.unlocked:
        password = "test_password_123"
        try:
            # Try to unlock existing key
            km.unlock(password)
            print(f"   ✓ KeyManager unlocked")
        except:
            # Import Hardhat test account private key
            print("   Importing Hardhat test account...")
            km.import_private_key(hardhat_test_key, password)
            km.unlock(password)
            print(f"   ✓ Key imported and unlocked")

    print(f"   EOA Address: {km.address}")

    # 4. Create Wallet
    print("\n4. Creating Wallet...")
    wallet = Wallet(
        key_manager=km,
        wallet_name='test_wallet',
        storage_path='wallet_test.json',
        auto_load=False  # Don't auto-load for testing
    )
    print("   ✓ Wallet created")

    # 5. Test EOA operations
    print("\n5. Testing EOA operations...")

    # Check EOA balance on localhost
    eoa_balance = wallet.get_eoa_balance('localhost')
    print(f"   EOA Balance: {Web3.from_wei(eoa_balance, 'ether')} ETH")

    eoa_nonce = wallet.get_eoa_nonce('localhost')
    print(f"   EOA Nonce: {eoa_nonce}")

    # 6. Add AA account to wallet
    print("\n6. Adding AA account to wallet...")
    test_account_info = deployment['testAccount']

    account = wallet.add_account(
        network_name='localhost',
        contract_address=test_account_info['address'],
        owners=test_account_info['owners'],
        threshold=test_account_info['threshold'],
        guardians=test_account_info['guardians'],
        guardian_threshold=test_account_info['guardianThreshold'],
        save=False  # Don't save for testing
    )
    print(f"   ✓ AA Account added: {account.contract_address}")

    # 7. Test AA account queries
    print("\n7. Testing AA account operations...")

    is_deployed = account.is_deployed()
    print(f"   Is Deployed: {is_deployed}")

    if is_deployed:
        aa_balance = account.get_balance()
        print(f"   AA Balance: {Web3.from_wei(aa_balance, 'ether')} ETH")

        aa_nonce = account.get_nonce()
        print(f"   AA Nonce: {aa_nonce}")
    else:
        print("   Note: Account not yet deployed (counterfactual address)")
        print("   To deploy, send a UserOperation or call factory.createAccount()")

    # 8. Test wallet summary
    print("\n8. Wallet Summary:")
    summary = wallet.summary()
    print(f"   Wallet Name: {summary['wallet_name']}")
    print(f"   EOA Address: {summary['eoa_address']}")
    print(f"   KeyManager Unlocked: {summary['key_manager_unlocked']}")
    print(f"   Networks: {list(summary['aa_accounts'].keys())}")
    print(f"   Total AA Accounts: {sum(len(accs) for accs in summary['aa_accounts'].values())}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

    print("\n📝 Next Steps:")
    print("   1. The AA account is at a counterfactual address (not yet deployed)")
    print("   2. To deploy it, you need to:")
    print("      - Fund the account address with ETH for gas")
    print("      - Send a UserOperation through the EntryPoint")
    print("      - Or call factory.createAccount() directly")
    print("   3. After deployment, you can send UserOperations through the account")


if __name__ == '__main__':
    main()
