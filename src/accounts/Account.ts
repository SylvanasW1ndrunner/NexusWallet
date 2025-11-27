import {
    createSmartAccountClient,
    type SmartAccountClient,
} from 'permissionless'
import { toSafeSmartAccount } from 'permissionless/accounts'
import { createBundlerClient,createPaymasterClient } from 'viem/account-abstraction'
import {
    createPublicClient,
    http,
    type Address,
    type Chain,
    type PublicClient,
    type Transport,
    type Hash
} from 'viem'
import type { PrivateKeyAccount } from 'viem/accounts'
import type { EntryPoint } from 'permissionless/types/entrypoint'
import { entryPoint06Address } from "viem/account-abstraction"
import {ToSafeSmartAccountReturnType} from "permissionless/accounts/safe/toSafeSmartAccount.ts";
// ==================== 类型定义 ====================

/**
 * Safe 配置 - 创建新 Safe
 */
export interface SafeCreateConfig {
    owners: PrivateKeyAccount[]
    threshold: number
    bundlerUrl: string
    rpcUrl: string
    chainId: number
    paymasterUrl?: string
}

/**
 * Safe 配置 - 导入已存在的 Safe
 */
export interface SafeImportConfig {
    safeAddress: Address
    bundlerUrl: string
    rpcUrl: string
    chainId: number
    paymasterUrl?: string
}

/**
 * Safe 配置联合类型
 */
export type SafeConfig = SafeCreateConfig | SafeImportConfig

/**
 * Safe 账户完整配置（用于导出）
 */
export interface SafeAccountConfig {
    safeAddress: Address
    controllerAddress: Address
    name?: string
    owners: Address[]
    threshold: number
    chainId: number
    isDeployed: boolean
}

/**
 * 交易调用
 */
export interface Call {
    to: Address
    value: bigint
    data: `0x${string}`
}

// ==================== 辅助函数 ====================

/**
 * 根据 chainId 获取 Chain 对象
 */
function getChain(chainId: number, rpcUrl: string): Chain {
    return {
        id: chainId,
        name: `Chain ${chainId}`,
        nativeCurrency: {
            name: 'Ether',
            symbol: 'ETH',
            decimals: 18
        },
        rpcUrls: {
            default: { http: [rpcUrl] },
            public: { http: [rpcUrl] }
        }
    } as Chain
}

// ==================== AAAccount 类 ====================

/**
 * AA 智能账户（Safe）
 *
 * 基于官方文档实现：
 * https://docs.safe.global/advanced/erc-4337/guides/permissionless-quickstart
 */
export class AAAccount {
    // ==================== 公开属性 ====================

    /**
     * Safe 合约地址
     */
    safeAddress!: Address

    /**
     * 控制者 EOA 账户
     */
    readonly controllerEOA: PrivateKeyAccount

    /**
     * 账户名称
     */
    name?: string

    // ==================== 私有属性 ====================

    private safeAccount!: ToSafeSmartAccountReturnType
    private smartAccountClient!: SmartAccountClient
    private publicClient: PublicClient
    private bundlerUrl: string
    private rpcUrl: string
    private chainId: number
    private chain: Chain
    private paymasterUrl?: string

    // Safe 配置缓存
    private _isDeployed?: boolean
    private _owners?: Address[]
    private _threshold?: number

    // ==================== 构造函数 ====================

    /**
     * 创建 AA 账户
     *
     * @param controllerAccount - 控制者 EOA 账户
     * @param config - Safe 配置
     * @param name - 可选，账户名称
     */
    constructor(
        controllerAccount: PrivateKeyAccount,
        config: SafeConfig,
        name?: string
    ) {
        this.controllerEOA = controllerAccount
        this.name = name
        this.bundlerUrl = config.bundlerUrl
        this.rpcUrl = config.rpcUrl
        this.chainId = config.chainId
        this.paymasterUrl = config.paymasterUrl

        // 创建 Chain 对象
        this.chain = getChain(config.chainId, config.rpcUrl)

        // 创建 Public Client
        this.publicClient = createPublicClient({
            chain: this.chain,
            transport: http(config.rpcUrl)
        })
    }

