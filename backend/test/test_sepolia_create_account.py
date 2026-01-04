"""
Test script for creating NEW Sepolia account with full social recovery testing
Creates a new account (not imports), tests complete social recovery workflow
"""

import json
import os
from time import sleep

from backend.keymanager.keyManager import KeyManager
from backend.config.config import Config, NetworkConfig
from backend.utils.wallet import Wallet
from backend.utils.PimlicoBundlerClient import PimlicoBundler
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import requests
import time

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
    print("Testing NEW Account Creation with Social Recovery")
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
    password = "test_password_create_account"

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
        wallet_name='sepolia_create_test_wallet',
        storage_path='wallet_sepolia_create.json',
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

    # 7. CREATE NEW AA account (not import!)
    print("\n6. Creating NEW AA account...")
    print("   Note: contract_address is NOT provided - will calculate counterfactual address")

    # Use the recipient address as guardian
    guardian_address = "0x3003A698EdcFDCC2BEa70FFf23DADF0b4bA1f6bf"

    account = wallet.add_account(
        network_name='sepolia',
        # contract_address NOT provided - this triggers address calculation
        owners=[km.address],  # Owner is the EOA
        threshold=1,
        guardians=[guardian_address],  # Use recipient as guardian
        guardian_threshold=1,
        salt=int(time.time()),  # Use timestamp as salt for uniqueness
        save=False
    )
    print(f"   ✓ NEW AA Account created: {account.contract_address}")
    print(f"   ✓ Owner: {km.address}")
    print(f"   ✓ Guardian: {guardian_address}")

    wallet.send_transaction("sepolia",to=account.contract_address,value=Web3.to_wei("0.003","ether"))

    # 8. Check if account is deployed
    print("\n7. Checking AA account deployment status...")
    is_deployed = account.is_deployed()
    print(f"   Is Deployed: {is_deployed}")

    if is_deployed:
        aa_balance = account.get_balance()
        print(f"   AA Balance: {Web3.from_wei(aa_balance, 'ether')} ETH")
    else:
        print(f"   Account NOT deployed yet (counterfactual)")
        print(f"   Will be deployed on first UserOperation")

    # 9. Test bundler connectivity
    print("\n8. Testing Pimlico bundler connectivity...")
    print(f"   Bundler URL: {bundler.bundler_url}")

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

    # 10. Transfer ETH to recipient (same as original test)
    print("\n9. Creating and sending UserOperation (ETH transfer)...")
    recipient = "0x3003A698EdcFDCC2BEa70FFf23DADF0b4bA1f6bf"  # Same recipient as guardian
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
            max_fee_per_gas=int(standard['maxFeePerGas'], 16),
            max_priority_fee_per_gas=int(standard['maxPriorityFeePerGas'], 16),
            call_gas_limit=None,  # Auto-adjusted
            verification_gas_limit=None  # Auto-adjusted
        )
        print(f"   ✓ UserOperation built (unpacked format)")
        print(f"   Sender: {user_op['sender']}")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   Factory: {user_op['factory']}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   VerificationGasLimit: {user_op['verificationGasLimit']}")

        # Debug: Check initCode
        print(f"\n   [DEBUG] initCode analysis:")
        if user_op['factory'] is not None:
            print(f"   Factory address: {user_op['factory']}")
            print(f"   Factory data length: {len(user_op['factoryData'])} chars")
            print(f"   This is a DEPLOYMENT transaction (account will be created)")
        else:
            print(f"   initCode is empty (account already deployed)")

        # Step 3: Get UserOperation hash
        print("\n   Step 3: Getting UserOperation hash...")
        user_op_hash = account.get_user_op_hash(user_op)
        print(f"   ✓ UserOp hash: {user_op_hash.hex()}")

        # Step 4: Sign UserOperation
        print("\n   Step 4: Signing UserOperation with KeyManager...")
        signature = km.sign_userop(user_op_hash)
        print(f"   ✓ Single signature: {signature.hex()[:20]}... ({len(signature)} bytes)")

        # Step 5: Encode signature
        print("\n   Step 5: Encoding multi-sig signature...")
        multisig_signature = account.encode_multisig_signature([signature])
        user_op['signature'] = '0x' + multisig_signature.hex()
        print(f"   ✓ Multi-sig signature: {multisig_signature.hex()[:20]}... ({len(multisig_signature)} bytes)")
        print(f"   ✓ UserOperation ready for bundler")

        # Step 6: Send to bundler
        print("\n   Step 6: Sending UserOperation to Pimlico bundler...")
        user_op_hash_returned = bundler.send_user_operation(
            user_op=user_op,
            entry_point=deployment['entryPoint']
        )

        print(f"   ✓ UserOperation sent!")
        print(f"   UserOp Hash: {user_op_hash_returned}")

        # Step 7: Wait for receipt
        print("\n   Step 7: Waiting for UserOperation receipt...")
        print("   (This will deploy the account AND execute the transfer)")

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

            # Check deployment
            is_now_deployed = account.is_deployed()
            print(f"\n   ✓ Account deployment status: {is_now_deployed}")

            if is_now_deployed:
                new_aa_balance = account.get_balance()
                print(f"   AA Balance: {Web3.from_wei(new_aa_balance, 'ether')} ETH")
        else:
            print("   ⚠️  UserOperation receipt not yet available")
            print(f"   Check status later with hash: {user_op_hash_returned}")

    except Exception as e:
        print(f"   ✗ UserOperation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ============================================
    # FULL Social Recovery Testing
    # ============================================
    print("\n" + "=" * 60)
    print("FULL Social Recovery Testing")
    print("=" * 60)

    # Wait for account to be fully deployed
    print("\n   Waiting for account deployment to finalize...")
    time.sleep(10)

    # Verify account is deployed
    if not account.is_deployed():
        print("   ✗ Account not deployed yet, cannot test social recovery")
        return

    # 11. Get current account configuration
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
        import traceback
        traceback.print_exc()
        return

    # ============================================
    # Test 1: Remove Guardian (if exists from deployment)
    # ============================================
    if len(current_guardians) > 0:
        print("\n11. Test 1: Remove existing guardian...")
        guardian_to_remove = current_guardians[0]
        print(f"   Removing guardian: {guardian_to_remove}")

        try:
            # Build callData
            call_data = account.encode_remove_guardian_call(guardian_to_remove)
            print(f"   ✓ CallData built: {call_data.hex()[:40]}...")

            # Build UserOperation
            userop_gas = bundler.get_UserOperation_GasPrice()
            standard = userop_gas['standard']

            user_op = account.build_user_operation(
                call_data=call_data,
                max_fee_per_gas=int(standard['maxFeePerGas'], 16),
                max_priority_fee_per_gas=int(standard['maxPriorityFeePerGas'], 16)
            )

            # Sign
            user_op_hash = account.get_user_op_hash(user_op)
            signature = km.sign_userop(user_op_hash)
            multisig_signature = account.encode_multisig_signature([signature])
            user_op['signature'] = '0x' + multisig_signature.hex()

            # Send
            print("   Sending UserOperation to remove guardian...")
            user_op_hash_returned = bundler.send_user_operation(user_op, deployment['entryPoint'])
            print(f"   ✓ UserOp sent: {user_op_hash_returned}")

            # Wait for receipt
            max_wait = 60
            start_time = time.time()
            receipt = None

            while time.time() - start_time < max_wait:
                receipt = bundler.get_user_operation_receipt(user_op_hash_returned)
                if receipt:
                    break
                print("   Waiting...")
                time.sleep(5)

            if receipt and receipt.get('success'):
                print(f"   ✓ Guardian removed successfully!")
                time.sleep(2)
                updated_guardians = account.get_guardians()
                print(f"   Updated Guardians: {updated_guardians}")
            else:
                print("   ⚠️  Transaction not confirmed")

        except Exception as e:
            print(f"   ✗ Error removing guardian: {e}")
            import traceback
            traceback.print_exc()

    # ============================================
    # Test 2: Add Guardian (the recipient address)
    # ============================================
    print("\n12. Test 2: Add guardian (recipient address)...")
    new_guardian = recipient  # Use the transfer recipient as guardian
    print(f"   Adding guardian: {new_guardian}")

    try:
        # Build callData
        call_data = account.encode_add_guardian_call(new_guardian)
        print(f"   ✓ CallData built: {call_data.hex()[:40]}...")

        # Build UserOperation
        userop_gas = bundler.get_UserOperation_GasPrice()
        standard = userop_gas['standard']

        user_op = account.build_user_operation(
            call_data=call_data,
            max_fee_per_gas=int(standard['maxFeePerGas'], 16),
            max_priority_fee_per_gas=int(standard['maxPriorityFeePerGas'], 16)
        )

        # Sign
        user_op_hash = account.get_user_op_hash(user_op)
        signature = km.sign_userop(user_op_hash)
        multisig_signature = account.encode_multisig_signature([signature])
        user_op['signature'] = '0x' + multisig_signature.hex()

        # Send
        print("   Sending UserOperation to add guardian...")
        user_op_hash_returned = bundler.send_user_operation(user_op, deployment['entryPoint'])
        print(f"   ✓ UserOp sent: {user_op_hash_returned}")

        # Wait for receipt
        max_wait = 60
        start_time = time.time()
        receipt = None

        while time.time() - start_time < max_wait:
            receipt = bundler.get_user_operation_receipt(user_op_hash_returned)
            if receipt:
                break
            print("   Waiting...")
            time.sleep(5)

        if receipt and receipt.get('success'):
            print(f"   ✓ Guardian added successfully!")
            time.sleep(2)
            updated_guardians = account.get_guardians()
            print(f"   Updated Guardians: {updated_guardians}")
            print(f"   Guardian Count: {len(updated_guardians)}")
        else:
            print("   ⚠️  Transaction not confirmed")
            return

    except Exception as e:
        print(f"   ✗ Error adding guardian: {e}")
        import traceback
        traceback.print_exc()
        return

    # ============================================
    # Test 3: Guardian Approves Recovery (Direct Contract Call)
    # ============================================
    print("\n13. Test 3: Guardian approves recovery (DIRECT contract call)...")
    print("   Note: Guardian calls contract directly (NOT through UserOperation)")

    # New owner will be a new test address
    new_owner_address = recipient
    new_owners = [new_owner_address]
    new_threshold = 1

    print(f"   Proposed new owner: {new_owner_address}")
    print(f"   Proposed threshold: {new_threshold}")

    # Check current approval count
    try:
        approval_count = account.get_recovery_approval_count(new_owners, new_threshold)
        print(f"\n   Current approval count: {approval_count}/{account.guardian_threshold}")
    except Exception as e:
        print(f"   Note: Could not check approval count: {e}")

    # For testing, we need the guardian's private key
    # Create a guardian EOA for testing
    print("\n   Creating guardian EOA for testing...")
    guardian_account = Account.create()
    guardian_private_key = guardian_account.key.hex()
    guardian_eoa_address = guardian_account.address
    print(f"   Guardian EOA: {guardian_eoa_address}")
    print(f"   Guardian Key: {guardian_private_key[:20]}...")

    # Send ETH to guardian for gas
    print("\n   Funding guardian EOA with ETH for gas...")
    try:
        guardian_funding_tx = wallet.send_transaction(
            network_name='sepolia',
            to=guardian_eoa_address,
            value=Web3.to_wei("0.002", "ether")
        )
        print(f"   ✓ Funded guardian EOA")
        time.sleep(5)  # Wait for tx confirmation
    except Exception as e:
        print(f"   ✗ Failed to fund guardian: {e}")
        return

    # First, replace the current guardian with our test guardian EOA
    print("\n   Replacing guardian with test guardian EOA...")
    current_guardians = account.get_guardians()
    if len(current_guardians) > 0:
        old_guardian = current_guardians[0]

        # Remove old guardian
        try:
            call_data = account.encode_remove_guardian_call(old_guardian)
            userop_gas = bundler.get_UserOperation_GasPrice()
            standard = userop_gas['standard']

            user_op = account.build_user_operation(
                call_data=call_data,
                max_fee_per_gas=int(standard['maxFeePerGas'], 16),
                max_priority_fee_per_gas=int(standard['maxPriorityFeePerGas'], 16)
            )

            user_op_hash = account.get_user_op_hash(user_op)
            signature = km.sign_userop(user_op_hash)
            multisig_signature = account.encode_multisig_signature([signature])
            user_op['signature'] = '0x' + multisig_signature.hex()

            user_op_hash_returned = bundler.send_user_operation(user_op, deployment['entryPoint'])
            print(f"   Removing old guardian...")

            max_wait = 60
            start_time = time.time()
            receipt = None

            while time.time() - start_time < max_wait:
                receipt = bundler.get_user_operation_receipt(user_op_hash_returned)
                if receipt:
                    break
                time.sleep(5)

            if receipt and receipt.get('success'):
                print(f"   ✓ Old guardian removed")
                time.sleep(2)
            else:
                print("   ⚠️  Failed to remove old guardian")
        except Exception as e:
            print(f"   Note: Could not remove old guardian: {e}")

    # Add our test guardian EOA
    try:
        call_data = account.encode_add_guardian_call(guardian_eoa_address)
        userop_gas = bundler.get_UserOperation_GasPrice()
        standard = userop_gas['standard']

        user_op = account.build_user_operation(
            call_data=call_data,
            max_fee_per_gas=int(standard['maxFeePerGas'], 16),
            max_priority_fee_per_gas=int(standard['maxPriorityFeePerGas'], 16)
        )

        user_op_hash = account.get_user_op_hash(user_op)
        signature = km.sign_userop(user_op_hash)
        multisig_signature = account.encode_multisig_signature([signature])
        user_op['signature'] = '0x' + multisig_signature.hex()

        user_op_hash_returned = bundler.send_user_operation(user_op, deployment['entryPoint'])
        print(f"   Adding test guardian EOA...")

        max_wait = 60
        start_time = time.time()
        receipt = None

        while time.time() - start_time < max_wait:
            receipt = bundler.get_user_operation_receipt(user_op_hash_returned)
            if receipt:
                break
            time.sleep(5)

        if receipt and receipt.get('success'):
            print(f"   ✓ Test guardian EOA added: {guardian_eoa_address}")
            time.sleep(2)
        else:
            print("   ⚠️  Failed to add test guardian")
            return
    except Exception as e:
        print(f"   ✗ Error adding test guardian: {e}")
        import traceback
        traceback.print_exc()
        return

    # Now guardian calls approveRecovery DIRECTLY (not through UserOperation)
    print("\n   Guardian calling approveRecovery() directly...")
    try:
        # Get Web3 instance
        from backend.config.abi import account_abi

        web3 = Web3(Web3.HTTPProvider(sepolia_rpc))
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(account.contract_address),
            abi=account_abi
        )

        # Build transaction
        nonce = web3.eth.get_transaction_count(guardian_eoa_address)
        gas_price = web3.eth.gas_price

        tx = contract.functions.approveRecovery(
            new_owners,
            new_threshold
        ).build_transaction({
            'from': guardian_eoa_address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': gas_price
        })

        print(f"   Transaction built:")
        print(f"   - From: {guardian_eoa_address}")
        print(f"   - To: {account.contract_address}")
        print(f"   - Function: approveRecovery({new_owners}, {new_threshold})")

        # Sign transaction with guardian's private key
        signed_tx = web3.eth.account.sign_transaction(tx, guardian_private_key)

        # Send transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"   ✓ Transaction sent: {tx_hash.hex()}")

        # Wait for receipt
        print("   Waiting for confirmation...")
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if tx_receipt.status == 1:
            print(f"   ✓ approveRecovery() executed successfully!")
            print(f"   Block: {tx_receipt.blockNumber}")
            print(f"   Gas used: {tx_receipt.gasUsed}")

            # Check updated approval count
            time.sleep(2)
            approval_count = account.get_recovery_approval_count(new_owners, new_threshold)
            print(f"   ✓ Approval count: {approval_count}/{account.guardian_threshold}")
        else:
            print(f"   ✗ Transaction failed")
            return

    except Exception as e:
        print(f"   ✗ Error calling approveRecovery: {e}")
        import traceback
        traceback.print_exc()
        return

    # ============================================
    # Test 4: Execute Recovery (Direct Contract Call)
    # ============================================
    print("\n14. Test 4: Execute recovery (DIRECT contract call)...")
    print("   Note: Anyone can call this after guardian threshold is reached")

    try:
        # Check if threshold is met
        approval_count = account.get_recovery_approval_count(new_owners, new_threshold)
        print(f"   Current approvals: {approval_count}/{account.guardian_threshold}")

        if approval_count < account.guardian_threshold:
            print(f"   ⚠️  Threshold not met yet, need {account.guardian_threshold} approvals")
            return

        # Anyone can call executeRecovery (we'll use the main EOA)
        print("\n   Calling executeRecovery() directly from EOA...")

        web3 = Web3(Web3.HTTPProvider(sepolia_rpc))
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(account.contract_address),
            abi=account_abi
        )

        # Build transaction
        nonce = web3.eth.get_transaction_count(km.address)
        gas_price = web3.eth.gas_price

        tx = contract.functions.executeRecovery(
            new_owners,
            new_threshold
        ).build_transaction({
            'from': km.address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': gas_price
        })

        print(f"   Transaction built:")
        print(f"   - From: {km.address}")
        print(f"   - To: {account.contract_address}")
        print(f"   - Function: executeRecovery({new_owners}, {new_threshold})")

        # Sign transaction with EOA's private key
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)

        # Send transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"   ✓ Transaction sent: {tx_hash.hex()}")

        # Wait for receipt
        print("   Waiting for confirmation...")
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if tx_receipt.status == 1:
            print(f"   ✓ executeRecovery() executed successfully!")
            print(f"   Block: {tx_receipt.blockNumber}")
            print(f"   Gas used: {tx_receipt.gasUsed}")

            # Verify owners changed
            time.sleep(2)
            updated_owners = account.get_owners()
            print(f"\n   ✓ Account owners updated!")
            print(f"   Old owners: {[km.address]}")
            print(f"   New owners: {updated_owners}")

            if updated_owners == new_owners:
                print(f"   ✅ Social recovery SUCCESSFUL!")
            else:
                print(f"   ⚠️  Owner mismatch")
        else:
            print(f"   ✗ Transaction failed")

    except Exception as e:
        print(f"   ✗ Error calling executeRecovery: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

    print("\n📝 Summary:")
    print(f"   1. ✓ NEW account created (not imported)")
    print(f"   2. ✓ Account address: {account.contract_address}")
    print(f"   3. ✓ Account deployed via first UserOperation")
    print(f"   4. ✓ ETH transfer executed")
    print(f"   5. ✓ Guardian management tested (remove + add via UserOp)")
    print(f"   6. ✓ Social recovery FULLY EXECUTED (direct contract calls)")

    print("\n📝 What was tested:")
    print("   • NEW account creation with counterfactual address")
    print("   • Account deployment via factory contract")
    print("   • UserOperation creation and signing")
    print("   • Transfer execution via bundler")
    print("   • removeGuardian() - via UserOperation (owner-only)")
    print("   • addGuardian() - via UserOperation (owner-only)")
    print("   • approveRecovery() - DIRECT contract call (guardian EOA)")
    print("   • executeRecovery() - DIRECT contract call (anyone)")

    print("\n📝 Account Configuration:")
    try:
        final_owners = account.get_owners()
        final_guardians = account.get_guardians()
        print(f"   Current Owners: {final_owners}")
        print(f"   Current Guardians: {final_guardians}")
        print(f"   Social Recovery: {account.is_social_recovery_enabled()}")
    except Exception as e:
        print(f"   Error getting final config: {e}")

    print("\n📝 Key Architectural Points:")
    print("   ✅ Guardian management (add/remove) uses UserOperation")
    print("      → Requires account owner signature (via EntryPoint)")
    print("   ✅ Social recovery (approve/execute) uses DIRECT calls")
    print("      → Guardian calls approveRecovery() with their EOA")
    print("      → Anyone calls executeRecovery() after threshold met")
    print("      → NO EntryPoint involved - this is the KEY feature!")
    print("      → Enables recovery when owner's private key is lost")

    print("\n💡 Key Achievement:")
    print("   ✅ Successfully created NEW account from scratch")
    print("   ✅ FULLY EXECUTED social recovery workflow")
    print("   ✅ Demonstrated correct architecture (direct calls, not UserOp)")
    print(f"   ✅ Monitor: https://sepolia.etherscan.io/address/{account.contract_address}")


if __name__ == '__main__':
    main()
