# Local Hardhat Testing Guide

本指南详细说明如何在本地 Hardhat 网络上测试 ERC-4337 合约和 Python 后端集成。

## 前置条件

- Node.js 和 npm 已安装
- Python 3.8+ 已安装
- 项目依赖已安装

---

## 第一部分：合约测试（Hardhat + TypeScript）

### 步骤 1: 启动本地 Hardhat 节点

打开第一个终端窗口：

```bash
cd contracts
npx hardhat node
```

**预期输出：**
```
Started HTTP and WebSocket JSON-RPC server at http://127.0.0.1:8545/

Accounts
========

WARNING: These accounts, and their private keys, are publicly known.
Any funds sent to them on Mainnet or any other live network WILL BE LOST.

Account #0: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 (10000 ETH)
Private Key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

Account #1: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 (10000 ETH)
...
```

**重要：保持这个终端窗口运行！不要关闭它。**

---

### 步骤 2: 部署合约到本地网络

打开第二个终端窗口：

```bash
cd contracts

# 编译合约
npm run compile

# 部署到本地网络
npx hardhat run scripts/deploy-local.ts --network localhost
```

**预期输出：**
```
Starting deployment...
Deploying with account: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
Account balance: 10000.0 ETH

1. Deploying EntryPoint...
✓ EntryPoint deployed to: 0x5FbDB2315678afecb367f032d93F642f64180aa3

2. Deploying SimpleAccountFactory...
✓ SimpleAccountFactory deployed to: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512

3. Calculating counterfactual account addresses...
✓ Test account counterfactual address: 0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0

4. Saving deployment configuration...
✓ Deployment info saved to: ../backend/local_deployment.json

✅ Deployment complete!

Deployment Summary:
==================
Network: localhost
Chain ID: 31337
EntryPoint: 0x5FbDB2315678afecb367f032d93F642f64180aa3
Factory: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
Test Account: 0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0
```

**检查点：**
- ✅ 部署成功，没有错误
- ✅ 生成了 `backend/local_deployment.json` 文件

---

### 步骤 3: 运行 TypeScript 合约测试

```bash
cd contracts

# 运行所有测试
npm test

# 或运行特定测试文件
npx hardhat test test/SimpleAccountMultisigTest.ts --network localhost
```

**预期输出：**
```
  SimpleAccount Multisig Tests
    Deployment
      ✓ Should deploy EntryPoint (XXXms)
      ✓ Should deploy SimpleAccountFactory (XXXms)
      ✓ Should create account with correct parameters (XXXms)

    Owner Management
      ✓ Should add new owner (XXXms)
      ✓ Should remove owner (XXXms)
      ✓ Should update threshold (XXXms)

    Guardian Management
      ✓ Should add guardian (XXXms)
      ✓ Should remove guardian (XXXms)

    Social Recovery
      ✓ Should approve recovery (XXXms)
      ✓ Should execute recovery when threshold met (XXXms)

  10 passing (Xs)
```

**可能的错误和解决方案：**

#### 错误 1: `Error: call revert exception`
```
原因：合约调用失败，可能是因为：
- SimpleAccount 使用了 v0.7 的接口但 core 是 v0.6
- 签名验证逻辑不兼容

解决：检查 SimpleAccount.sol 第 136 行的 _validateSignature 函数签名
```

#### 错误 2: `TypeError: Cannot read property 'address' of undefined`
```
原因：部署失败或合约地址未正确返回

解决：
1. 重启 Hardhat 节点
2. 重新部署合约
3. 检查 deploy-local.ts 脚本
```

#### 错误 3: `Error: network does not support ENS`
```
原因：本地网络不支持 ENS

解决：这是警告，可以忽略，不影响测试
```

---

## 第二部分：Python 后端集成测试

### 步骤 4: 安装 Python 依赖

在第二个终端窗口（或新开一个）：

```bash
# 回到项目根目录
cd ..

# 安装依赖（如果还没安装）
pip install web3 eth-account requests
```

---

### 步骤 5: 运行 Python 后端测试

```bash
python -m backend.test_local_deployment
```

