import {
    generatePrivateKey,
    privateKeyToAccount, // 新增
    english,           // 新增
} from 'viem/accounts'
import { HDKey } from '@scure/bip32'
import { mnemonicToSeedSync, generateMnemonic } from '@scure/bip39'
import {type Address, type PrivateKeyAccount, createWalletClient, custom, http, createPublicClient} from 'viem'
import { AAAccount, type SafeConfig, type SafeAccountConfig } from './Account.ts'
import { Wallet as EthersWallet } from 'ethers';
import {safeApiKit} from "../Utils/SafeApiKit.ts";
import {sepolia} from "viem/chains";
import {type Chain, type PublicClient, type Transport} from "viem";
import * as url from "node:url";
/**
 * 钱包配置
 */
export interface WalletImportConfig {
    // 二选一：私钥或助记词
    privateKey?: `0x${string}`
    mnemonic?: string              // 新增
}


/**
 * 钱包导出配置
 */
export interface WalletExportConfig {
    privateKey: `0x${string}`
    mnemonic?: string
    controllerAddress: Address
    aaAccounts: Array<{
        safeAddress: Address
        name?: string
        owners: Address[]
        threshold: number
    }>
}

/**
 * 钱包摘要信息
 */
export interface WalletSummary {
    controllerAddress: Address
    hasMnemonic: boolean
    aaAccountCount: number
    aaAccounts: Array<{
        safeAddress: Address
        name?: string
        isDeployed: boolean
    }>
}

/**
 * Wallet 类 - 简化版钱包
 *
 * 设计原则：
 * 1. 一个钱包 = 一个私钥 = 一个控制者 EOA
 * 2. 可以控制多个 Safe 智能账户
 * 3. 不使用 HD 钱包派生
 */
export class Wallet {
    // ==================== 私有属性 ====================

    /**
     * 控制者私钥账户（EOA）
     */
    private controllerAccount: PrivateKeyAccount
    private privateKey: `0x${string}`  // 新增：保存私钥
    private mnemonic?: string          // 新增：保存助记词
    /**
     * 所有智能账户（Safe）
     */
    public ChainID: number
    public Chain:Chain
    private aaAccounts: AAAccount[] = []
    public walletClient
    public publicClient
    // ==================== 构造函数 ====================

    /**
     * 创建或导入钱包
     *
     * @param config - 钱包配置
     * @param config.privateKey - 可选，导入已有私钥；不提供则生成新私钥
     *
     * @example
     * // 创建新钱包
     * const wallet = new Wallet()
     *
     * // 导入已有私钥
     * const wallet = new Wallet({
     *     privateKey: '0x...'
     * })
     */
    constructor(config?: WalletImportConfig) {
        if (config?.privateKey && config?.mnemonic) {
            throw new Error('不能同时提供 privateKey 和 mnemonic')
        }
        this.ChainID = 11155111
        let existingSafeAddrList = []
        if (config?.mnemonic) {
            // 从助记词导入
            this.mnemonic = config.mnemonic
            const wallet_temp = EthersWallet.fromPhrase(this.mnemonic)

            //
            // !! 修正 !!
            // 直接使用 ethers 返回的私钥字符串
            //
            this.privateKey = wallet_temp.privateKey as `0x${string}`

            this.controllerAccount = privateKeyToAccount(this.privateKey)

        } else if (config?.privateKey) {
            // 从私钥导入
            this.privateKey = config.privateKey
            this.controllerAccount = privateKeyToAccount(config.privateKey)
            this.mnemonic = undefined

        } else {
            // 生成新钱包（创建助记词）
            this.mnemonic = generateMnemonic(english)
            const seed = mnemonicToSeedSync(this.mnemonic, '')
            const hdKey = HDKey.fromMasterSeed(seed)   // 新增：从助记词创建 HDKey 对象f
            const privateKeyAccount = hdKey.derive("m/44'/60'/0'/0/0")
            this.privateKey = `0x${Buffer.from(privateKeyAccount.privateKey!).toString('hex')}` as `0x${string}`
            this.controllerAccount = privateKeyToAccount(this.privateKey)
        }
        this.walletClient = createWalletClient({
            chain: sepolia,
            account: this.controllerAccount,
            transport: http('https://eth-sepolia.api.onfinality.io/public')
        })
        this.publicClient = createPublicClient({
            chain: sepolia,
            transport: http('https://eth-sepolia.api.onfinality.io/public')
        })
        existingSafeAddrList = safeApiKit(this.ChainID,this.controllerAccount.address)
        let index = 0;
        for (let i = 0; i < existingSafeAddrList.length; i++) {
            const newconfig = {
                safeAddress: existingSafeAddrList[i].safeAddress,
                bundlerUrl: 'https://api.pimlico.io/v2/11155111/rpc?apikey=pim_gdR7HaA5MpQ5PK3HMdSTkr',
                rpcUrl: 'https://eth-sepolia.api.onfinality.io/public',
                chainId: existingSafeAddrList[i].chainId ? existingSafeAddrList[i].chainId : this.ChainID
            }
            const safeAccount = this.createSafeAccount(newconfig,String(BigInt(index)))
            this.aaAccounts.push(safeAccount)
        }
    }


