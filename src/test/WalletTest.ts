import { Wallet } from '../accounts/Wallet'
import type { Address } from 'viem'

const TEST_CONFIG = {
    CHAIN_ID: 11155111,
    RPC_URL: 'https://eth-sepolia.api.onfinality.io/public',
    BUNDLER_URL: 'https://api.pimlico.io/v2/11155111/rpc?apikey=pim_gdR7HaA5MpQ5PK3HMdSTkr',

    // 导入测试用
    EXISTING_PRIVATE_KEY: '0x0000000000000000000000000000000000000000000000000000000000000000' as `0x${string}`,
    EXISTING_MNEMONIC: 'thing scrap return craft extra indicate expand demise riot shallow night chest',  // 新增
    EXISTING_SAFE_ADDRESS: '0x8B13872725C881050Bf1311d2EA5DdD3616F661C' as Address,
}


// ==================== 测试 1：创建和导入钱包 ====================
async function test1_CreateAndImportWallet() {
    console.log('\n===== 测试 1：创建和导入钱包 =====\n')

    // 1.1 创建新钱包（生成助记词）
    console.log('1.1 创建新钱包（生成助记词）...')
    const wallet1 = new Wallet()
    console.log('✅ 控制者地址:', wallet1.controllerAddress)
    console.log('✅ 有助记词:', wallet1.hasMnemonic)

    // 1.2 导出助记词
    console.log('\n1.2 导出助记词...')
    const mnemonic = wallet1.exportMnemonic()
    console.log('✅ 助记词:', mnemonic)

    // 1.3 导出私钥
    console.log('\n1.3 导出私钥...')
    const privateKey = wallet1.exportPrivateKey()
    console.log('✅ 私钥:', privateKey)

    // 1.4 使用助记词恢复钱包
    console.log('\n1.4 使用助记词恢复钱包...')
    const wallet2 = new Wallet({ mnemonic })
    console.log('✅ 恢复后的地址:', wallet2.controllerAddress)
    console.log('✅ 地址匹配:', wallet1.controllerAddress === wallet2.controllerAddress)
    console.log('✅ 有助记词:', wallet2.hasMnemonic)

    // 1.5 使用私钥恢复钱包
    console.log('\n1.5 使用私钥恢复钱包...')
    const wallet3 = new Wallet({ privateKey })
    console.log('✅ 恢复后的地址:', wallet3.controllerAddress)
    console.log('✅ 地址匹配:', wallet1.controllerAddress === wallet3.controllerAddress)
    console.log('✅ 有助记词:', wallet3.hasMnemonic)  // 应该是 false

    // 1.6 测试错误：同时提供私钥和助记词
    console.log('\n1.6 测试错误处理...')
    try {
        new Wallet({ privateKey, mnemonic })
        console.log('❌ 应该抛出错误')
    } catch (error) {
        console.log('✅ 正确抛出错误:', (error as Error).message)
    }

    console.log('\n✅ 测试 1 通过\n')
    return wallet1
}
// ==================== 测试 1.5：助记词功能 ====================
async function test1_5_MnemonicFeatures() {
    console.log('\n===== 测试 1.5：助记词功能 =====\n')

    // 1. 创建新钱包（自动生成助记词）
    console.log('1.1 创建新钱包（自动生成助记词）...')
    const wallet1 = new Wallet()
    const mnemonic1 = wallet1.exportMnemonic()
    console.log('✅ 助记词:', mnemonic1)
    console.log('✅ 单词数量:', mnemonic1.split(' ').length)

    // 2. 从助记词恢复
    console.log('\n1.2 从助记词恢复...')
    const wallet2 = new Wallet({ mnemonic: mnemonic1 })
    console.log('✅ 地址匹配:', wallet1.controllerAddress === wallet2.controllerAddress)
    console.log('✅ 私钥匹配:', wallet1.exportPrivateKey() === wallet2.exportPrivateKey())

    // 3. 从私钥导入（没有助记词）
    console.log('\n1.3 从私钥导入（没有助记词）...')
    const privateKey = wallet1.exportPrivateKey()
    const wallet3 = new Wallet({ privateKey })
    console.log('✅ 地址匹配:', wallet1.controllerAddress === wallet3.controllerAddress)
    console.log('✅ 有助记词:', wallet3.hasMnemonic)

    // 4. 尝试导出不存在的助记词
    console.log('\n1.4 尝试导出不存在的助记词...')
    try {
        wallet3.exportMnemonic()
        console.log('❌ 应该抛出错误')
    } catch (error) {
        console.log('✅ 正确抛出错误:', (error as Error).message)
    }

    // 5. 使用标准测试助记词
    console.log('\n1.5 使用标准测试助记词...')
    const testMnemonic = 'test test test test test test test test test test test junk'
    const wallet4 = new Wallet({ mnemonic: testMnemonic })
    console.log('✅ 测试钱包地址:', wallet4.controllerAddress)
    // 已知地址: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
    console.log('✅ 地址正确:', wallet4.controllerAddress === '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266')

    console.log('\n✅ 测试 1.5 通过\n')
}