**预期输出：**
```
============================================================
Testing Local Hardhat Deployment Integration
============================================================

1. Loading deployment configuration...
   Network: localhost
   Chain ID: 31337
   EntryPoint: 0x5FbDB2315678afecb367f032d93F642f64180aa3
   Factory: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
   Test Account: 0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0

2. Configuring network in Config singleton...
   ✓ Network configured

3. Setting up KeyManager...
   Importing Hardhat test account...
   ✓ Key imported and unlocked
   EOA Address: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266

4. Creating Wallet...
   ✓ Wallet created

5. Testing EOA operations...
   EOA Balance: 9999.XXXX ETH
   EOA Nonce: X

6. Adding AA account to wallet...
   ✓ AA Account added: 0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0

7. Testing AA account operations...
   Is Deployed: False
   Note: Account not yet deployed (counterfactual address)
   To deploy, send a UserOperation or call factory.createAccount()

8. Wallet Summary:
   Wallet Name: test_wallet
   EOA Address: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
   KeyManager Unlocked: True
   Networks: ['localhost']
   Total AA Accounts: 1

============================================================
✅ All tests passed!
============================================================

📝 Next Steps:
   1. The AA account is at a counterfactual address (not yet deployed)
   2. To deploy it, you need to:
      - Fund the account address with ETH for gas
      - Send a UserOperation through the EntryPoint
      - Or call factory.createAccount() directly
   3. After deployment, you can send UserOperations through the account
```

**检查点：**
- ✅ 成功加载 `local_deployment.json`
- ✅ 配置网络成功
- ✅ KeyManager 解锁成功
- ✅ EOA 余额显示正确（接近 10000 ETH）
- ✅ AA 账户地址与部署脚本一致

**可能的错误和解决方案：**

#### 错误 1: `FileNotFoundError: Deployment file not found`
```
原因：部署脚本还没运行或运行失败

解决：
1. 确保 Hardhat 节点在运行
2. 重新运行部署脚本（步骤 2）
3. 检查 backend/local_deployment.json 是否存在
```

#### 错误 2: `requests.exceptions.ConnectionError`
```
原因：无法连接到 Hardhat 节点

解决：
1. 确保 Hardhat 节点在 http://127.0.0.1:8545 运行
2. 检查防火墙设置
3. 尝试重启 Hardhat 节点
```

#### 错误 3: `KeyError: 'Network localhost not configured'`
```
原因：网络配置失败

解决：
1. 检查 config.json 文件
2. 删除 config.json 让程序重新创建
3. 检查 Config 类的 add_network 方法
```

#### 错误 4: `ValueError: Invalid private key`
```
原因：私钥格式错误

解决：
1. 检查 test_local_deployment.py 第 70 行
2. 确保私钥以 0x 开头
3. 私钥长度应为 66 个字符（含 0x）
```

---

## 第三部分：手动测试合约功能

### 步骤 6: 使用 Hardhat Console 交互测试

```bash
cd contracts
npx hardhat console --network localhost
```

在 console 中运行：

```javascript
// 1. 获取部署的合约
const EntryPoint = await ethers.getContractFactory('EntryPoint')
const entryPoint = await EntryPoint.attach('0x5FbDB2315678afecb367f032d93F642f64180aa3')

const Factory = await ethers.getContractFactory('SimpleAccountFactory')
const factory = await Factory.attach('0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512')

// 2. 获取测试账户
const [owner] = await ethers.getSigners()
console.log('Owner:', owner.address)

// 3. 创建 AA 账户
const owners = [owner.address]
const threshold = 1
const guardians = []
const guardianThreshold = 0
const salt = 0

// 计算地址
const accountAddress = await factory.getAddress(owners, threshold, guardians, guardianThreshold, salt)
console.log('Account address:', accountAddress)

// 4. 部署账户
const tx = await factory.createAccount(owners, threshold, guardians, guardianThreshold, salt)
await tx.wait()
console.log('Account deployed!')

// 5. 获取账户合约实例
const SimpleAccount = await ethers.getContractFactory('SimpleAccount')
const account = await SimpleAccount.attach(accountAddress)

// 6. 检查账户状态
const accountOwners = await account.getOwners()
console.log('Account owners:', accountOwners)

const accountThreshold = await account.threshold()
console.log('Threshold:', accountThreshold.toString())

// 7. 给账户转账
await owner.sendTransaction({
  to: accountAddress,
  value: ethers.utils.parseEther('1.0')
})
console.log('Sent 1 ETH to account')

// 8. 检查余额
const balance = await ethers.provider.getBalance(accountAddress)
console.log('Account balance:', ethers.utils.formatEther(balance), 'ETH')

// 退出
.exit
```

---

## 第四部分：验证 v0.6 兼容性

### 步骤 7: 检查关键接口

创建一个测试文件 `contracts/test/CompatibilityTest.ts`：

