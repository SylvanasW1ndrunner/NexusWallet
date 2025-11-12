import { Wallet } from '../accounts/Wallet'

async function main() {
    // 创建钱包
    const wallet = new Wallet()

    // 创建 EOA 账户
    const eoa1 = wallet.createEOAAccount()
    console.log('EOA Address:', eoa1.address)

    // 创建 AA 账户（异步）
    const aaAccount = await wallet.createAAAccount(
        {
            owners: [eoa1.address],
            threshold: 1,
            bundlerUrl: 'https://api.pimlico.io/v2/11155111/rpc?apikey=pim_gdR7HaA5MpQ5PK3HMdSTkr',
            chainId: 84532, // Base Sepolia
            rpcUrl: 'https://eth-sepolia.api.onfinality.io/public',
            safeVersion: '1.4.1',
            saltNonce: '0', // 可选
            // Paymaster 配置（可选
        },
        1
    )

    console.log('AA Safe Address:', aaAccount.getSafeAddress())
    console.log('AA Signer Address:', aaAccount.getSignerAddress())
}

main()