// ==================== 测试 2：创建 Safe 账户 ====================
async function test2_CreateSafeAccounts() {
    console.log('\n===== 测试 2：创建 Safe 账户 =====\n')

    const wallet = new Wallet()
    console.log('控制者地址:', wallet.controllerAddress)

    // 2.1 创建单签 Safe
    console.log('\n2.1 创建单签 Safe...')
    console.log('控制者地址:', wallet.controllerAddress)
    const safe1 = await wallet.createSafeAccount(
        {
            owners: [wallet.getControllerAccount()],
            threshold: 1,
            bundlerUrl: TEST_CONFIG.BUNDLER_URL,
            rpcUrl: TEST_CONFIG.RPC_URL,
            chainId: TEST_CONFIG.CHAIN_ID,
        },
        '我的主钱包'
    )

    console.log('✅ Safe 地址:', safe1.safeAddress)
    console.log('✅ 名称:', safe1.name)
    console.log('✅ Owners:', await safe1.getOwners())
    console.log('✅ Threshold:', await safe1.getThreshold())

    // 2.2 创建第二个 Safe
    console.log('\n2.2 创建第二个 Safe...')
    const safe2 = await wallet.createSafeAccount(
        {
            owners: [wallet.getControllerAccount()],
            threshold: 1,
            bundlerUrl: TEST_CONFIG.BUNDLER_URL,
            rpcUrl: TEST_CONFIG.RPC_URL,
            chainId: TEST_CONFIG.CHAIN_ID,
        },
        '备用钱包'
    )

    console.log('✅ Safe 地址:', safe2.safeAddress)

    // 2.3 查看钱包摘要
    console.log('\n2.3 钱包摘要...')
    const summary = await wallet.getSummary()
    console.log('✅ Safe 数量:', summary.aaAccountCount)

    console.log('\n✅ 测试 2 通过\n')
    return { wallet, safe1, safe2 }
}

// ==================== 测试 3：导入已存在的 Safe ====================
async function test3_ImportExistingSafe() {
    console.log('\n===== 测试 3：导入已存在的 Safe =====\n')

    console.log('⚠️  需要替换 TEST_CONFIG 中的：')
    console.log('    - EXISTING_PRIVATE_KEY 或 EXISTING_MNEMONIC')
    console.log('    - EXISTING_SAFE_ADDRESS')
    console.log('')

    // 优先使用助记词，否则使用私钥
    const wallet = TEST_CONFIG.EXISTING_MNEMONIC !== 'test test test test test test test test test test test junk'
        ? new Wallet({ mnemonic: TEST_CONFIG.EXISTING_MNEMONIC })
        : new Wallet({ privateKey: TEST_CONFIG.EXISTING_PRIVATE_KEY })

    console.log('控制者地址:', wallet.controllerAddress)
    console.log('有助记词:', wallet.hasMnemonic)

    const importedSafe = await wallet.createSafeAccount(
        {
            safeAddress: TEST_CONFIG.EXISTING_SAFE_ADDRESS,
            bundlerUrl: TEST_CONFIG.BUNDLER_URL,
            rpcUrl: TEST_CONFIG.RPC_URL,
            chainId: TEST_CONFIG.CHAIN_ID,
        },
        '导入的 Safe'
    )

    console.log('✅ Safe 地址:', importedSafe.safeAddress)
    console.log('✅ Owners:', await importedSafe.getOwners())
    console.log('✅ Threshold:', await importedSafe.getThreshold())

    console.log('\n✅ 测试 3 通过\n')
}


