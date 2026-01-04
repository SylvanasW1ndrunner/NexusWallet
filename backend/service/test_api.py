"""
API Flow Execution Script for Nexus AA Service

Execution flow divided into two parts:
Part 1: Basic API Operations - Execute individual endpoint calls
Part 2: Complete Transaction Flow - Execute full UserOperation flow using APIs

Environment Variables:
    API_BASE_URL: API server URL (default: http://localhost:8000)
    PASSWORD: Password for wallet encryption (default: TestPassword123!)
    NETWORK: Network to use (default: sepolia)
    PIMLICO_API_KEY: Pimlico bundler API key (required for Part 2)
    PRIVATE_KEY: (Optional) Private key to import. If not provided, creates new wallet.

Usage:
    1. Set up .env file with required variables
    2. Start API server: python backend/service/api.py
    3. Run script: python backend/service/test_api.py
"""
import requests
import json
import time
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✓ Loaded .env from: {env_path}")

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
PASSWORD = os.getenv("PASSWORD", os.getenv("PASSWORD", "TestPassword123!"))
NETWORK = os.getenv("NETWORK", os.getenv("NETWORK", "sepolia"))
print("NETWORK: ", NETWORK)
# Global state
session_token: Optional[str] = None
eoa_address: Optional[str] = None
account_address: Optional[str] = None


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def print_step(text: str):
    """Print step message"""
    print(f"{Colors.CYAN}▶ {text}{Colors.RESET}")


def print_response(response: requests.Response, show_full: bool = True):
    """Print formatted response"""
    print(f"  Status: {response.status_code}")
    try:
        data = response.json()
        if show_full:
            print(f"  Response: {json.dumps(data, indent=2)}")
        else:
            # Print summary for large responses
            if isinstance(data, dict):
                print(f"  Response keys: {list(data.keys())}")
            else:
                print(f"  Response: {data}")
    except:
        print(f"  Response: {response.text[:200]}")


# ============================================
# Part 1: Basic API Operations
# ============================================

def check_health():
    """Check API health endpoint"""
    print_step("Step: Health Check")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print_response(response)

        if response.status_code == 200:
            print_success("Health check passed")
            return True
        else:
            print_error("Health check failed")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


def list_networks():
    """List available networks"""
    print_step("Step: List Networks")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/chain/networks", timeout=5)
        print_response(response)

        if response.status_code == 200:
            networks = response.json()["networks"]
            print_success(f"Found {len(networks)} configured networks")
            for net in networks:
                print(f"    - {net['network_name']} (Chain ID: {net['chain_id']})")
            return True
        else:
            print_error("Failed to list networks")
            return False
    except Exception as e:
        print_error(f"List networks error: {e}")
        return False


def check_auth_status():
    """Check authentication status"""
    print_step("Step: Check Auth Status")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/chain/auth/status", timeout=5)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Initialized: {data['initialized']}, Unlocked: {data['unlocked']}")
            return data
        else:
            print_error("Failed to check auth status")
            return None
    except Exception as e:
        print_error(f"Auth status error: {e}")
        return None


def import_private_key():
    """Import wallet from private key"""
    print_step("Step: Import Private Key")
    global session_token, eoa_address

    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print_error("PRIVATE_KEY not found in environment")
        return False

    # Remove 0x prefix if present
    if private_key.startswith("0x"):
        private_key = private_key[2:]

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chain/init/import-private-key",
            json={
                "private_key": private_key,
                "password": PASSWORD
            },
            timeout=10
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            session_token = data["session_token"]
            eoa_address = data["eoa_address"]
            print_success(f"Private key imported: {eoa_address}")
            print_info(f"Session token: {session_token[:20]}...")
            return True
        else:
            print_error(f"Failed to import private key: {response.text}")
            return False
    except Exception as e:
        print_error(f"Import private key error: {e}")
        return False


def create_wallet():
    """Create new wallet"""
    print_step("Step: Create New Wallet")
    global session_token, eoa_address

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chain/init/create",
            json={"password": PASSWORD},
            timeout=10
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            session_token = data["session_token"]
            eoa_address = data["eoa_address"]
            print_success(f"Wallet created: {eoa_address}")
            print_info(f"Session token: {session_token[:20]}...")
            return True
        else:
            print_error("Failed to create wallet")
            return False
    except Exception as e:
        print_error(f"Create wallet error: {e}")
        return False


