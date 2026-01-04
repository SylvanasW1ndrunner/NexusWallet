/**
 * Sepolia testnet deployment script (debuggable)
 * Deploys SimpleAccountFactory using standard ERC-4337 v0.7 EntryPoint
 * Added: debug helpers to surface revert reason when estimateGas fails.
 */

import { ethers } from 'hardhat'
import * as fs from 'fs'
import * as path from 'path'

const ENTRYPOINT_ADDRESS = '0x0000000071727De22E5E9d8BAf0edAc6f37da032'

function decodeRevertReason (data: string): string | null {
  try {
    if (!data || data === '0x') return null
    // standard Error(string) selector: 0x08c379a0
    if (data.startsWith('0x08c379a0')) {
      // skip selector (4 bytes) + offset (32 bytes) + string length (32 bytes) = 4 + 32 + 32 = 68 bytes = 136 hex chars + '0x' => 138
      const hex = '0x' + data.slice(138)
      return ethers.utils.toUtf8String(hex)
    }
    // ERC-165 / custom error - best effort: if it's short, return raw
    return data
  } catch (e) {
    return data
  }
}

async function simulateDeploy (factoryBytecode: string, deployTxData: string, deployerAddress: string) {
  // provider.call for contract creation simulation
  try {
    console.log('→ Running provider.call to simulate contract creation (to capture revert data)...')
    const callResult = await ethers.provider.call({
      from: deployerAddress,
      to: null, // contract creation
      data: deployTxData
    })
    console.log('simulate call result (hex):', callResult) // usually will not be reached if revert
    return { ok: true, data: callResult }
  } catch (err: any) {
    // ethers error wraps data differently across versions/providers
    console.error('simulate call threw (expected on revert). raw error:')
    console.error(err)

    // try to extract revert data
    const maybeData =
        err?.error?.data || err?.error?.data?.originalError || err?.data || err?.reason || err?.r || null

    // fallback: sometimes err has body with JSON
    let revertData: string | null = null
    if (typeof maybeData === 'string') {
      revertData = maybeData
    } else if (maybeData && typeof maybeData === 'object') {
      // some providers embed hex under keys like 'data' or '0x...'
      if (maybeData.data) revertData = maybeData.data
    }

    return { ok: false, error: err, data: revertData }
  }
}

