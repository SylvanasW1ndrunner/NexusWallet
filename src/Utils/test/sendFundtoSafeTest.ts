// @ts-ignore
// @ts-ignore

import {sendFundtoSafe} from "../sendFundtoSafe.ts"
import {Wallet} from "../../accounts/Wallet.ts";
import type {Address} from "viem";

const TEST_CONFIG = {
    CHAIN_ID: 11155111,
    RPC_URL: 'https://eth-sepolia.api.onfinality.io/public',
    BUNDLER_URL: 'https://api.pimlico.io/v2/11155111/rpc?apikey=pim_gdR7HaA5MpQ5PK3HMdSTkr',

    // 导入测试用
    EXISTING_PRIVATE_KEY: '0x0000000000000000000000000000000000000000000000000000000000000000' as `0x${string}`,
    EXISTING_MNEMONIC: 'thing scrap return craft extra indicate expand demise riot shallow night chest',  // 新增
    EXISTING_SAFE_ADDRESS: '0x8B13872725C881050Bf1311d2EA5DdD3616F661C' as Address,
}

const wallet = new Wallet({ mnemonic:'thing scrap return craft extra indicate expand demise riot shallow night chest' })
const importedSafe = await wallet.createSafeAccount(
    {
        safeAddress: TEST_CONFIG.EXISTING_SAFE_ADDRESS,
        bundlerUrl: TEST_CONFIG.BUNDLER_URL,
        rpcUrl: TEST_CONFIG.RPC_URL,
        chainId: TEST_CONFIG.CHAIN_ID,
    },
    '导入的 Safe'
)

let txhash = await sendFundtoSafe(100n,wallet,importedSafe.safeAddress)
console.log(txhash)