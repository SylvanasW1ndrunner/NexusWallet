import { Safe } from '@gnosis.pm/safe-core-sdk'
const SAFE_API_ENDPOINTS: Record<number, string> = {
    1: 'https://safe-transaction-mainnet.safe.global',        // Ethereum Mainnet
    5: 'https://safe-transaction-goerli.safe.global',         // Goerli (deprecated)
    11155111: 'https://safe-transaction-sepolia.safe.global', // Sepolia
    10: 'https://safe-transaction-optimism.safe.global',      // Optimism
    420: 'https://safe-transaction-optimism-goerli.safe.global', // Optimism Goerli
    137: 'https://safe-transaction-polygon.safe.global',      // Polygon
    42161: 'https://safe-transaction-arbitrum.safe.global',   // Arbitrum One
    100: 'https://safe-transaction-gnosis-chain.safe.global', // Gnosis Chain
    8453: 'https://safe-transaction-base.safe.global',        // Base
    84531: 'https://safe-transaction-base-goerli.safe.global', // Base Goerli
}

export async function getSafeAccountByAddr(chainId, safeAddress) {
    const safe_endpoint = SAFE_API_ENDPOINTS[chainId] + '/api/v1/owners/' + safeAddress + '/safes/';
    const response = await fetch(safe_endpoint);
    const data = await response.json();
    const address_list = data["safes"]
    return address_list
}

export async function proposeTransaction()