// ==================== 测试 4：Safe 查询和管理 ====================
async function test4_SafeManagement() {
    console.log('\n===== 测试 4：Safe 查询和管理 =====\n')

    const wallet = new Wallet()

    // 创建多个 Safe
    const safe1 = await wallet.createSafeAccount(
        {
            owners: [wallet.getControllerAccount()],
            threshold: 1,
            bundlerUrl: TEST_CONFIG.BUNDLER_URL,
            rpcUrl: TEST_CONFIG.RPC_URL,
            chainId: TEST_CONFIG.CHAIN_ID,
        },
        'Safe-1'
    )

    const safe2 = await wallet.createSafeAccount(
        {
            owners: [wallet.getControllerAccount()],
            threshold: 1,
            bundlerUrl: TEST_CONFIG.BUNDLER_URL,
            rpcUrl: TEST_CONFIG.RPC_URL,
            chainId: TEST_CONFIG.CHAIN_ID,
        },
        'Safe-2'
    )

    // 4.1 通过地址查询
    console.log('4.1 通过地址查询...')
    const found = wallet.getSafeAccount(safe1.safeAddress)
    console.log('✅ 找到:', found?.name)

    // 4.2 通过名称查询
    console.log('\n4.2 通过名称查询...')
    const foundByName = wallet.getSafeAccountByName('Safe-2')
    console.log('✅ 找到:', foundByName?.safeAddress)

    // 4.3 更新名称
    console.log('\n4.3 更新名称...')
    wallet.updateSafeAccountName(safe1.safeAddress, '新名称')
    console.log('✅ 新名称:', wallet.getSafeAccount(safe1.safeAddress)?.name)

    // 4.4 删除 Safe
    console.log('\n4.4 删除 Safe...')
    const removed = wallet.removeSafeAccount(safe2.safeAddress)
    console.log('✅ 删除成功:', removed)
    console.log('✅ 剩余数量:', wallet.safeAccounts.length)

    console.log('\n✅ 测试 4 通过\n')
}
// ==================== 测试 6：打印钱包信息 ====================
async function test6_PrintWalletInfo() {
    console.log('\n===== 测试 6：打印钱包信息 =====\n')

    // 测试有助记词的钱包
    console.log('6.1 有助记词的钱包:')
    const wallet1 = new Wallet()

    await wallet1.createSafeAccount(
        {
            owners: [wallet1.getControllerAccount()],
            threshold: 1,
            bundlerUrl: TEST_CONFIG.BUNDLER_URL,
            rpcUrl: TEST_CONFIG.RPC_URL,
            chainId: TEST_CONFIG.CHAIN_ID,
        },
        '钱包 A'
    )

    await wallet1.printInfo()

    // 测试只有私钥的钱包
    console.log('\n6.2 只有私钥的钱包:')
    const wallet2 = new Wallet({ privateKey: wallet1.exportPrivateKey() })

    await wallet2.createSafeAccount(
        {
            owners: [wallet2.getControllerAccount()],
            threshold: 1,
            bundlerUrl: TEST_CONFIG.BUNDLER_URL,
            rpcUrl: TEST_CONFIG.RPC_URL,
            chainId: TEST_CONFIG.CHAIN_ID,
        },
        '钱包 B'
    )

    await wallet2.printInfo()

    console.log('✅ 测试 6 通过\n')
}


// ==================== 主测试函数 ====================
async function runAllTests() {
    console.log('\n╔════════════════════════════════════════╗')
    console.log('║     Wallet 测试套件 (支持助记词)       ║')
    console.log('╚════════════════════════════════════════╝')

    try {
        await test1_CreateAndImportWallet()
        await test1_5_MnemonicFeatures()  // 新增
        await test2_CreateSafeAccounts()
        await test3_ImportExistingSafe()  // 需要真实的 Safe 地址
        await test4_SafeManagement()
        await test6_PrintWalletInfo()

        console.log('\n✅ 所有测试通过！\n')
    } catch (error) {
        console.error('\n❌ 测试失败:', error)
        process.exit(1)
    }
}



runAllTests()

export {
    test1_CreateAndImportWallet,
    test1_5_MnemonicFeatures,  // 新增
    test2_CreateSafeAccounts,
    test3_ImportExistingSafe,
    test4_SafeManagement,
    runAllTests
}