def unlock_wallet():
    """Unlock existing wallet"""
    print_step("Step: Unlock Wallet")
    global session_token, eoa_address

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chain/auth/unlock",
            json={"password": PASSWORD},
            timeout=10
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            session_token = data["session_token"]
            eoa_address = data["eoa_address"]
            print_success(f"Wallet unlocked: {eoa_address}")
            print_info(f"Session token: {session_token[:20]}...")
            return True
        else:
            print_error("Failed to unlock wallet")
            return False
    except Exception as e:
        print_error(f"Unlock wallet error: {e}")
        return False


def get_session_info():
    """Get session information"""
    print_step("Step: Get Session Info")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/chain/auth/session-info",
            headers={"X-Session-Token": session_token},
            timeout=5
        )
        print_response(response)

        if response.status_code == 200:
            print_success("Session info retrieved")
            return True
        else:
            print_error("Failed to get session info")
            return False
    except Exception as e:
        print_error(f"Session info error: {e}")
        return False


def create_account():
    """Create smart account"""
    print_step("Step: Create Smart Account")
    global account_address

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chain/accounts",
            headers={"X-Session-Token": session_token},
            json={
                "network_name": NETWORK,
                "owners": [eoa_address],
                "threshold": 1,
                "name": "Test Account - Basic"
            },
            timeout=10
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            account_address = data["account_address"]
            print_success(f"Account created: {account_address}")
            print_info(f"Name: {data.get('name', 'N/A')}")
            print_info(f"Deployed: {data['deployed']}")
            print_info(f"Balance: {data['balance']} wei")
            return True
        else:
            print_error("Failed to create account")
            return False
    except Exception as e:
        print_error(f"Create account error: {e}")
        return False


def list_accounts():
    """List all accounts"""
    print_step("Step: List All Accounts")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/chain/accounts",
            headers={"X-Session-Token": session_token},
            timeout=5
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Found accounts on networks: {data['networks']}")
            return True
        else:
            print_error("Failed to list accounts")
            return False
    except Exception as e:
        print_error(f"List accounts error: {e}")
        return False


def get_account_details():
    """Get account details"""
    print_step("Step: Get Account Details")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/chain/accounts/{NETWORK}/{account_address}",
            headers={"X-Session-Token": session_token},
            timeout=5
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success("Account details retrieved")
            print_info(f"Owners: {data['owners']}")
            print_info(f"Threshold: {data['threshold']}")
            print_info(f"Deployed: {data['deployed']}")
            return True
        else:
            print_error("Failed to get account details")
            return False
    except Exception as e:
        print_error(f"Get account details error: {e}")
        return False


def get_balance():
    """Get account balance"""
    print_step("Step: Get Account Balance")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/chain/balance/{NETWORK}/{account_address}",
            headers={"X-Session-Token": session_token},
            timeout=5
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Balance: {data['balance_eth']} ETH ({data['balance_wei']} wei)")
            return True
        else:
            print_error("Failed to get balance")
            return False
    except Exception as e:
        print_error(f"Get balance error: {e}")
        return False


def get_nonce():
    """Get account nonce"""
    print_step("Step: Get Account Nonce")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/chain/nonce/{NETWORK}/{account_address}",
            headers={"X-Session-Token": session_token},
            timeout=5
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Nonce: {data['nonce']}")
            return True
        else:
            print_error("Failed to get nonce")
            return False
    except Exception as e:
        print_error(f"Get nonce error: {e}")
        return False


def get_wallet_summary():
    """Get wallet summary"""
    print_step("Step: Get Wallet Summary")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/chain/wallet/summary",
            headers={"X-Session-Token": session_token},
            timeout=5
        )
        print_response(response)

        if response.status_code == 200:
            print_success("Wallet summary retrieved")
            return True
        else:
            print_error("Failed to get wallet summary")
            return False
    except Exception as e:
        print_error(f"Wallet summary error: {e}")
        return False


