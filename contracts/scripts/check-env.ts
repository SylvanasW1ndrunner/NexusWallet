/**
 * Environment checker for Sepolia deployment
 * Validates that all required environment variables and setup is complete
 */

import env, { ethers } from 'hardhat'
import * as dotenv from 'dotenv'
import * as fs from 'fs'
import * as path from 'path'

dotenv.config()
const envPath = path.join(__dirname, '../.env')
console.log('env path:', envPath)
console.log('ENV TEST:', process.env.SEPOLIA_RPC_URL)
console.log('ENV TEST:', process.env.INFURA_ID)

async function main () {
  console.log('🔍 Checking Sepolia Deployment Environment...\n')

  let hasErrors = false

  // 1. Check for .env file
  console.log('1. Checking .env file...')
  const envPath = path.join(__dirname, '../.env')
  if (!fs.existsSync(envPath)) {
    console.log('   ✗ .env file not found!')
    console.log('   → Create one: cp .env.example .env')
    hasErrors = true
  } else {
    console.log('   ✓ .env file exists')
  }

  // 2. Check INFURA_ID
  console.log('\n2. Checking INFURA_ID...')
  if (!process.env.INFURA_ID) {
    console.log('   ⚠️  INFURA_ID not set')
    console.log('   → Get API key from https://infura.io')
    console.log('   → Or set SEPOLIA_RPC_URL instead')
    hasErrors = true
  } else {
    console.log(`   ✓ INFURA_ID is set: ${process.env.INFURA_ID.substring(0, 8)}...`)
  }

  // 3. Check network connectivity
  console.log('\n3. Checking Sepolia network connectivity...')
  try {
    const provider = new ethers.providers.JsonRpcProvider(
      process.env.SEPOLIA_RPC_URL || `https://sepolia.infura.io/v3/${process.env.INFURA_ID}`
    )

    const network = await provider.getNetwork()
    console.log(`   ✓ Connected to network: ${network.name} (Chain ID: ${network.chainId})`)

    if (network.chainId !== 11155111) {
      console.log('   ✗ Wrong network! Expected Sepolia (11155111)')
      hasErrors = true
    }

    const blockNumber = await provider.getBlockNumber()
    console.log(`   ✓ Current block: ${blockNumber}`)
  } catch (error) {
    console.log(`   ✗ Failed to connect: ${error}`)
    hasErrors = true
  }

  // 4. Check deployer account
  console.log('\n4. Checking deployer account...')
  try {
    const [deployer] = await ethers.getSigners()
    console.log(`   ✓ Deployer address: ${deployer.address}`)

    const balance = await deployer.getBalance()
    const balanceEth = ethers.utils.formatEther(balance)
    console.log(`   Account balance: ${balanceEth} ETH`)

    if (balance.eq(0)) {
      console.log('   ✗ No balance! Get Sepolia ETH from:')
      console.log('      - https://sepoliafaucet.com')
      console.log('      - https://www.infura.io/faucet/sepolia')
      hasErrors = true
    } else if (balance.lt(ethers.utils.parseEther('0.01'))) {
      console.log('   ⚠️  Low balance! You may need more ETH for deployment.')
      console.log('      Recommended: at least 0.05 ETH')
    } else {
      console.log('   ✓ Balance looks good!')
    }
  } catch (error) {
    console.log(`   ✗ Failed to check account: ${error}`)
    hasErrors = true
  }

  // 5. Check Pimlico API key
  console.log('\n5. Checking Pimlico API key...')
  if (!process.env.PIMLICO_API_KEY) {
    console.log('   ⚠️  PIMLICO_API_KEY not set (needed for testing)')
    console.log('   → Get API key from https://dashboard.pimlico.io')
  } else {
    console.log(`   ✓ PIMLICO_API_KEY is set: ${process.env.PIMLICO_API_KEY.substring(0, 8)}...`)

    // Test Pimlico connectivity
    try {
      const response = await fetch(
        `https://api.pimlico.io/v1/sepolia/rpc?apikey=${process.env.PIMLICO_API_KEY}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'eth_supportedEntryPoints',
            params: []
          })
        }
      )

      if (response.ok) {
        console.log('   ✓ Pimlico bundler is accessible')
      } else {
        console.log('   ⚠️  Pimlico API returned error')
      }
    } catch (error) {
      console.log('   ⚠️  Could not test Pimlico connectivity')
    }
  }

  // 6. Summary
  console.log('\n' + '='.repeat(60))
  if (hasErrors) {
    console.log('❌ Environment check FAILED')
    console.log('Please fix the errors above before deploying.')
    process.exit(1)
  } else {
    console.log('✅ Environment check PASSED')
    console.log('\nYou are ready to deploy!')
    console.log('\nNext step:')
    console.log('  npx hardhat run scripts/deploy-sepolia.ts --network sepolia')
  }
  console.log('='.repeat(60))
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error)
    process.exit(1)
  })