    // ==================== Getter 属性 ====================

    /**
     * 获取控制者 EOA 地址
     */
    get controllerAddress(): Address {
        return this.controllerAccount.address
    }

    /**
     * 获取所有智能账户
     */
    get safeAccounts(): readonly AAAccount[] {
        return Object.freeze([...this.aaAccounts])
    }

    // ==================== 私钥管理 ====================

    /**
     * 获取控制者账户对象（用于签名）
     *
     * @internal
     */
    getControllerAccount(): PrivateKeyAccount {
        return this.controllerAccount
    }

    // ==================== Safe 账户管理 ====================

    /**
     * 创建或导入 Safe 智能账户
     *
     * @param config - Safe 配置
     * @param name - 可选，账户名称
     *
     * @example
     * // 创建新的单签 Safe
     * const safe = await wallet.createSafeAccount({
     *     owners: [wallet.controllerAddress],
     *     threshold: 1,
     *     bundlerUrl: 'https://...',
     *     rpcUrl: 'https://...',
     *     chainId: 11155111
     * }, '我的主钱包')
     *
     * // 导入已存在的 Safe
     * const existingSafe = await wallet.createSafeAccount({
     *     safeAddress: '0x...',
     *     bundlerUrl: 'https://...',
     *     rpcUrl: 'https://...',
     *     chainId: 11155111
     * }, '导入的钱包')
     */
    async createSafeAccount(
        config: SafeConfig,
        name?: string
    ): Promise<AAAccount> {
        // 验证：如果创建新 Safe，controllerAddress 必须在 owners 中
        if (!('safeAddress' in config) && 'owners' in config) {
            if (!config.owners.includes(this.controllerAccount)) {
                throw new Error(
                    `Controller address ${this.controllerAddress} must be in owners list`
                )
            }
        }

        // 创建 AAAccount
        const aaAccount = new AAAccount(
            this.controllerAccount,
            config,
            name
        )

        // ✅ 重要：必须调用 initialize
        await aaAccount.initialize(config)

        // 如果导入已存在的 Safe，验证 controllerAddress 是否是 owner
        if ('safeAddress' in config && config.safeAddress) {
            const isOwner = await aaAccount.isOwner(this.controllerAddress)
            if (!isOwner) {
                throw new Error(
                    `Controller address ${this.controllerAddress} is not an owner of Safe ${config.safeAddress}`
                )
            }
        }

        // 添加到列表
        this.aaAccounts.push(aaAccount)

        return aaAccount
    }

    /**
     * 通过 Safe 地址获取账户
     *
     * @param safeAddress - Safe 合约地址
     * @returns Safe 账户，未找到返回 undefined
     */
    get hasMnemonic(): boolean {
        return this.mnemonic !== undefined
    }

    getSafeAccount(safeAddress: Address): AAAccount | undefined {
        return this.aaAccounts.find(
            account => account.safeAddress.toLowerCase() === safeAddress.toLowerCase()
        )
    }

    /**
     * 通过名称获取账户
     *
     * @param name - 账户名称
     * @returns Safe 账户，未找到返回 undefined
     */
    getSafeAccountByName(name: string): AAAccount | undefined {
        return this.aaAccounts.find(account => account.name === name)
    }

    /**
     * 删除 Safe 账户
     *
     * @param safeAddress - Safe 合约地址
     * @returns 是否删除成功
     */
    removeSafeAccount(safeAddress: Address): boolean {
        const index = this.aaAccounts.findIndex(
            account => account.safeAddress.toLowerCase() === safeAddress.toLowerCase()
        )

        if (index !== -1) {
            this.aaAccounts.splice(index, 1)
            return true
        }

        return false
    }