def sign_message():
    """Sign message"""
    print_step("Step: Sign Message")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chain/message/sign",
            headers={"X-Session-Token": session_token},
            json={"message": "Hello, Nexus AA!"},
            timeout=5
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success("Message signed successfully")
            print_info(f"Signature: {data['signature'][:20]}...")
            return True
        else:
            print_error("Failed to sign message")
            return False
    except Exception as e:
        print_error(f"Sign message error: {e}")
        return False


def run_basic_api_tests():
    """Run all basic API tests sequentially"""
    print_header("PART 1: BASIC API TESTS")

    results = []

    # Step 1: Health check
    results.append(("Health Check", check_health()))
    # Step 2: List networks

    # Step 3: Check auth status
    results.append(("create singleton",import_private_key()))
    results.append(("list networks",list_networks()))
    # Step 6: Session info
    if session_token:
        results.append(("Session Info", get_session_info()))

    # Step 7: Create account
    if session_token:
        results.append(("Create Account", create_account()))

    # Step 8: List accounts
    if session_token:
        results.append(("List Accounts", list_accounts()))

    # Step 9: Get account details
    if session_token and account_address:
        results.append(("Account Details", get_account_details()))

    # Step 10: Get balance
    if session_token and account_address:
        results.append(("Get Balance", get_balance()))

    # Step 11: Get nonce
    if session_token and account_address:
        results.append(("Get Nonce", get_nonce()))

    # Step 12: Wallet summary
    if session_token:
        results.append(("Wallet Summary", get_wallet_summary()))

    # Step 13: Sign message
    if session_token:
        results.append(("Sign Message", sign_message()))

    return results


# ============================================
# Part 2: Complete Transaction Flow
# ============================================