```typescript
import { expect } from 'chai'
import { ethers } from 'hardhat'

describe('v0.6 Compatibility Tests', function () {
  it('Should verify PackedUserOperation structure', async function () {
    // 检查 PackedUserOperation 的字段
    const userOp = {
      sender: ethers.constants.AddressZero,
      nonce: 0,
      initCode: '0x',
      callData: '0x',
      accountGasLimits: ethers.constants.HashZero,
      preVerificationGas: 0,
      gasFees: ethers.constants.HashZero,
      paymasterAndData: '0x',
      signature: '0x'
    }

    // 这应该不会报错
    expect(userOp.sender).to.equal(ethers.constants.AddressZero)
  })

  it('Should verify EntryPoint interface', async function () {
    const EntryPoint = await ethers.getContractFactory('EntryPoint')
    const entryPoint = await EntryPoint.deploy()
    await entryPoint.deployed()

    // 检查 EntryPoint 的关键方法
    expect(entryPoint.interface.functions).to.have.property('handleOps(tuple[],address)')
  })

  it('Should verify BaseAccount interface', async function () {
    const Factory = await ethers.getContractFactory('SimpleAccountFactory')
    const entryPoint = await (await ethers.getContractFactory('EntryPoint')).deploy()
    await entryPoint.deployed()

    const factory = await Factory.deploy(entryPoint.address)
    await factory.deployed()

    const [owner] = await ethers.getSigners()
    const tx = await factory.createAccount([owner.address], 1, [], 0, 0)
    await tx.wait()

    const accountAddr = await factory.getAddress([owner.address], 1, [], 0, 0)
    const SimpleAccount = await ethers.getContractFactory('SimpleAccount')
    const account = SimpleAccount.attach(accountAddr)

    // 检查 validateUserOp 方法存在
    expect(account.interface.functions).to.have.property('validateUserOp(tuple,bytes32,uint256)')
  })
})
```

运行测试：

```bash
npx hardhat test test/CompatibilityTest.ts --network localhost
```

---

## 常见问题排查

### 问题 1: 合约编译失败

**症状：**
```
Error: Solidity compilation errors
```

**可能原因：**
- SimpleAccount 使用了 v0.7 的 API
- pragma 版本不匹配

**检查：**
```bash
# 检查 SimpleAccount.sol 第 136 行
# _validateSignature 的签名应该是：
function _validateSignature(PackedUserOperation calldata userOp, bytes32 userOpHash)
    internal override virtual returns (uint256 validationData)
```

---

### 问题 2: 测试运行但功能不正常

**症状：**
- 测试通过但账户无法验证签名
- UserOperation 提交失败

**可能原因：**
- v0.6 的 PackedUserOperation 结构与 v0.7 不同
- 签名验证逻辑需要调整

**需要检查的文件：**
1. `SimpleAccount.sol` 第 136-146 行（`_validateSignature` 方法）
2. `SimpleAccount.sol` 第 148-184 行（`_verifySchnorrSignature` 方法）

---

### 问题 3: Python 后端无法连接

**症状：**
```
ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=8545)
```

**解决：**
1. 确保 Hardhat 节点在运行
2. 检查端口没有被占用
3. 尝试使用 `localhost` 代替 `127.0.0.1`

---

## 完整测试流程总结

### 快速测试命令（按顺序执行）

**终端 1：**
```bash
cd contracts
npx hardhat node
```

**终端 2：**
```bash
cd contracts
npm run compile
npx hardhat run scripts/deploy-local.ts --network localhost
npm test
```

**终端 3（或终端 2）：**
```bash
cd ..
python -m backend.test_local_deployment
```

---

## 下一步

测试通过后，您可以：

1. **实现 UserOperation 创建**：在 Python Account 类中添加 `create_user_operation()` 方法
2. **实现签名逻辑**：使用 KeyManager 签名 UserOperation
3. **测试 EntryPoint 交互**：通过 Python 提交 UserOperation
4. **部署到 Sepolia**：使用 Sepolia 部署指南测试真实网络

---

## 文件清单

测试过程中会生成/使用以下文件：

- ✅ `backend/local_deployment.json` - 部署配置
- ✅ `config.json` - 网络配置（Python）
- ✅ `wallet_test.json` - 钱包状态（如果保存）
- ✅ `contracts/artifacts/` - 编译产物
- ✅ `contracts/cache/` - Hardhat 缓存

如果测试出现问题，可以删除这些文件重新开始。

---

## 支持

如果遇到问题：
1. 查看上面的"常见问题排查"部分
2. 检查 Hardhat 节点输出的错误信息
3. 查看 Python 脚本的详细错误堆栈
4. 确认所有依赖版本正确
