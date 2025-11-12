import { privateKeyToAccount } from 'viem/accounts'
import type { Address } from 'viem'
import type { PrivateKeyAccount } from 'viem'
import { Safe4337Pack } from '@safe-global/relay-kit'
import type { Safe4337CreateTransactionProps } from '@safe-global/relay-kit'

// ==================== BaseAccount 基类 ====================
export abstract class BaseAccount {
    public address: Address
    public derivationPath: string

    constructor(address: Address, derivationPath: string) {
        this.address = address
        this.derivationPath = derivationPath
    }

    getAddress(): Address {
        return this.address
    }

    getDerivationPath(): string {
        return this.derivationPath
    }

    abstract getAccountType(): 'EOA' | 'AA'
}

// ==================== EOAAccount 类 ====================
export class EOAAccount extends BaseAccount {
    private prikey: `0x${string}`
    public account: PrivateKeyAccount

    constructor(privateKey: `0x${string}`, derivationPath: string) {
        const account = privateKeyToAccount(privateKey)
        super(account.address, derivationPath)

        this.prikey = privateKey
        this.account = account
    }

    getAccountType(): 'EOA' {
        return 'EOA'
    }

    getPrivateKey(): `0x${string}` {
        return this.prikey
    }

    getViemAccount(): PrivateKeyAccount {
        return this.account
    }
}

// ==================== AA Account 相关接口 ====================

/**
 * Safe 4337 配置接口
 */
export interface Safe4337Config {
    // Safe 账户基础配置
    owners: Address[]
    threshold: number
    saltNonce?: string

    // 4337 相关配置
    entryPoint?: Address
    bundlerUrl: string

    // Paymaster 配置（可选）
    paymasterUrl?: string
    paymasterAddress?: Address
    isSponsored?: boolean,
    paymasterTokenAddress?: Address
    sponsorshipPolicyId?: `0x${string}`

    // Safe 版本和链信息
    safeVersion?: string
    chainId: number

    // RPC 配置
    rpcUrl: string
}

/**
 * AA 账户签名者信息
 * 这是从 HD 钱包派生出来的子账户信息
 */
export interface AASignerInfo {
    signerAddress: Address
    signerPrivateKey: `0x${string}`
    signerAccount: PrivateKeyAccount
    derivationPath: string
}

/**
 * Safe 账户部署信息
 */
export interface SafeDeploymentInfo {
    isDeployed: boolean
    predictedAddress: Address
    deploymentTxHash?: `0x${string}`
}

/**
 * Safe 账户初始化选项
 */
export interface SafeAccountInitOptions {
    signerInfo: AASignerInfo
    config: Safe4337Config
}

// ==================== AAAccount 类 ====================
export class AAAccount extends BaseAccount {
    // 从 HD 钱包派生的签名者信息
    private signerInfo: AASignerInfo

    // Safe 4337 配置
    public config: Safe4337Config

    // Safe 账户部署信息
    public deploymentInfo: SafeDeploymentInfo

    // Safe4337Pack 实例
    public safe4337Pack: Safe4337Pack

    // Safe 账户地址（Safe 智能合约地址）
    public safeAddress: Address

    private constructor(
        signerInfo: AASignerInfo,
        config: Safe4337Config,
        safe4337Pack: Safe4337Pack,
        safeAddress: Address
    ) {
        super(safeAddress, signerInfo.derivationPath)

        this.signerInfo = signerInfo
        this.config = config
        this.safe4337Pack = safe4337Pack
        this.safeAddress = safeAddress

        this.deploymentInfo = {
            isDeployed: false,
            predictedAddress: safeAddress
        }
    }