def run_complete_userop_flow():
    """
    Run complete UserOperation flow using APIs
    Simulates the full transaction flow from creation to submission
    """
    print_header("PART 2: COMPLETE TRANSACTION FLOW")

    global session_token, eoa_address, account_address

    results = []

    # Environment check
    print_step("Step 0: Environment Check")
    pimlico_api_key = os.getenv("PIMLICO_API_KEY")
    if not pimlico_api_key:
        print_error("PIMLICO_API_KEY not set in environment")
        print_info("This requires a Pimlico API key")
        print_info("Get one from: https://dashboard.pimlico.io")
        return [("Environment Check", False)]
    print_success(f"Pimlico API Key: {pimlico_api_key[:8]}...")
    results.append(("Environment Check", True))

    # Step 1: Ensure wallet is unlocked
    print_step("Step 1: Ensure Wallet is Unlocked")
    if not session_token:
        auth_status = check_auth_status()

        if auth_status and not auth_status["initialized"]:
            # Wallet not initialized
            private_key = os.getenv("PRIVATE_KEY")

            if private_key:
                print_info("Found PRIVATE_KEY, importing...")
                if not import_private_key():
                    print_error("Failed to import private key")
                    return results
            else:
                print_info("No PRIVATE_KEY found, creating new wallet...")
                if not create_wallet():
                    print_error("Failed to create wallet")
                    return results

        elif auth_status and auth_status["initialized"] and not auth_status["unlocked"]:
            # Wallet exists but locked
            if not unlock_wallet():
                print_error("Failed to unlock wallet")
                return results

        elif auth_status and auth_status["unlocked"]:
            # Wallet exists and unlocked but we don't have token
            if not unlock_wallet():
                print_error("Failed to get session token")
                return results

    print_success(f"Wallet ready: {eoa_address}")
    results.append(("Wallet Unlock", True))



    # Step 2: Create an account for transaction flow
    print_step("Step 2: Create Account for Transaction")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chain/accounts",
            headers={"X-Session-Token": session_token},
            json={
                "network_name": NETWORK,
                "owners": [eoa_address],
                "threshold": 1,
                "name": "Account - Transaction Flow",
                "salt": int(time.time())  # Use timestamp as salt for unique address
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            test_account = data["account_address"]
            print_success(f"Account created: {test_account}")
            print_info(f"Deployed: {data['deployed']}")
            print_info(f"Balance: {data['balance']} wei")
            results.append(("Create Transaction Account", True))
        else:
            print_error(f"Failed to create account: {response.text}")
            results.append(("Create Transaction Account", False))
            return results
    except Exception as e:
        print_error(f"Create account error: {e}")
        results.append(("Create Transaction Account", False))
        return results

    # Step 3: Check account balance
    print_step("Step 3: Check Account Balance")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/chain/balance/{NETWORK}/{test_account}",
            headers={"X-Session-Token": session_token},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            balance_eth = data['balance_eth']
            print_success(f"Account balance: {balance_eth} ETH")

            if balance_eth == 0:
                print_info("⚠️  Account has no balance")
                print_info("Note: Account will be deployed on first transaction")
                print_info("Make sure EOA has enough ETH to fund deployment")

            results.append(("Check Balance", True))
        else:
            print_error("Failed to check balance")
            results.append(("Check Balance", False))
    except Exception as e:
        print_error(f"Check balance error: {e}")
        results.append(("Check Balance", False))

    # Step 4: Send UserOperation
    print_step("Step 4: Send UserOperation (Transfer)")

    recipient = "0x3003A698EdcFDCC2BEa70FFf23DADF0b4bA1f6bf"  # Recipient address
    amount_eth = 0.0001

    print_info(f"Recipient: {recipient}")
    print_info(f"Amount: {amount_eth} ETH")
    print_info("This will execute:")
    print_info("  - UserOperation construction")
    print_info("  - Gas estimation")
    print_info("  - Signature generation")
    print_info("  - Bundler submission")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chain/userop/send",
            headers={"X-Session-Token": session_token},
            json={
                "network_name": NETWORK,
                "account_address": test_account,
                "target": recipient,
                "value": int(amount_eth * 10**18),  # Convert to wei
                "data": "0x"  # Empty data for simple transfer
            },
            timeout=30  # UserOp submission may take time
        )

        print_response(response, show_full=True)

        if response.status_code == 200:
            data = response.json()
            tx_hash = data["transaction_hash"]
            is_multisig = data.get("is_multisig", False)

            print_success(f"UserOperation sent!")
            print_info(f"Transaction hash: {tx_hash}")
            print_info(f"Is multisig: {is_multisig}")
            print_info(f"Account: {data['account_address']}")
            print_info(f"Network: {data['network_name']}")

            if not is_multisig:
                print_info("✓ Transaction submitted to bundler")
                print_info("  Waiting for bundler to include it in a bundle...")
                print_info(f"  Check status: https://{NETWORK}.etherscan.io/tx/{tx_hash}")
            else:
                print_info("✓ Transaction submitted to aggregator")
                print_info("  Waiting for additional signatures...")

            results.append(("Send UserOperation", True))

            # Step 5: Wait and check transaction status (for single-sig)
            if not is_multisig:
                print_step("Step 5: Check Transaction Status")
                print_info("Waiting 10 seconds for bundler to process...")
                time.sleep(10)

                # Check balance again
                try:
                    response = requests.get(
                        f"{API_BASE_URL}/api/v1/chain/balance/{NETWORK}/{test_account}",
                        headers={"X-Session-Token": session_token},
                        timeout=5
                    )

                    if response.status_code == 200:
                        data = response.json()
                        new_balance = data['balance_eth']
                        print_success(f"New balance: {new_balance} ETH")

                        # Check if balance changed
                        if new_balance != balance_eth:
                            print_success("✓ Transaction executed successfully!")
                        else:
                            print_info("Balance unchanged - transaction may still be pending")

                        results.append(("Check Transaction Status", True))
                    else:
                        print_error("Failed to check new balance")
                        results.append(("Check Transaction Status", False))
                except Exception as e:
                    print_error(f"Check status error: {e}")
                    results.append(("Check Transaction Status", False))
        else:
            print_error(f"Failed to send UserOperation")
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            results.append(("Send UserOperation", False))

    except Exception as e:
        print_error(f"Send UserOperation error: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Send UserOperation", False))

    return results


