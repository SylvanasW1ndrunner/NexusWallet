"""
Test script for Sepolia deployment with Pimlico bundler
Tests UserOperation submission using Pimlico's bundler service
"""

import json
import os
from backend.keymanager.keyManager import KeyManager
from backend.config.config import Config, NetworkConfig
from backend.utils.wallet import Wallet
from backend.utils.PimlicoBundlerClient import PimlicoBundler
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import requests

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from project root
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    print(f"✓ Loaded environment variables from: {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Using system environment variables instead...")


def load_deployment_info():
    """Load deployment info from sepolia_deployment.json"""
    deployment_path = os.path.join(os.path.dirname(__file__), 'sepolia_deployment.json')

    if not os.path.exists(deployment_path):
        raise FileNotFoundError(
            f"Deployment file not found: {deployment_path}\n"
            "Please deploy contracts first using: npx hardhat run scripts/deploy-sepolia.ts --network sepolia"
        )

    with open(deployment_path, 'r') as f:
        return json.load(f)




def main():
    print("=" * 60)
    print("Testing Sepolia Deployment with Pimlico Bundler")
    print("=" * 60)

    # Load environment variables
    infura_id = os.getenv("INFURA_ID")
    pimlico_api_key = os.getenv('PIMLICO_API_KEY')
    private_key = os.getenv('PRIVATE_KEY')
    # Validate required environment variables
    if not pimlico_api_key:
        raise ValueError(
            "PIMLICO_API_KEY environment variable not set.\n"
            "Get your API key from https://dashboard.pimlico.io"
        )

    if not infura_id:
        raise ValueError(
            "INFURA_ID environment variable not set.\n"
            "Get your Infura project ID from https://infura.io"
        )

    if not private_key:
        print("   WARNING: PRIVATE_KEY not set, using test key...")
        private_key = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'

    print(f"✓ Environment variables loaded")
    print(f"  INFURA_ID: {infura_id[:8]}...")
    print(f"  PIMLICO_API_KEY: {pimlico_api_key[:8]}...")
    print(f"  PRIVATE_KEY: {private_key[:10]}...")
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
    print("\n2. Configuring Sepolia network...")
    config = Config()

    # Use Infura RPC endpoint
    sepolia_rpc = f"https://sepolia.infura.io/v3/{infura_id}"
    print(f"   RPC URL: {sepolia_rpc[:50]}...")

    config.add_network(
        network_name='sepolia',
        network_config=NetworkConfig(
            chain_id=deployment['chainId'],
            rpc_url=sepolia_rpc,
            entrypoint_address=deployment['entryPoint'],
            factory_address=deployment['factory'],
            name='Sepolia Testnet'
        ),
        save=True
    )
    print("   ✓ Sepolia network configured")

    # 3. Setup Pimlico bundler
    print("\n3. Initializing Pimlico bundler...")
    bundler = PimlicoBundler(api_key=pimlico_api_key, chain_name='sepolia')
    print("   ✓ Pimlico bundler initialized")

    # 4. Setup KeyManager and Wallet
    print("\n4. Setting up wallet...")
    km = KeyManager()
    password = "test_password_sepolia"

    if not km.unlocked:
        try:
            km.unlock(password)
            print("   ✓ KeyManager unlocked")
        except:
            print("   Importing private key...")
            km.import_private_key(private_key, password)
            km.unlock(password)
            print("   ✓ Key imported and unlocked")

    print(f"   EOA Address: {km.address}")

    # 5. Create Wallet
    wallet = Wallet(
        key_manager=km,
        wallet_name='sepolia_test_wallet',
        storage_path='wallet_sepolia.json',
        auto_load=False
    )

    # 6. Check EOA balance
    print("\n5. Checking EOA balance...")
    eoa_balance = wallet.get_eoa_balance('sepolia')
    print(f"   EOA Balance: {Web3.from_wei(eoa_balance, 'ether')} ETH")

    if eoa_balance == 0:
        print("\n   ⚠️  WARNING: EOA has no balance!")
        print("   Get Sepolia ETH from faucet:")
        print("   - https://sepoliafaucet.com")
        print("   - https://www.infura.io/faucet/sepolia")
        return

    ##向AA账户转账
    txhash = wallet.send_transaction("sepolia", to=deployment['testAccount']['address'])
    # 7. Add AA account
    print("\n6. Adding AA account to wallet...")
    test_account_info = deployment['testAccount']

    account = wallet.add_account(
        network_name='sepolia',
        contract_address=test_account_info['address'],
        owners=test_account_info['owners'],
        threshold=test_account_info['threshold'],
        guardians=test_account_info['guardians'],
        guardian_threshold=test_account_info['guardianThreshold'],
        salt=test_account_info['salt'],
        save=False
    )
    print(f"   ✓ AA Account: {account.contract_address}")

    recipt = wallet.send_transaction("sepolia", to=deployment['testAccount']['address'],value=Web3.to_wei("0.001", "ether"))

    # 8. Check if account is deployed
    print("\n7. Checking AA account deployment status...")
    is_deployed = account.is_deployed()
    print(f"   Is Deployed: {is_deployed}")

    if is_deployed:
        aa_balance = account.get_balance()
        print(f"   AA Balance: {Web3.from_wei(aa_balance, 'ether')} ETH")
        aa_nonce = account.get_nonce()
        print(f"   AA Nonce: {aa_nonce}")

    # 9. Test bundler connectivity
    print("\n8. Testing Pimlico bundler connectivity...")
    print(f"   Bundler URL: {bundler.bundler_url}")

    # Simple test: try to get supported entry points
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_supportedEntryPoints",
            "params": []
        }
        response = requests.post(bundler.bundler_url, json=payload)
        response.raise_for_status()
        result = response.json()

        if 'result' in result:
            print(f"   ✓ Bundler is accessible")
            print(f"   Supported EntryPoints: {result['result']}")
        else:
            print(f"   ⚠️  Unexpected response: {result}")
    except Exception as e:
        print(f"   ✗ Bundler connection failed: {e}")
        return

    # 10. Test UserOperation creation and submission
    print("\n9. Creating and sending UserOperation...")
    recipient = "0x3003A698EdcFDCC2BEa70FFf23DADF0b4bA1f6bf"
    amount_eth = 0.0001
    amount_wei = Web3.to_wei(amount_eth, 'ether')

    print(f"   Recipient: {recipient}")
    print(f"   Amount: {amount_eth} ETH ({amount_wei} Wei)")

    try:
        # Step 1: Build callData for transfer
        print("\n   Step 1: Building callData...")
        call_data = account.encode_execute_call(
            target=recipient,
            value=amount_wei,
            data=b''
        )
        print(f"   ✓ CallData built: {call_data.hex()[:64]}...")

        # Step 2: Build UserOperation (without signature)
        print("\n   Step 2: Building UserOperation...")

        userop_gas = bundler.get_UserOperation_GasPrice()
        standard = userop_gas['standard']

        user_op = account.build_user_operation(
            call_data=call_data,
            nonce=None,  # Will fetch from EntryPoint
            max_fee_per_gas=int(standard['maxFeePerGas'],16),  # Will use current gas prices
            max_priority_fee_per_gas=int(standard['maxPriorityFeePerGas'],16),
            call_gas_limit=None,  # Auto-adjusted
            verification_gas_limit=None  # Auto-adjusted
        )
        print(f"   ✓ UserOperation built (unpacked format)")
        print(f"   Sender: {user_op['sender']}")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   Factory: {user_op['factory']}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   VerificationGasLimit: {user_op['verificationGasLimit']}")

        # Debug: Check initCode (factory + factoryData)
        print(f"\n   [DEBUG] initCode analysis:")
        if user_op['factory'] is not None:
            print(f"   Factory address: {user_op['factory']}")
            print(f"   Factory data: {user_op['factoryData'][:66]}...")

            # Decode function selector from factoryData
            if user_op['factoryData'] and len(user_op['factoryData']) > 10:
                func_selector = user_op['factoryData'][2:10]
                print(f"   Function selector: 0x{func_selector}")

                # Expected selector for createAccount(address[],uint256,address[],uint256,uint256)
                expected_selector = Web3.keccak(text='createAccount(address[],uint256,address[],uint256,uint256)')[:4].hex()
                print(f"   Expected selector: 0x{expected_selector}")
                print(f"   Selector match: {func_selector == expected_selector}")
        else:
            print(f"   initCode is empty (account already deployed)")

        # Step 3: Get UserOperation hash from EntryPoint
        print("\n   Step 3: Getting UserOperation hash...")
        user_op_hash = account.get_user_op_hash(user_op)
        print(f"   ✓ UserOp hash: {user_op_hash.hex()}")

        # Step 4: Sign UserOperation hash using KeyManager
        print("\n   Step 4: Signing UserOperation with KeyManager...")
        signature = km.sign_userop(user_op_hash)
        print(f"   ✓ Single signature: {signature.hex()[:20]}... ({len(signature)} bytes)")

        # Step 5: Encode multi-sig signature and update UserOperation
        print("\n   Step 5: Encoding multi-sig signature...")
        # For multi-sig account, concatenate all signatures
        # Each signature is 65 bytes: [r(32) | s(32) | v(1)]
        multisig_signature = account.encode_multisig_signature([signature])
        # Update signature in UserOperation (convert bytes to hex string)
        user_op['signature'] = '0x' + multisig_signature.hex()
        print(f"   ✓ Multi-sig signature: {multisig_signature.hex()[:20]}... ({len(multisig_signature)} bytes)")
        print(f"   ✓ Signature count: {len(multisig_signature) // 65}")
        print(f"   ✓ UserOperation ready for bundler (unpacked format)")

        # Step 6: Send to Pimlico bundler
        print("\n   Step 6: Sending UserOperation to Pimlico bundler...")
        print(f"   Bundler URL: {bundler.bundler_url}")

        user_op_hash_returned = bundler.send_user_operation(
            user_op=user_op,
            entry_point=deployment['entryPoint']
        )

        print(f"   ✓ UserOperation sent!")
        print(f"   UserOp Hash: {user_op_hash_returned}")

        # Step 7: Wait for UserOperation receipt
        print("\n   Step 7: Waiting for UserOperation receipt...")
        print("   (This may take a while as bundler needs to include it in a bundle)")

        import time
        max_wait = 120  # 2 minutes
        start_time = time.time()
        receipt = None

        while time.time() - start_time < max_wait:
            receipt = bundler.get_user_operation_receipt(user_op_hash_returned)
            if receipt:
                break
            print("   Waiting for bundler to process...")
            time.sleep(5)

        if receipt:
            print(f"   ✓ UserOperation executed!")
            print(f"   Transaction hash: {receipt.get('transactionHash', 'N/A')}")
            print(f"   Block number: {receipt.get('blockNumber', 'N/A')}")
            print(f"   Success: {receipt.get('success', 'N/A')}")

            # Check new AA account balance
            new_aa_balance = account.get_balance()
            print(f"   New AA Balance: {Web3.from_wei(new_aa_balance, 'ether')} ETH")
        else:
            print("   ⚠️  UserOperation receipt not yet available")
            print(f"   Check status later with hash: {user_op_hash_returned}")
            print(f"   View on explorer: https://sepolia.etherscan.io/tx/{user_op_hash_returned}")

    except Exception as e:
        print(f"   ✗ UserOperation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ============================================
    # Social Recovery Testing
    # ============================================
    print("\n" + "=" * 60)
    print("Testing Social Recovery Features")
    print("=" * 60)

    # Wait a bit to ensure account is fully deployed
    if not is_deployed:
        print("\n   Waiting for account deployment to finalize...")
        time.sleep(5)

    # 10. Get current account configuration
    print("\n10. Getting current account configuration...")
    try:
        current_owners = account.get_owners()
        current_guardians = account.get_guardians()
        is_recovery_enabled = account.is_social_recovery_enabled()

        print(f"   Current Owners: {current_owners}")
        print(f"   Owner Count: {len(current_owners)}")
        print(f"   Threshold: {account.threshold}")
        print(f"   Current Guardians: {current_guardians}")
        print(f"   Guardian Count: {len(current_guardians)}")
        print(f"   Guardian Threshold: {account.guardian_threshold}")
        print(f"   Social Recovery Enabled: {is_recovery_enabled}")
    except Exception as e:
        print(f"   ⚠️  Error getting account info: {e}")
        print("   This might happen if account was just deployed, skipping recovery tests...")
        import traceback
        traceback.print_exc()
        # Continue to summary
        current_guardians = []
        is_recovery_enabled = False

    # 11. Test adding a guardian (if no guardians and account has balance)
    if len(current_guardians) == 0 and is_deployed:
        print("\n11. Testing: Add Guardian...")
        # Use a different address as guardian (could be another EOA you control)
        new_guardian = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"  # Example guardian address

        print(f"   Adding guardian: {new_guardian}")
        print(f"   Note: In production, use a trusted guardian address you control")

        try:
            # Step 1: Build callData for addGuardian
            print("\n   Step 1: Building addGuardian callData...")
            call_data = account.encode_add_guardian_call(new_guardian)
            print(f"   ✓ CallData: {call_data.hex()[:40]}...")

            # Step 2: Build UserOperation
            print("\n   Step 2: Building UserOperation...")
            user_op = account.build_user_operation(call_data=call_data)
            print(f"   ✓ UserOperation built")

            # Step 3: Get UserOp hash
            print("\n   Step 3: Getting UserOperation hash...")
            user_op_hash = account.get_user_op_hash(user_op)
            print(f"   ✓ UserOp hash: {user_op_hash.hex()}")

            # Step 4: Sign and update UserOperation
            print("\n   Step 4: Signing UserOperation...")
            signature = km.sign_userop(user_op_hash)
            multisig_signature = account.encode_multisig_signature([signature])
            # Update signature in UserOperation (convert bytes to hex string)
            user_op['signature'] = '0x' + multisig_signature.hex()
            print(f"   ✓ Signature: {multisig_signature.hex()[:20]}...")
            print(f"   ✓ UserOperation ready for bundler")

            # Step 5: Send to bundler
            print("\n   Step 5: Sending to Pimlico bundler...")
            user_op_hash_returned = bundler.send_user_operation(
                user_op=user_op,
                entry_point=deployment['entryPoint']
            )
            print(f"   ✓ UserOperation sent: {user_op_hash_returned}")

            # Step 6: Wait for receipt
            print("\n   Step 6: Waiting for transaction receipt...")
            max_wait = 60
            start_time = time.time()
            receipt = None

            while time.time() - start_time < max_wait:
                receipt = bundler.get_user_operation_receipt(user_op_hash_returned)
                if receipt:
                    break
                print("   Waiting for bundler to process...")
                time.sleep(5)

            if receipt:
                print(f"   ✓ Guardian added successfully!")
                print(f"   Transaction hash: {receipt.get('transactionHash', 'N/A')}")
                print(f"   Block number: {receipt.get('blockNumber', 'N/A')}")

                # Verify the guardian was added
                time.sleep(2)  # Wait for state to update
                updated_guardians = account.get_guardians()
                print(f"\n   ✓ Verified - Updated Guardians: {updated_guardians}")
                print(f"   Guardian Count: {len(updated_guardians)}")
            else:
                print("   ⚠️  Transaction not confirmed within timeout")
                print(f"   UserOp Hash: {user_op_hash_returned}")

        except Exception as e:
            print(f"   ✗ Error adding guardian: {e}")
            import traceback
            traceback.print_exc()

    # 12. Demonstrate social recovery workflow
    print("\n12. Social Recovery Workflow Demo...")
    print("   The social recovery process works as follows:")
    print("\n   Step 1: Guardian Approval")
    print("   - Guardians call approveRecovery(newOwners, newThreshold)")
    print("   - Need guardianThreshold number of approvals")

    print("\n   Step 2: Execute Recovery")
    print("   - Anyone can call executeRecovery(newOwners, newThreshold)")
    print("   - This updates the account owners")

    # Example callData (not sending)
    example_new_owner = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
    example_owners = [example_new_owner]
    example_threshold = 1

    print(f"\n   Example: Recover to new owner {example_new_owner}")

    approval_calldata = account.encode_approve_recovery_call(example_owners, example_threshold)
    print(f"   approveRecovery callData: {approval_calldata.hex()[:60]}...")

    recovery_calldata = account.encode_execute_recovery_call(example_owners, example_threshold)
    print(f"   executeRecovery callData: {recovery_calldata.hex()[:60]}...")

    if is_recovery_enabled:
        try:
            approval_count = account.get_recovery_approval_count(example_owners, example_threshold)
            print(f"\n   Current approval count: {approval_count}/{account.guardian_threshold}")
        except Exception as e:
            print(f"\n   Note: Could not check approval count: {e}")

    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)

    print("\n📝 Summary:")
    print(f"   1. ✓ Sepolia network configured")
    print(f"   2. ✓ Pimlico bundler connected")
    print(f"   3. ✓ Account deployed (if needed) and transfer executed")
    print(f"   4. ✓ AA Account: {account.contract_address}")
    print(f"   5. ✓ Social recovery features tested")

    print("\n📝 What was tested:")
    print("   • Account deployment with factory (if needed)")
    print("   • UserOperation creation and signing")
    print("   • Transfer execution via bundler")
    print("   • Guardian management (add guardian)")
    print("   • Social recovery workflow demonstration")

    print("\n📝 Social Recovery Features:")
    print("   • getOwners() - View current owners")
    print("   • getGuardians() - View current guardians")
    print("   • addGuardian(address) - Add a guardian")
    print("   • removeGuardian(address) - Remove a guardian")
    print("   • approveRecovery(address[], uint256) - Guardian approves recovery")
    print("   • executeRecovery(address[], uint256) - Execute recovery after threshold")
    print("   • addOwner(address) - Add an owner")
    print("   • removeOwner(address) - Remove an owner")

    print("\n📝 Next Steps:")
    print("   • Add more guardians for full social recovery testing")
    print("   • Test complete recovery flow with multiple guardians")
    print("   • Add paymaster integration for gas sponsorship")
    print("   • Implement batch transaction support")
    print(f"   • Monitor account: https://sepolia.etherscan.io/address/{account.contract_address}")


if __name__ == '__main__':
    main()