async function main () {
  console.log('Starting Sepolia deployment (with debug)...')

  const [deployer] = await ethers.getSigners()
  console.log(`Deploying with account: ${deployer.address}`)

  const balance = await deployer.getBalance()
  console.log(`Account balance: ${ethers.utils.formatEther(balance)} ETH`)

  if (balance.lt(ethers.utils.parseEther('0.01'))) {
    console.warn('⚠️  Warning: Account balance is low. You may need more ETH for deployment.')
  }

  const network = await ethers.provider.getNetwork()
  console.log(`Network: ${network.name} (Chain ID: ${network.chainId})`)

  if (network.chainId !== 11155111) {
    throw new Error('This script is for Sepolia testnet only!')
  }

  // Pre-check: is there code at ENTRYPOINT_ADDRESS?
  const entryCode = await ethers.provider.getCode(ENTRYPOINT_ADDRESS)
  console.log(`EntryPoint code present? ${entryCode !== '0x'}`)
  if (entryCode === '0x') {
    console.warn(`⚠️ No contract code at ENTRYPOINT_ADDRESS ${ENTRYPOINT_ADDRESS} on this provider. This will likely cause deploy to revert.`)
  }

  // 2. Prepare deploy transaction but simulate first
  console.log('\n2. Preparing SimpleAccountFactory deploy transaction (simulation)...')
  const SimpleAccountFactory = await ethers.getContractFactory('SimpleAccountFactory')

  // build unsigned deploy transaction
  const deployTransactionRequest = SimpleAccountFactory.getDeployTransaction(ENTRYPOINT_ADDRESS)
  if (!deployTransactionRequest.data) {
    throw new Error('Cannot build deploy transaction data (no bytecode/data). Check contract compilation.')
  }

  // try estimateGas
  try {
    console.log('→ Attempting provider.estimateGas on deploy tx...')
    const gasEstimate = await ethers.provider.estimateGas({
      from: deployer.address,
      to: null, // contract creation
      data: deployTransactionRequest.data
    })
    console.log('estimateGas succeeded:', gasEstimate.toString())
  } catch (errEstimate: any) {
    console.error('estimateGas failed. Will attempt provider.call to capture revert data...')
    // simulate call to get revert reason
    const sim = await simulateDeploy(SimpleAccountFactory.bytecode, deployTransactionRequest.data, deployer.address)
    if (!sim.ok) {
      const raw = sim.data || sim.error
      const decoded = decodeRevertReason(sim.data || (sim.error && sim.error.data) || '')
      console.error('---- Deployment simulation indicates a revert ----')
      console.error('raw simulate data / error:', raw)
      console.error('decoded revert reason (if present):', decoded)
    } else {
      console.log('simulate call returned (no revert):', sim.data)
    }
    console.log('You can attempt a manual deploy with an explicit gasLimit to see on-chain revert reason.')
  }

  // Optionally attempt an actual deploy with manual gasLimit to capture on-chain revert / receipt
  // We try to deploy, but catch and print revert data if it fails.
  console.log('\n3. Attempting actual deployment (this will send tx) ...')
  try {
    // Adjust gasLimit if you want; here we try a reasonably high limit for debugging.
    const txResponse = await SimpleAccountFactory.deploy(ENTRYPOINT_ADDRESS, { gasLimit: 8_000_000 })
    console.log('Sent deploy tx:', txResponse.deployTransaction.hash)
    const receipt = await txResponse.deployTransaction.wait(1)
    console.log('Deploy receipt:', receipt)
    const factoryAddress = txResponse.address
    console.log(`✓ SimpleAccountFactory deployed to: ${factoryAddress}`)
    // Continue original script flow: wait confirmations, compute counterfactual and save config
    console.log('Waiting for confirmations...')
    await txResponse.deployTransaction.wait(3)

    // 3. Calculate some counterfactual account addresses for testing
    console.log('\n4. Calculating counterfactual account addresses...')
    const testOwners = [deployer.address]
    const testThreshold = 1
    const testGuardians: string[] = []
    const testGuardianThreshold = 0
    const testSalt = 0

    const factory = SimpleAccountFactory.attach(factoryAddress)
    const accountAddress = await factory.getAddress(
      testOwners,
      testThreshold,
      testGuardians,
      testGuardianThreshold,
      testSalt
    )
    console.log(`✓ Test account counterfactual address: ${accountAddress}`)

    // 4. Save deployment info
    console.log('\n5. Saving deployment configuration...')
    const deploymentInfo = {
      network: 'sepolia',
      chainId: network.chainId,
      deployer: deployer.address,
      entryPoint: ENTRYPOINT_ADDRESS,
      factory: factoryAddress,
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
    console.log('Network: Sepolia Testnet')
    console.log(`Chain ID: ${network.chainId}`)
    console.log(`EntryPoint: ${ENTRYPOINT_ADDRESS} (standard)`)
    console.log(`Factory: ${factoryAddress}`)
    console.log(`Test Account: ${accountAddress}`)
  } catch (err: any) {
    console.error('Deployment failed. Printing debug information...')

    // Try to extract revert data if present
    const data = err?.error?.data || err?.data || err?.reason || err?.error
    console.error('Raw error object:', err)
    if (typeof data === 'string' && data.startsWith('0x')) {
      const decoded = decodeRevertReason(data)
      console.error('Decoded revert reason:', decoded)
    } else {
      console.error('No hex revert data detected in error object.')
    }

    process.exit(1)
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('Script top-level error:', error)
    process.exit(1)
  })