def run_multisig_flow():
    """Run multi-signature transaction flow"""
    print_header("PART 2B: MULTI-SIGNATURE TRANSACTION FLOW")

    global session_token, eoa_address

    results = []

    if not session_token:
        print_error("No active session. Run basic operations first.")
        return results

    # Step 1: Create multi-sig account
    print_step("Step 1: Create Multi-Sig Account (threshold=2)")

    # Create second owner (for demo, we use a dummy address)
    # In real scenario, this would be another user's EOA
    second_owner = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

    print_info(f"Owner 1: {eoa_address}")
    print_info(f"Owner 2: {second_owner}")
    print_info("Threshold: 2")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chain/accounts",
            headers={"X-Session-Token": session_token},
            json={
                "network_name": NETWORK,
                "owners": [eoa_address, second_owner],
                "threshold": 2,
                "name": "Multi-Sig Account",
                "salt": int(time.time()) + 1000
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            multisig_account = data["account_address"]
            print_success(f"Multi-sig account created: {multisig_account}")
            print_info(f"Owners: {data['owners']}")
            print_info(f"Threshold: {data['threshold']}")
            results.append(("Create Multi-Sig Account", True))
        else:
            print_error(f"Failed to create multi-sig account: {response.text}")
            results.append(("Create Multi-Sig Account", False))
            return results
    except Exception as e:
        print_error(f"Create multi-sig account error: {e}")
        results.append(("Create Multi-Sig Account", False))
        return results

    # Step 2: Submit multi-sig transaction
    print_step("Step 2: Submit Multi-Sig Transaction")

    recipient = "0x3003A698EdcFDCC2BEa70FFf23DADF0b4bA1f6bf"
    amount_eth = 0.0001

    print_info("This transaction will require 2 signatures")
    print_info("First signature will be provided now")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chain/userop/send",
            headers={"X-Session-Token": session_token},
            json={
                "network_name": NETWORK,
                "account_address": multisig_account,
                "target": recipient,
                "value": int(amount_eth * 10**18),
                "data": "0x"
            },
            timeout=30
        )

        print_response(response, show_full=True)

        if response.status_code == 200:
            data = response.json()
            tx_hash = data["transaction_hash"]

            print_success("Multi-sig transaction submitted to aggregator")
            print_info(f"Transaction hash: {tx_hash}")
            print_info(f"Signatures collected: 1/2")
            print_info("Transaction is pending additional signature")

            results.append(("Submit Multi-Sig Transaction", True))

            # Step 3: Check pending transactions
            print_step("Step 3: Query Pending Transactions")

            try:
                response = requests.get(
                    f"{API_BASE_URL}/api/v1/multisig/transactions/pending",
                    headers={"X-Session-Token": session_token},
                    params={
                        "account_address": multisig_account,
                        "chain_id": 11155111,  # Sepolia
                        "signer_address": eoa_address
                    },
                    timeout=5
                )

                print_response(response, show_full=True)

                if response.status_code == 200:
                    data = response.json()
                    transactions = data.get("transactions", [])
                    print_success(f"Found {len(transactions)} pending transaction(s)")

                    for tx in transactions:
                        print_info(f"  TX Hash: {tx['transaction_hash']}")
                        print_info(f"  Signatures: {tx['signatures_collected']}/{tx['threshold']}")
                        print_info(f"  Already signed: {tx['already_signed']}")

                    results.append(("Query Pending Transactions", True))
                else:
                    print_error("Failed to query pending transactions")
                    results.append(("Query Pending Transactions", False))
            except Exception as e:
                print_error(f"Query pending error: {e}")
                results.append(("Query Pending Transactions", False))

            # Step 4: Check transaction status
            print_step("Step 4: Check Transaction Status")

            try:
                response = requests.get(
                    f"{API_BASE_URL}/api/v1/multisig/transactions/{tx_hash}/status",
                    headers={"X-Session-Token": session_token},
                    timeout=5
                )

                print_response(response, show_full=True)

                if response.status_code == 200:
                    data = response.json()
                    print_success(f"Transaction status: {data['status']}")
                    print_info(f"Signatures collected: {data['signatures_collected']}/{data['threshold']}")
                    print_info(f"Created: {data['creation_time']}")

                    results.append(("Check Transaction Status", True))
                else:
                    print_error("Failed to check transaction status")
                    results.append(("Check Transaction Status", False))
            except Exception as e:
                print_error(f"Check status error: {e}")
                results.append(("Check Transaction Status", False))

            print_info("\n📝 Note: To complete this transaction:")
            print_info("  1. Second owner needs to call POST /api/v1/multisig/transactions/{tx_hash}/sign")
            print_info("  2. Provide their signature")
            print_info("  3. Transaction will auto-submit to bundler when threshold reached")

        else:
            print_error(f"Failed to submit multi-sig transaction: {response.text}")
            results.append(("Submit Multi-Sig Transaction", False))

    except Exception as e:
        print_error(f"Multi-sig transaction error: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Submit Multi-Sig Transaction", False))

    return results


