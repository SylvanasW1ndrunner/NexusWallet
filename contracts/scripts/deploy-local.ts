/**
 * Simple local deployment script for testing
 * Deploys EntryPoint and SimpleAccountFactory to local Hardhat node
 */

import { ethers } from 'hardhat'
import * as fs from 'fs'
import * as path from 'path'

async function main() {
  console.log('Starting deployment...')

  const [deployer] = await ethers.getSigners()
  console.log(`Deploying with account: ${deployer.address}`)
  console.log(`Account balance: ${ethers.utils.formatEther(await deployer.getBalance())} ETH`)

  // 1. Deploy EntryPoint
  console.log('\n1. Deploying EntryPoint...')
  const EntryPoint = await ethers.getContractFactory('EntryPoint')
  const entryPoint = await EntryPoint.deploy()
  await entryPoint.deployed()
  console.log(`✓ EntryPoint deployed to: ${entryPoint.address}`)

  // 2. Deploy SimpleAccountFactory
  console.log('\n2. Deploying SimpleAccountFactory...')
  const SimpleAccountFactory = await ethers.getContractFactory('SimpleAccountFactory')
  const factory = await SimpleAccountFactory.deploy(entryPoint.address)
  await factory.deployed()
  console.log(`✓ SimpleAccountFactory deployed to: ${factory.address}`)

  // 3. Calculate some counterfactual account addresses for testing
  console.log('\n3. Calculating counterfactual account addresses...')

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
  console.log(`✓ Test account counterfactual address: ${accountAddress}`)

  // 4. Save deployment info to backend
  console.log('\n4. Saving deployment configuration...')
  const deploymentInfo = {
    network: 'localhost',
    chainId: (await ethers.provider.getNetwork()).chainId,
    deployer: deployer.address,
    entryPoint: entryPoint.address,
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
  const outputPath = path.join(backendPath, 'local_deployment.json')

  fs.mkdirSync(backendPath, { recursive: true })
  fs.writeFileSync(outputPath, JSON.stringify(deploymentInfo, null, 2))
  console.log(`✓ Deployment info saved to: ${outputPath}`)

  console.log('\n✅ Deployment complete!')
  console.log('\nDeployment Summary:')
  console.log('==================')
  console.log(`Network: localhost`)
  console.log(`Chain ID: ${deploymentInfo.chainId}`)
  console.log(`EntryPoint: ${entryPoint.address}`)
  console.log(`Factory: ${factory.address}`)
  console.log(`Test Account: ${accountAddress}`)
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error)
    process.exit(1)
  })
