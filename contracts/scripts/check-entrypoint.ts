/**
 * Check if EntryPoint exists at the standard address on Sepolia
 */

import { ethers } from 'hardhat'

const STANDARD_ENTRYPOINT = '0x0000000071727De22E5E9d8BAf0edAc6f37da032'

async function main() {
  console.log('Checking EntryPoint on Sepolia...\n')

  const network = await ethers.provider.getNetwork()
  console.log(`Network: ${network.name} (Chain ID: ${network.chainId})`)

  if (network.chainId !== 11155111) {
    console.error('❌ This script is for Sepolia testnet only!')
    process.exit(1)
  }

  console.log(`\nChecking address: ${STANDARD_ENTRYPOINT}`)

  // Check if contract exists at this address
  const code = await ethers.provider.getCode(STANDARD_ENTRYPOINT)

  if (code === '0x' || code === '0x0') {
    console.log('❌ No contract found at this address!')
    console.log('\nThe standard EntryPoint v0.7 is NOT deployed on Sepolia yet.')
    console.log('\n📝 Options:')
    console.log('1. Deploy your own EntryPoint (modify deploy-sepolia.ts to deploy EntryPoint)')
    console.log('2. Use a different EntryPoint address if one is already deployed')
    console.log('3. Wait for official EntryPoint v0.7 deployment on Sepolia')
  } else {
    console.log('✅ Contract exists at this address!')
    console.log(`   Code length: ${code.length} bytes`)

    // Try to get senderCreator (required by SimpleAccountFactory)
    try {
      const entryPoint = await ethers.getContractAt('IEntryPoint', STANDARD_ENTRYPOINT)
      const senderCreator = await entryPoint.senderCreator()
      console.log(`✅ SenderCreator: ${senderCreator}`)
      console.log('\n✅ This EntryPoint is compatible with our SimpleAccountFactory!')
    } catch (error) {
      console.log('⚠️  Could not verify EntryPoint interface')
      console.log('   The contract exists but may not be a valid EntryPoint')
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error)
    process.exit(1)
  })
