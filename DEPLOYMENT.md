# Local Deployment Guide

This guide explains how to deploy and test the AA wallet contracts on a local Hardhat node.

## Prerequisites

- Node.js and npm installed
- Python 3.7+ installed
- Hardhat dependencies installed

## Step 1: Install Dependencies

```bash
cd contracts
npm install
```

## Step 2: Start Local Hardhat Node

In a terminal window, start the Hardhat local node:

```bash
cd contracts
npx hardhat node
```

This will:
- Start a local Ethereum node at `http://127.0.0.1:8545`
- Create 20 test accounts with 10,000 ETH each
- Display the test accounts and their private keys
- Keep running until you stop it (Ctrl+C)

**Important**: Keep this terminal window open while testing!

## Step 3: Deploy Contracts

In a **new terminal window**, deploy the contracts:

```bash
cd contracts
npx hardhat run scripts/deploy-local.ts --network localhost
```

This will:
1. Deploy the EntryPoint contract
2. Deploy the SimpleAccountFactory contract
3. Calculate a counterfactual address for a test AA account
4. Save deployment info to `backend/local_deployment.json`

Expected output:
```
Starting deployment...
Deploying with account: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
Account balance: 10000.0 ETH

1. Deploying EntryPoint...
✓ EntryPoint deployed to: 0x5FbDB2315678afecb367f032d93F642f64180aa3

2. Deploying SimpleAccountFactory...
✓ SimpleAccountFactory deployed to: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512

3. Calculating counterfactual account addresses...
✓ Test account counterfactual address: 0x...

4. Saving deployment configuration...
✓ Deployment info saved to: .../backend/local_deployment.json

✅ Deployment complete!
```

## Step 4: Test with Python Backend

```bash
cd ..  # Go back to project root
python -m backend.test_local_deployment
```

This test script will:
1. Load deployment configuration
2. Configure the Config singleton with localhost network
3. Create/unlock a KeyManager using Hardhat's first test account
4. Create a Wallet instance
5. Test EOA operations (balance, nonce)
6. Add the deployed AA account to the wallet
7. Test AA account queries
8. Display wallet summary

## Understanding the Test Accounts

Hardhat provides 20 test accounts by default:

**Account #0** (used in our tests):
- Address: `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266`
- Private Key: `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80`
- Balance: 10,000 ETH

You can use any of these accounts for testing.

## Project Structure After Deployment

```
Nexus/
├── backend/
│   ├── config.json              # Network configurations (auto-saved)
│   ├── local_deployment.json    # Deployment addresses (created by script)
│   ├── keystore.json            # Encrypted private key (created on first run)
│   ├── wallet_test.json         # Wallet config (if saved)
│   └── test_local_deployment.py # Test script
└── contracts/
    └── scripts/
        └── deploy-local.ts      # Deployment script
```

## Deployment Configuration File

The `backend/local_deployment.json` file contains:

```json
{
  "network": "localhost",
  "chainId": 31337,
  "deployer": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
  "entryPoint": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
  "factory": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
  "testAccount": {
    "address": "0x...",
    "owners": ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"],
    "threshold": 1,
    "guardians": [],
    "guardianThreshold": 0,
    "salt": 0
  },
  "timestamp": "2025-12-03T..."
}
```

## Next Steps

After running the tests, you can:

1. **Deploy the AA Account**: The test creates a counterfactual address. To actually deploy:
   ```python
   # Fund the account first
   tx_hash = wallet.send_transaction(
       network_name='localhost',
       to=account.contract_address,
       value=Web3.to_wei(1, 'ether')
   )

   # Then deploy by calling factory or sending a UserOperation
   ```

2. **Send UserOperations**: Once deployed, use `account.build_user_operation()` to create UserOps

3. **Test Multi-sig**: Add more owners and test threshold signatures

4. **Test Social Recovery**: Add guardians and test the recovery flow

## Troubleshooting

**Error: "Cannot connect to RPC"**
- Make sure the Hardhat node is running (`npx hardhat node`)
- Check that it's listening on `http://127.0.0.1:8545`

**Error: "Deployment file not found"**
- Run the deployment script first: `npx hardhat run scripts/deploy-local.ts --network localhost`

**Error: "Keystore not found"**
- This is normal on first run - the script will import the Hardhat test account

**Reset Everything**
- Stop the Hardhat node (Ctrl+C)
- Delete generated files: `config.json`, `local_deployment.json`, `keystore.json`, `wallet_test.json`
- Start fresh from Step 2

## Clean Up

To stop testing:
1. Stop the Hardhat node (Ctrl+C in the node terminal)
2. Optionally delete test files:
   ```bash
   cd backend
   rm config.json local_deployment.json keystore.json wallet_test.json
   ```

## Development Workflow

For active development:
1. Keep Hardhat node running in one terminal
2. Modify contracts
3. Redeploy: `npx hardhat run scripts/deploy-local.ts --network localhost`
4. Test: `python -m backend.test_local_deployment`

Note: The Hardhat node resets its state when restarted, so you'll need to redeploy contracts after restarting the node.
