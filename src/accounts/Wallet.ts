import { generateMnemonic, mnemonicToSeedSync, validateMnemonic } from '@scure/bip39'
import { wordlist } from '@scure/bip39/wordlists/english'
import HDKey from 'hdkey'
import { privateKeyToAccount } from 'viem/accounts'
import type { Address } from 'viem'
import {
    BaseAccount,
    EOAAccount,
    AAAccount,
    Safe4337Config,
    AASignerInfo,
    SafeAccountInitOptions
} from './Account'

export const DERIVATION_PATHS = {
    EOA_BASE: "m/44'/60'/0'/0",
    AA_BASE: "m/44'/60'/1'/0",
} as const

export class Wallet {
    public mnemonic: string
    private hdKey: HDKey
    public eoaAccounts: EOAAccount[]
    public aaAccounts: AAAccount[]
    private nextEOAIndex: number = 0
    private nextAAIndex: number = 0

    constructor(mnemonic?: string) {
        if (mnemonic) {
            if (!validateMnemonic(mnemonic, wordlist)) {
                throw new Error('Invalid mnemonic phrase')
            }
            this.mnemonic = mnemonic
        } else {
            this.mnemonic = generateMnemonic(wordlist, 128)
        }

        const seed = mnemonicToSeedSync(this.mnemonic)
        this.hdKey = HDKey.fromMasterSeed(seed)

        this.eoaAccounts = []
        this.aaAccounts = []
    }

    private derivePrivateKey(path: string): `0x${string}` {
        const childKey = this.hdKey.derive(path)

        if (!childKey.privateKey) {
            throw new Error(`Failed to derive private key for path: ${path}`)
        }

        return `0x${childKey.privateKey.toString('hex')}`
    }

    private buildDerivationPath(base: string, index: number): string {
        return `${base}/${index}`
    }

    createEOAAccount(index?: number): EOAAccount {
        const accountIndex = index !== undefined ? index : this.nextEOAIndex
        const derivationPath = this.buildDerivationPath(DERIVATION_PATHS.EOA_BASE, accountIndex)

        const privateKey = this.derivePrivateKey(derivationPath)
        const eoaAccount = new EOAAccount(privateKey, derivationPath)

        this.eoaAccounts.push(eoaAccount)

        if (index === undefined) {
            this.nextEOAIndex++
        } else if (accountIndex >= this.nextEOAIndex) {
            this.nextEOAIndex = accountIndex + 1
        }

        return eoaAccount
    }

    /**
     * 创建新的 AA (Safe) 账户
     * 注意：这是一个异步方法，因为需要初始化 Safe4337Pack
     */
    async createAAAccount(
        config: Safe4337Config,
        index?: number
    ): Promise<AAAccount> {
        const accountIndex = index !== undefined ? index : this.nextAAIndex
        const derivationPath = this.buildDerivationPath(DERIVATION_PATHS.AA_BASE, accountIndex)

        // 派生签名者私钥
        const signerPrivateKey = this.derivePrivateKey(derivationPath)

        // 创建签名者账户
        const signerAccount = privateKeyToAccount(signerPrivateKey)

        // 构建签名者信息
        const signerInfo: AASignerInfo = {
            signerAddress: signerAccount.address,
            signerPrivateKey: signerPrivateKey,
            signerAccount: signerAccount,
            derivationPath: derivationPath
        }

        // 使用静态工厂方法创建 AA 账户（会自动初始化 Safe4337Pack）
        const aaAccount = await AAAccount.create(
            signerInfo,
            config
        )

        this.aaAccounts.push(aaAccount)

        // 更新索引
        if (index === undefined) {
            this.nextAAIndex++
        } else if (accountIndex >= this.nextAAIndex) {
            this.nextAAIndex = accountIndex + 1
        }

        return aaAccount
    }

    removeEOAAccount(address: Address): boolean {
        const index = this.eoaAccounts.findIndex(
            account => account.address.toLowerCase() === address.toLowerCase()
        )

        if (index === -1) return false

        this.eoaAccounts.splice(index, 1)
        return true
    }

    removeAAAccount(address: Address): boolean {
        const index = this.aaAccounts.findIndex(
            account => account.address.toLowerCase() === address.toLowerCase()
        )

        if (index === -1) return false

        this.aaAccounts.splice(index, 1)
        return true
    }

    getMnemonic(): string {
        return this.mnemonic
    }

    getEOAAccount(address: Address): EOAAccount | undefined {
        return this.eoaAccounts.find(
            account => account.address.toLowerCase() === address.toLowerCase()
        )
    }

    getAAAccount(address: Address): AAAccount | undefined {
        return this.aaAccounts.find(
            account => account.address.toLowerCase() === address.toLowerCase()
        )
    }

    getOrCreateEOAAccount(index: number): EOAAccount {
        const derivationPath = this.buildDerivationPath(DERIVATION_PATHS.EOA_BASE, index)
        const existing = this.eoaAccounts.find(acc => acc.derivationPath === derivationPath)

        if (existing) return existing

        return this.createEOAAccount(index)
    }

    getAllAccounts(): BaseAccount[] {
        return [...this.eoaAccounts, ...this.aaAccounts]
    }

    exportWalletInfo() {
        return {
            eoaCount: this.eoaAccounts.length,
            aaCount: this.aaAccounts.length,
            nextEOAIndex: this.nextEOAIndex,
            nextAAIndex: this.nextAAIndex,
            eoaAccounts: this.eoaAccounts.map(acc => ({
                address: acc.address,
                derivationPath: acc.derivationPath
            })),
            aaAccounts: this.aaAccounts.map(acc => acc.exportConfig())
        }
    }
}