    /**
     * 初始化 Safe 账户
     * 必须在创建后调用一次
     */
    async initialize(config: SafeConfig): Promise<void> {
        // 步骤 1: 创建 Safe Account
        this._owners = config.owners
        this._threshold = config.threshold
        if ('safeAddress' in config && config.safeAddress) {
            // 导入已存在的 Safe
            this.safeAccount = await toSafeSmartAccount({
                client: this.publicClient,
                owners: [this.controllerEOA],
                version: "1.4.1",
                entryPoint: {
                    address: entryPoint06Address,
                    version: "0.6"
                },
                address: config.safeAddress,
            })
            this.safeAddress = config.safeAddress
        } else {
            // 创建新 Safe
            const createConfig = config as SafeCreateConfig

            this.safeAccount = await toSafeSmartAccount({
                client: this.publicClient,
                owners: createConfig.owners,
                version: '1.4.1',
                entryPoint: {
                    version: '0.6',
                    address: entryPoint06Address
                },
                saltNonce: 0n,
                threshold: BigInt(createConfig.threshold),
            })
            this.safeAddress = this.safeAccount.address
        }

        // 步骤 2: 创建 Bundler Client
        const bundlerClient = createBundlerClient({
            client:this.safeAccount,
            transport: http(this.bundlerUrl),
        })

        // 步骤 3: 创建 Paymaster Client（如果提供）
        const paymasterClient = this.paymasterUrl
            ? createPaymasterClient({
                transport: http(this.paymasterUrl)
            })
            : undefined

        // 步骤 4: 创建 Smart Account Client
        this.smartAccountClient = createSmartAccountClient({
            account: this.safeAccount,
            chain: this.chain,
            bundlerTransport: http(this.bundlerUrl),
            paymaster: paymasterClient,
            userOperation: {
                estimateFeesPerGas: async () => {
                    return bundlerClient.estimateUserOperationGas // only when using pimlico bundler
                },
            }
        })

        // 步骤 5: 检查 Safe 是否已部署并缓存配置
        await this.refreshConfig()
    }

    // ==================== 配置刷新 ====================

    /**
     * 刷新 Safe 配置（从链上读取）
     */
    async refreshConfig(): Promise<void> {
        // 检查是否已部署
        const code = await this.publicClient.getBytecode({
            address: this.safeAddress
        })
        this._isDeployed = code !== undefined && code !== '0x'

        // 如果已部署，读取 owners 和 threshold
        if (this._isDeployed) {
            try {
                // 读取 owners
                this._owners = await this.publicClient.readContract({
                    address: this.safeAddress,
                    abi: [
                        {
                            inputs: [],
                            name: 'getOwners',
                            outputs: [{ type: 'address[]' }],
                            stateMutability: 'view',
                            type: 'function'
                        }
                    ],
                    functionName: 'getOwners'
                }) as Address[]

                // 读取 threshold
                this._threshold = Number(await this.publicClient.readContract({
                    address: this.safeAddress,
                    abi: [
                        {
                            inputs: [],
                            name: 'getThreshold',
                            outputs: [{ type: 'uint256' }],
                            stateMutability: 'view',
                            type: 'function'
                        }
                    ],
                    functionName: 'getThreshold'
                }))
            } catch (error) {
                console.warn('无法读取 Safe 配置:', error)
            }
        }
    }

    // ==================== Safe 信息查询 ====================

    /**
     * 检查 Safe 是否已部署
     */
    isDeployed(): boolean {
        return this._isDeployed ?? false
    }

    /**
     * 获取 Safe 的所有 owner 地址
     */
    async getOwners(): Promise<Address[]> {
        if (!this._isDeployed) {
            return this._owners!
        }
        await this.refreshConfig()

        return this._owners!
    }

    /**
     * 获取 Safe 的签名阈值
     */
    async getThreshold(): Promise<number> {
        if (!this._isDeployed) {
            return this._threshold!
        }

        await this.refreshConfig()

        return this._threshold!
    }

    /**
     * 检查地址是否是 Safe 的 owner
     */
    async isOwner(address: Address): Promise<boolean> {
        const owners = await this.getOwners()
        return owners.some(
            owner => owner.toLowerCase() === address.toLowerCase()
        )
    }

    /**
     * 获取 Safe 的 nonce
     */
    async getNonce(): Promise<bigint> {
        return await this.safeAccount.getNonce()
    }

    /**
     * 获取 Safe 的余额
     */
    async getBalance(): Promise<bigint> {
        return await this.publicClient.getBalance({
            address: this.safeAddress
        })
    }

    // ==================== 交易操作 ====================

