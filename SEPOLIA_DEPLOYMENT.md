# Sepolia Deployment Guide

This guide walks you through deploying the Account Abstraction contracts to Sepolia testnet and testing with Pimlico bundler.

## Prerequisites

1. Node.js and npm installed
2. Python 3.8+ installed
3. Sepolia testnet ETH (for deployment gas fees)
4. Pimlico API key

## Step 1: Get Required API Keys

### 1.1 Get Sepolia ETH
Get testnet ETH from one of these faucets:
- https://sepoliafaucet.com
- https://www.infura.io/faucet/sepolia
- https://sepolia-faucet.pk910.de

### 1.2 Get Infura API Key (Optional)
If you want to use Infura RPC:
1. Go to https://infura.io
2. Create a free account
3. Create a new project
4. Copy your API key

### 1.3 Get Pimlico API Key
1. Go to https://dashboard.pimlico.io
2. Sign up for a free account
3. Create a new API key
4. Copy your API key

## Step 2: Configure Environment

### 2.1 Create `.env` file in contracts directory

```bash
cd contracts
cp .env.example .env
```

### 2.2 Edit `.env` file

```bash
# If using Infura
INFURA_ID=your_infura_api_key_here

# Or use a custom RPC URL
# SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_API_KEY

# Your deployer private key (the account that will pay for deployment)
# This should be the account where you got Sepolia ETH
# WARNING: Never commit this file!
PRIVATE_KEY=your_private_key_without_0x_prefix

# Pimlico API key
PIMLICO_API_KEY=your_pimlico_api_key_here
```

### 2.3 Update Hardhat Config (if needed)

The `hardhat.config.ts` is already configured to use environment variables from `.env`.

## Step 3: Deploy Contracts to Sepolia

### 3.1 Install dependencies

```bash
cd contracts
npm install
```

### 3.2 Compile contracts

```bash
npm run compile
```

### 3.3 Deploy to Sepolia

```bash
npx hardhat run scripts/deploy-sepolia.ts --network sepolia
```

This will:
- Deploy the EntryPoint contract
- Deploy the SimpleAccountFactory contract
- Calculate a test account address
- Save deployment info to `backend/sepolia_deployment.json`

**Expected output:**
```
Starting Sepolia deployment...
Deploying with account: 0x...
Account balance: X.XX ETH
Network: sepolia (Chain ID: 11155111)

1. Deploying EntryPoint...
✓ EntryPoint deployed to: 0x...
  Waiting for confirmations...

2. Deploying SimpleAccountFactory...
✓ SimpleAccountFactory deployed to: 0x...
  Waiting for confirmations...

3. Calculating counterfactual account addresses...
✓ Test account counterfactual address: 0x...

4. Saving deployment configuration...
✓ Deployment info saved to: ../backend/sepolia_deployment.json

✅ Deployment complete!
```

### 3.4 (Optional) Verify Contracts on Etherscan

```bash
# Get Etherscan API key from https://etherscan.io/apis

# Verify EntryPoint
npx hardhat verify --network sepolia <ENTRYPOINT_ADDRESS>

# Verify Factory
npx hardhat verify --network sepolia <FACTORY_ADDRESS> <ENTRYPOINT_ADDRESS>
```

## Step 4: Test with Python Backend

### 4.1 Set environment variables

```bash
# On Linux/Mac
export PIMLICO_API_KEY=your_pimlico_api_key
export DEPLOYER_PRIVATE_KEY=your_private_key

# On Windows (PowerShell)
$env:PIMLICO_API_KEY="your_pimlico_api_key"
$env:DEPLOYER_PRIVATE_KEY="your_private_key"

# On Windows (CMD)
set PIMLICO_API_KEY=your_pimlico_api_key
set DEPLOYER_PRIVATE_KEY=your_private_key
```

### 4.2 Run the test script

```bash
cd ..
python -m backend.test_sepolia_deployment
```

This will:
- Load the deployment configuration
- Configure Sepolia network in the Config singleton
- Initialize Pimlico bundler client
- Create a wallet with your key
- Check balances
- Test bundler connectivity

**Expected output:**
```
============================================================
Testing Sepolia Deployment with Pimlico Bundler
============================================================

1. Loading deployment configuration...
   Network: sepolia
   Chain ID: 11155111
   EntryPoint: 0x...
   Factory: 0x...
   Test Account: 0x...

2. Configuring Sepolia network...
   ✓ Sepolia network configured

3. Initializing Pimlico bundler...
   ✓ Pimlico bundler initialized

4. Setting up wallet...
   EOA Address: 0x...

5. Checking EOA balance...
   EOA Balance: X.XX ETH

6. Adding AA account to wallet...
   ✓ AA Account: 0x...

7. Checking AA account deployment status...
   Is Deployed: False

8. Testing Pimlico bundler connectivity...
   Bundler URL: https://api.pimlico.io/v1/sepolia/rpc?apikey=...
   ✓ Bundler is accessible
   Supported EntryPoints: ['0x...']

============================================================
✅ Setup complete!
============================================================
```

## Step 5: Next Steps

Now that contracts are deployed and the bundler is configured, you can:

1. **Implement UserOperation Creation**: Add methods to create and sign UserOperations
2. **Submit UserOperations**: Send operations through Pimlico bundler
3. **Monitor Transactions**: Track UserOperation status on Sepolia Etherscan

### Example: Sending a UserOperation

```python
# TODO: Implement in the Account class
user_op = account.create_user_operation(
    target=recipient_address,
    value=amount,
    data=b''
)

# Sign the UserOperation
signed_user_op = account.sign_user_operation(user_op, key_manager)

# Submit to bundler
bundler = PimlicoBundler(api_key=pimlico_api_key)
user_op_hash = bundler.send_user_operation(signed_user_op, entrypoint_address)

# Wait for receipt
receipt = bundler.get_user_operation_receipt(user_op_hash)
```

## Troubleshooting

### Error: "Insufficient funds"
- Make sure your deployer account has enough Sepolia ETH
- Check balance: `npx hardhat run scripts/check-balance.ts --network sepolia`

### Error: "Network not configured"
- Check that INFURA_ID is set in `.env`
- Or set SEPOLIA_RPC_URL to a valid Sepolia RPC endpoint

### Error: "Bundler connection failed"
- Check that PIMLICO_API_KEY is valid
- Verify you have network access to api.pimlico.io

### Error: "This script is for Sepolia testnet only"
- Make sure you're using `--network sepolia` flag
- Check that your RPC endpoint is for Sepolia (chain ID 11155111)

## Useful Links

- **Sepolia Etherscan**: https://sepolia.etherscan.io
- **Pimlico Dashboard**: https://dashboard.pimlico.io
- **Pimlico Docs**: https://docs.pimlico.io
- **ERC-4337 Spec**: https://eips.ethereum.org/EIPS/eip-4337
- **Sepolia Faucets**: Listed in Step 1.1

## Security Notes

- **Never commit `.env` file** - it contains sensitive keys
- Use a separate key for testnet vs mainnet
- Keep your API keys secure
- Rotate keys regularly