def print_summary(basic_results, flow_results, multisig_results=None):
    """Print comprehensive execution summary"""
    print_header("EXECUTION SUMMARY")

    # Basic operations summary
    print(f"\n{Colors.BOLD}Part 1: Basic API Operations{Colors.RESET}")
    passed_basic = sum(1 for _, result in basic_results if result)
    total_basic = len(basic_results)

    for step_name, result in basic_results:
        if result:
            print_success(f"{step_name}")
        else:
            print_error(f"{step_name}")

    print(f"\n  Results: {passed_basic}/{total_basic} completed")

    # Flow execution summary
    print(f"\n{Colors.BOLD}Part 2: Complete Transaction Flow{Colors.RESET}")
    passed_flow = sum(1 for _, result in flow_results if result)
    total_flow = len(flow_results)

    for step_name, result in flow_results:
        if result:
            print_success(f"{step_name}")
        else:
            print_error(f"{step_name}")

    print(f"\n  Results: {passed_flow}/{total_flow} completed")

    # Multi-sig flow summary
    if multisig_results:
        print(f"\n{Colors.BOLD}Part 2B: Multi-Signature Flow{Colors.RESET}")
        passed_multisig = sum(1 for _, result in multisig_results if result)
        total_multisig = len(multisig_results)

        for step_name, result in multisig_results:
            if result:
                print_success(f"{step_name}")
            else:
                print_error(f"{step_name}")

        print(f"\n  Results: {passed_multisig}/{total_multisig} completed")

    # Overall summary
    all_results = basic_results + flow_results + (multisig_results if multisig_results else [])
    total_passed = sum(1 for _, result in all_results if result)
    total_tests = len(all_results)

    print(f"\n{Colors.BOLD}Overall: {total_passed}/{total_tests} steps completed{Colors.RESET}")

    if total_passed == total_tests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL STEPS COMPLETED!{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME STEPS FAILED{Colors.RESET}\n")
        return 1


def main():
    """Main execution entry point"""
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}Nexus AA Service - API Flow Execution{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print(f"Network: {NETWORK}")
    print(f"Password: {PASSWORD}")

    # Check wallet initialization method
    private_key = os.getenv("PRIVATE_KEY")
    if private_key:
        print(f"\n{Colors.GREEN}✓ PRIVATE_KEY found in environment{Colors.RESET}")
        print(f"{Colors.GREEN}  Will import existing private key{Colors.RESET}")
        print(f"{Colors.GREEN}  (Recommended for consistent execution with funded accounts){Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️  No PRIVATE_KEY in environment{Colors.RESET}")
        print(f"{Colors.YELLOW}  Will create new random wallet{Colors.RESET}")
        print(f"{Colors.YELLOW}  (New wallet will have 0 balance initially){Colors.RESET}")

    print(f"\n{Colors.YELLOW}Make sure the API server is running!{Colors.RESET}")
    print(f"{Colors.YELLOW}Start with: python backend/service/api.py{Colors.RESET}\n")

    input("Press Enter to start execution...")

    # Run Part 1: Basic API Operations
    basic_results = run_basic_api_tests()

    # Check if basic operations succeeded before continuing
    basic_passed = sum(1 for _, result in basic_results if result)
    if basic_passed < len(basic_results) * 0.7:  # At least 70% should pass
        print_error("\nToo many basic operations failed. Skipping transaction flow.")
        print_error("Please fix basic API issues first.")
        return print_summary(basic_results, [], None)

    # Run Part 2: Complete Transaction Flow
    flow_results = run_complete_userop_flow()

    # Run Part 2B: Multi-Sig Flow (optional)
    print(f"\n{Colors.YELLOW}Do you want to run multi-signature flow? (y/n){Colors.RESET}")
    run_multisig = input().strip().lower() == 'y'

    multisig_results = None
    if run_multisig:
        multisig_results = run_multisig_flow()

    # Print comprehensive summary
    return print_summary(basic_results, flow_results, multisig_results)


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