    /**
     * 创建 AA 账户的静态工厂方法
     * 使用 async 初始化 Safe4337Pack
     */
    static async create(
        signerInfo: AASignerInfo,
        config: Safe4337Config
    ): Promise<AAAccount> {
        // 初始化 Safe4337Pack
        const safe4337Pack = await Safe4337Pack.init({
            // 签名者配置
            provider: config.rpcUrl,
            signer: signerInfo.signerPrivateKey,

            // Bundler 配置
            bundlerUrl: config.bundlerUrl,

            // Safe 配置
            options: {
                owners: config.owners,
                threshold: config.threshold,
                saltNonce: config.saltNonce,
            },

            // Paymaster 配置（可选）
            paymasterOptions: config.paymasterUrl ? {
                paymasterUrl: config.paymasterUrl,
                paymasterAddress: config.paymasterAddress,
                isSponsored: config.isSponsored,
                paymasterTokenAddress: config.paymasterTokenAddress,
                sponsorshipPolicyId: config.sponsorshipPolicyId
            } : undefined,
        })
        const safeAddress = await safe4337Pack.protocolKit.getAddress() as Address
        return new AAAccount(
            signerInfo,
            config,
            safe4337Pack,
            safeAddress
        )
    }


    getAccountType(): 'AA' {
        return 'AA'
    }

    /**
     * 获取签名者地址
     */
    getSignerAddress(): Address {
        return this.signerInfo.signerAddress
    }

    /**
     * 获取签名者私钥（谨慎使用）
     */
    getSignerPrivateKey(): `0x${string}` {
        return this.signerInfo.signerPrivateKey
    }

    /**
     * 获取签名者 viem account
     */
    getSignerAccount(): PrivateKeyAccount {
        return this.signerInfo.signerAccount
    }

    /**
     * 获取签名者信息
     */
    getSignerInfo(): Readonly<AASignerInfo> {
        return { ...this.signerInfo }
    }

    /**
     * 检查地址是否是 owner
     */
    isOwner(address: Address): boolean {
        return this.config.owners.some(
            owner => owner.toLowerCase() === address.toLowerCase()
        )
    }

    /**
     * 获取 EntryPoint 地址
     */
    getEntryPoint(): Address {
        return this.config.entryPoint
    }

    /**
     * 获取 Bundler URL
     */
    getBundlerUrl(): string {
        return this.config.bundlerUrl
    }

    /**
     * 获取 Safe 地址
     */
    getSafeAddress(): Address {
        return this.safeAddress
    }

    /**
     * 更新部署状态
     */
    updateDeploymentStatus(isDeployed: boolean, txHash?: `0x${string}`): void {
        this.deploymentInfo.isDeployed = isDeployed
        if (txHash) {
            this.deploymentInfo.deploymentTxHash = txHash
        }
    }

    /**
     * 检查 Safe 是否已部署
     */
    isDeployed(): boolean {
        return this.deploymentInfo.isDeployed
    }

    /**
     * 创建用户操作交易
     */
    async createTransaction(
        transactions: Safe4337CreateTransactionProps['transactions']
    ) {
        return await this.safe4337Pack.createTransaction({
            transactions
        })
    }

    /**
     * 签名用户操作
     */
    async signUserOperation(safeOperation: any) {
        return await this.safe4337Pack.signSafeOperation(safeOperation)
    }

    /**
     * 执行用户操作（通过 Bundler）
     */
    async executeUserOperation(signedSafeOperation: any) {
        const userOperationHash = await this.safe4337Pack.executeTransaction({
            executable: signedSafeOperation
        })
        return userOperationHash
    }

    /**
     * 获取用户操作收据
     */
    async getUserOperationReceipt(userOperationHash: string) {
        // 需要使用 bundler client
        // 这里可以通过 safe4337Pack 内部的 bundler 获取
        return await this.safe4337Pack.getUserOperationReceipt(userOperationHash)
    }

    /**
     * 获取 Safe 账户余额
     */
    async getBalance(): Promise<bigint> {
        // 使用 viem 或者其他方式获取余额
        // 需要传入 provider
        return 0n // 占位符
    }

    /**
     * 导出账户配置（不含私钥）
     */
    exportConfig() {
        return {
            address: this.address,
            safeAddress: this.safeAddress,
            signerAddress: this.signerInfo.signerAddress,
            derivationPath: this.derivationPath,
            owners: this.config.owners,
            threshold: this.config.threshold,
            entryPoint: this.config.entryPoint,
            bundlerUrl: this.config.bundlerUrl,
            chainId: this.config.chainId,
            isDeployed: this.deploymentInfo.isDeployed,
            predictedAddress: this.deploymentInfo.predictedAddress,
            deploymentTxHash: this.deploymentInfo.deploymentTxHash
        }
    }
}