    /**
     * 更新 Safe 账户名称
     *
     * @param safeAddress - Safe 合约地址
     * @param newName - 新名称
     * @returns 是否更新成功
     */
    updateSafeAccountName(safeAddress: Address, newName: string): boolean {
        const account = this.getSafeAccount(safeAddress)
        if (account) {
            account.name = newName
            return true
        }
        return false
    }

    // ==================== 批量操作 ====================

    /**
     * 获取所有已部署的 Safe 账户
     */
    getDeployedSafeAccounts(): AAAccount[] {
        return this.aaAccounts.filter(account => account.isDeployed())
    }

    /**
     * 获取所有未部署的 Safe 账户
     */
    getUndeployedSafeAccounts(): AAAccount[] {
        return this.aaAccounts.filter(account => !account.isDeployed())
    }

    /**
     * 获取所有单签 Safe 账户（threshold = 1）
     */
    async getSingleSignerSafeAccounts(): Promise<AAAccount[]> {
        const results = await Promise.all(
            this.aaAccounts.map(async account => ({
                account,
                threshold: await account.getThreshold()
            }))
        )

        return results
            .filter(({ threshold }) => threshold === 1)
            .map(({ account }) => account)
    }

    /**
     * 获取所有多签 Safe 账户（threshold > 1）
     */
    async getMultiSignerSafeAccounts(): Promise<AAAccount[]> {
        const results = await Promise.all(
            this.aaAccounts.map(async account => ({
                account,
                threshold: await account.getThreshold()
            }))
        )

        return results
            .filter(({ threshold }) => threshold > 1)
            .map(({ account }) => account)
    }

    // ==================== 钱包信息 ====================

    /**
     * 获取钱包摘要信息
     */
    async getSummary(): Promise<WalletSummary> {
        const aaAccounts = await Promise.all(
            this.aaAccounts.map(async account => ({
                safeAddress: account.safeAddress,
                name: account.name,
                isDeployed: account.isDeployed()
            }))
        )

        return {
            controllerAddress: this.controllerAddress,
            hasMnemonic: this.hasMnemonic,  // 新增
            aaAccountCount: this.aaAccounts.length,
            aaAccounts
        }
    }
    exportPrivateKey(): `0x${string}` {
        return this.privateKey  // 直接返回保存的私钥
    }

    /**
     * 导出钱包配置（用于备份或迁移）
     * ⚠️ 包含私钥，请安全存储
     */
    async exportConfig(): Promise<WalletExportConfig> {
        const aaAccounts = await Promise.all(
            this.aaAccounts.map(async account => ({
                safeAddress: account.safeAddress,
                name: account.name,
                owners: await account.getOwners(),
                threshold: await account.getThreshold()
            }))
        )

        return {
            privateKey: this.exportPrivateKey(),
            mnemonic: this.hasMnemonic ? this.exportMnemonic() : undefined,  // 新增
            controllerAddress: this.controllerAddress,
            aaAccounts
        }
    }

    /**
     * 从导出的配置恢复钱包
     *
     * @param exportedConfig - 导出的配置
     * @param safeConfigs - Safe 连接配置（bundlerUrl, rpcUrl 等）
     *
     * @example
     * const wallet = await Wallet.fromExportedConfig(
     *     exportedConfig,
     *     {
     *         bundlerUrl: 'https://...',
     *         rpcUrl: 'https://...',
     *         chainId: 11155111
     *     }
     * )
     */

    // ==================== 实用方法 ====================

    /**
     * 打印钱包信息（用于调试）
     */
    async printInfo(): Promise<void> {
        const summary = await this.getSummary()
        console.log('Has Mnemonic:', summary.hasMnemonic ? 'Yes' : 'No')  // 新增
        console.log('\n===== Wallet Info =====')
        console.log('Controller Address:', summary.controllerAddress)
        console.log('Safe Accounts:', summary.aaAccountCount)
        console.log('')

        for (const account of summary.aaAccounts) {
            console.log(`Safe: ${account.safeAddress}`)
            console.log(`  Name: ${account.name || '(unnamed)'}`)
            console.log(`  Deployed: ${account.isDeployed ? 'Yes' : 'No'}`)
            console.log('')
        }
    }

    exportMnemonic(): string {
        if (!this.mnemonic) {
            throw new Error('此钱包没有助记词（通过私钥导入）')
        }
        return this.mnemonic
    }

}
