/**
 * Sepolia deployment script with debugging
 */

import { ethers } from 'hardhat'
import * as fs from 'fs'
import * as path from 'path'

// ERC-4337 v0.7 standard EntryPoint address
const ENTRYPOINT_ADDRESS = '0x0000000071727De22E5E9d8BAf0edAc6f37da032'

async function main() {
  console.log('Starting Sepolia deployment with debugging...\n')

  const [deployer] = await ethers.getSigners()
  console.log(`Deploying with account: ${deployer.address}`)

  const balance = await deployer.getBalance()
  console.log(`Account balance: ${ethers.utils.formatEther(balance)} ETH`)

  const network = await ethers.provider.getNetwork()
  console.log(`Network: ${network.name} (Chain ID: ${network.chainId})\n`)

  if (network.chainId !== 11155111) {
    throw new Error('This script is for Sepolia testnet only!')
  }

  // Step 1: Verify EntryPoint exists
  console.log('1. Verifying EntryPoint...')
  const entryPointCode = await ethers.provider.getCode(ENTRYPOINT_ADDRESS)
  if (entryPointCode === '0x' || entryPointCode === '0x0') {
    throw new Error(`No contract found at EntryPoint address: ${ENTRYPOINT_ADDRESS}`)
  }
  console.log(`✓ EntryPoint exists (code length: ${entryPointCode.length} bytes)`)

  // Step 2: Try to call senderCreator()
  console.log('\n2. Checking EntryPoint.senderCreator()...')
  try {
    const entryPoint = await ethers.getContractAt(
      'contracts/interfaces/IEntryPoint.sol:IEntryPoint',
      ENTRYPOINT_ADDRESS
    )
    const senderCreatorAddress = await entryPoint.senderCreator()
    console.log(`✓ SenderCreator address: ${senderCreatorAddress}`)

    // Check if SenderCreator has code
    const senderCreatorCode = await ethers.provider.getCode(senderCreatorAddress)
    if (senderCreatorCode === '0x' || senderCreatorCode === '0x0') {
      console.log(`⚠️  WARNING: SenderCreator has no code at ${senderCreatorAddress}`)
    } else {
      console.log(`✓ SenderCreator has code (${senderCreatorCode.length} bytes)`)
    }
  } catch (error: any) {
    console.error(`❌ Failed to call senderCreator(): ${error.message}`)
    throw new Error('EntryPoint does not have a valid senderCreator() function')
  }

  // Step 3: Deploy SimpleAccount implementation first (to test if EntryPoint works)
  console.log('\n3. Deploying SimpleAccount implementation...')
  try {
    const SimpleAccount = await ethers.getContractFactory('SimpleAccount')
    const accountImpl = await SimpleAccount.deploy(ENTRYPOINT_ADDRESS)
    await accountImpl.deployed()
    console.log(`✓ SimpleAccount implementation deployed to: ${accountImpl.address}`)
    console.log(`  Waiting for confirmations...`)
    await accountImpl.deployTransaction.wait(2)
  } catch (error: any) {
    console.error(`❌ Failed to deploy SimpleAccount: ${error.message}`)
    console.log('\nThis error suggests the EntryPoint might not be compatible.')
    console.log('Consider deploying your own EntryPoint instead.')
    throw error
  }

  // Step 4: Deploy SimpleAccountFactory
  console.log('\n4. Deploying SimpleAccountFactory...')
  try {
    const SimpleAccountFactory = await ethers.getContractFactory('SimpleAccountFactory')

    // Estimate gas first
    console.log('   Estimating gas...')
    const deployTx = SimpleAccountFactory.getDeployTransaction(ENTRYPOINT_ADDRESS)
    const gasEstimate = await ethers.provider.estimateGas({
      from: deployer.address,
      data: deployTx.data
    })
    console.log(`   Gas estimate: ${gasEstimate.toString()}`)

    const factory = await SimpleAccountFactory.deploy(ENTRYPOINT_ADDRESS, {
      gasLimit: gasEstimate.mul(120).div(100) // Add 20% buffer
    })
    await factory.deployed()
    console.log(`✓ SimpleAccountFactory deployed to: ${factory.address}`)
    console.log(`  Waiting for confirmations...`)
    await factory.deployTransaction.wait(3)

    // Save deployment info
    console.log('\n5. Saving deployment configuration...')
    const testOwners = [deployer.address]
    const testThreshold = 1
    const testGuardians: string[] = []
    const testGuardianThreshold = 0
    const testSalt = 0

    const accountAddress = await factory.getAddress(
      testOwners,
      testThreshold,
      testGuardians,
      testGuardianThreshold,
      testSalt
    )

    const deploymentInfo = {
      network: 'sepolia',
      chainId: network.chainId,
      deployer: deployer.address,
      entryPoint: ENTRYPOINT_ADDRESS,
      factory: factory.address,
      testAccount: {
        address: accountAddress,
        owners: testOwners,
        threshold: testThreshold,
        guardians: testGuardians,
        guardianThreshold: testGuardianThreshold,
        salt: testSalt
      },
      timestamp: new Date().toISOString()
    }

    const backendPath = path.join(__dirname, '../../backend')
    const outputPath = path.join(backendPath, 'sepolia_deployment.json')

    fs.mkdirSync(backendPath, { recursive: true })
    fs.writeFileSync(outputPath, JSON.stringify(deploymentInfo, null, 2))
    console.log(`✓ Deployment info saved to: ${outputPath}`)

    console.log('\n✅ Deployment complete!')
    console.log('\nDeployment Summary:')
    console.log('==================')
    console.log(`Network: Sepolia Testnet`)
    console.log(`Chain ID: ${network.chainId}`)
    console.log(`EntryPoint: ${ENTRYPOINT_ADDRESS} (standard)`)
    console.log(`Factory: ${factory.address}`)
    console.log(`Test Account: ${accountAddress}`)

  } catch (error: any) {
    console.error(`\n❌ Deployment failed: ${error.message}`)

    if (error.message.includes('execution reverted')) {
      console.log('\n📝 Possible causes:')
      console.log('1. EntryPoint contract incompatibility')
      console.log('2. Constructor validation failed')
      console.log('3. Insufficient gas')
      console.log('\n💡 Suggestion: Deploy your own EntryPoint instead of using the standard one')
    }

    throw error
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error)
    process.exit(1)
  })