    /**
     * 发送单个交易
     *
     * @example
     * const txHash = await safe.sendTransaction({
     *     to: '0x...',
     *     value: parseEther('0.1'),
     *     data: '0x'
     * })
     */
    async sendTransaction(call: Call): Promise<Hash> {
        return await this.sendTransactions([call])
    }

    /**
     * 批量发送交易
     *
     * @example
     * const txHash = await safe.sendTransactions([
     *     { to: '0x...', value: parseEther('0.1'), data: '0x' },
     *     { to: '0x...', value: 0n, data: '0x...' }
     * ])
     */
    async sendTransactions(calls: Call[]): Promise<Hash> {
        const userOpHash = await this.smartAccountClient.sendUserOperation({
            userOperation: {
                callData: await this.safeAccount.encodeCallData(calls)
            }
        })

        console.log(`UserOperation 已提交: ${userOpHash}`)
        console.log(`查看详情: https://jiffyscan.xyz/userOpHash/${userOpHash}?network=sepolia`)

        // 等待交易确认
        const receipt = await this.smartAccountClient.waitForUserOperationReceipt({
            hash: userOpHash
        })

        console.log(`交易已确认: ${receipt.receipt.transactionHash}`)

        return receipt.receipt.transactionHash
    }

    /**
     * 发送 ETH
     *
     * @example
     * const txHash = await safe.sendETH(
     *     '0x...',
     *     parseEther('0.1')
     * )
     */
    async sendETH(to: Address, value: bigint): Promise<Hash> {
        return await this.sendTransaction({
            to,
            value,
            data: '0x'
        })
    }

    /**
     * 调用合约（写操作）
     *
     * @example
     * const txHash = await safe.writeContract({
     *     to: erc20Address,
     *     data: encodeFunctionData({
     *         abi: erc20Abi,
     *         functionName: 'transfer',
     *         args: [recipient, amount]
     *     })
     * })
     */
    async writeContract(params: {
        to: Address
        data: `0x${string}`
        value?: bigint
    }): Promise<Hash> {
        return await this.sendTransaction({
            to: params.to,
            value: params.value ?? 0n,
            data: params.data
        })
    }

    // ==================== 高级操作 ====================

    /**
     * 部署 Safe（如果尚未部署）
     *
     * 注意：首次发送交易时会自动部署
     */
    async deploy(): Promise<void> {
        if (this.isDeployed()) {
            console.log('Safe 已部署')
            return
        }

        console.log('正在部署 Safe...')

        // 发送一个空交易来触发部署
        await this.sendTransaction({
            to: this.safeAddress,
            value: 0n,
            data: '0x'
        })

        // 刷新配置
        await this.refreshConfig()

        console.log('✅ Safe 已部署')
    }

    /**
     * 估算 UserOperation 的 Gas
     */
    async estimateGas(calls: Call[]): Promise<{
        preVerificationGas: bigint
        verificationGasLimit: bigint
        callGasLimit: bigint
    }> {
        const userOp = await this.smartAccountClient.prepareUserOperationRequest({
            userOperation: {
                callData: await this.safeAccount.encodeCallData(calls)
            }
        })

        return {
            preVerificationGas: userOp.preVerificationGas,
            verificationGasLimit: userOp.verificationGasLimit,
            callGasLimit: userOp.callGasLimit
        }
    }

    // ==================== 配置导出 ====================

    /**
     * 导出账户配置
     */
    async exportConfig(): Promise<SafeAccountConfig> {
        let owners: Address[] = []
        let threshold: number = 0

        if (this.isDeployed()) {
            owners = await this.getOwners()
            threshold = await this.getThreshold()
        }

        return {
            safeAddress: this.safeAddress,
            controllerAddress: this.controllerEOA.address,
            name: this.name,
            owners,
            threshold,
            chainId: this.chainId,
            isDeployed: this.isDeployed()
        }
    }

    // ==================== 获取底层客户端（高级用法） ====================

    /**
     * 获取 Smart Account Client
     * 用于高级操作
     */
    getSmartAccountClient(): SmartAccountClient{
        return this.smartAccountClient
    }

    /**
     * 获取 Safe Account
     * 用于高级操作
     */
    getSafeAccount(): ToSafeSmartAccountReturnType {
        return this.safeAccount
    }

    /**
     * 获取 Public Client
     * 用于读取链上数据
     */
    getPublicClient(): PublicClient {
        return this.publicClient
    }
}
