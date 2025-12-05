import { expect } from 'chai'
import { ethers } from 'hardhat'
import { SimpleAccountFactory, SimpleAccount, EntryPoint } from '../typechain-types'
import { SignerWithAddress } from '@nomiclabs/hardhat-ethers/signers'

describe('SimpleAccount MultiSig', function () {
  let entryPoint: EntryPoint
  let factory: SimpleAccountFactory
  let owner1: SignerWithAddress
  let owner2: SignerWithAddress
  let owner3: SignerWithAddress
  let beneficiary: SignerWithAddress
  let guardian1: SignerWithAddress
  let guardian2: SignerWithAddress
  let guardian3: SignerWithAddress

  before(async function () {
    // 获取测试账户
    [owner1, owner2, owner3, beneficiary, guardian1, guardian2, guardian3] = await ethers.getSigners()

    console.log('\n=== 测试账户 ===')
    console.log('Owner1:', owner1.address)
    console.log('Owner2:', owner2.address)
    console.log('Owner3:', owner3.address)
    console.log('Beneficiary:', beneficiary.address)
    console.log('Guardian1:', guardian1.address)
    console.log('Guardian2:', guardian2.address)
    console.log('Guardian3:', guardian3.address)
  })

  beforeEach(async function () {
    // 部署 EntryPoint
    const EntryPoint = await ethers.getContractFactory('EntryPoint')
    entryPoint = await EntryPoint.deploy() as EntryPoint
    await entryPoint.deployed()

    console.log('\n=== 部署的合约 ===')
    console.log('EntryPoint:', entryPoint.address)

    // 部署 SimpleAccountFactory
    const SimpleAccountFactory = await ethers.getContractFactory('SimpleAccountFactory')
    factory = await SimpleAccountFactory.deploy(entryPoint.address) as SimpleAccountFactory
    await factory.deployed()

    console.log('Factory:', factory.address)
    console.log('AccountImplementation:', await factory.accountImplementation())
  })

  describe('账户创建测试', function () {
    it('应该能计算账户地址（2-of-3 多签，带 guardians）', async function () {
      const signers = [owner1.address, owner2.address, owner3.address]
      const threshold = 2
      const guardians = [guardian1.address, guardian2.address]
      const guardianThreshold = 2
      const salt = 0

      const accountAddress = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)

      console.log('\n=== 计算的账户地址 ===')
      console.log('Account Address:', accountAddress)

      // 验证地址格式
      expect(accountAddress).to.be.properAddress
      console.log('✓ 地址格式验证通过')
    })

    it('应该能计算账户地址（无 guardians）', async function () {
      const signers = [owner1.address, owner2.address]
      const threshold = 2
      const guardians: string[] = []
      const guardianThreshold = 0
      const salt = 1

      const accountAddress = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)

      console.log('\n=== 无 Guardian 账户地址 ===')
      console.log('Account Address:', accountAddress)

      expect(accountAddress).to.be.properAddress
    })

    it('应该能创建账户并验证初始状态（带 guardians）', async function () {
      const signers = [owner1.address, owner2.address, owner3.address]
      const threshold = 2
      const guardians = [guardian1.address, guardian2.address, guardian3.address]
      const guardianThreshold = 2
      const salt = 2

      console.log('\n=== 创建账户 ===')
      console.log('Owners:', signers)
      console.log('Threshold:', threshold)
      console.log('Guardians:', guardians)
      console.log('Guardian Threshold:', guardianThreshold)

      // 1. 预计算地址
      const accountAddress = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)
      console.log('\n1. 预计算地址:', accountAddress)

      // 2. 向地址发送 ETH
      const fundAmount = ethers.utils.parseEther('1.0')
      await owner1.sendTransaction({
        to: accountAddress,
        value: fundAmount
      })
      console.log('\n2. 发送 1 ETH 到账户 ✓')

      // 3. 创建账户
      const tx = await factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      await tx.wait()
      console.log('\n3. 账户创建成功 ✓')

      // 4. 验证余额
      const balance = await ethers.provider.getBalance(accountAddress)
      console.log('   账户余额:', ethers.utils.formatEther(balance), 'ETH')
      expect(balance).to.equal(fundAmount)

      // 5. 验证账户状态
      const account = await ethers.getContractAt('SimpleAccount', accountAddress)

      const ownerList = await account.getOwners()
      expect(ownerList.length).to.equal(3)
      expect(ownerList).to.include(owner1.address)
      expect(ownerList).to.include(owner2.address)
      expect(ownerList).to.include(owner3.address)

      const accountThreshold = await account.threshold()
      expect(accountThreshold).to.equal(2)

      const guardianList = await account.getGuardians()
      expect(guardianList.length).to.equal(3)
      expect(guardianList).to.include(guardian1.address)

      const accountGuardianThreshold = await account.guardianThreshold()
      expect(accountGuardianThreshold).to.equal(2)

      console.log('\n4. 账户状态验证通过 ✓')

      // 6. 再次调用 getAddress 验证一致性
      const accountAddress2 = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)
      expect(accountAddress2).to.equal(accountAddress)
      console.log('\n5. 地址一致性验证通过 ✓')
    })

    it('应该能创建账户（无 guardians）', async function () {
      const signers = [owner1.address, owner2.address]
      const threshold = 2
      const guardians: string[] = []
      const guardianThreshold = 0
      const salt = 3

      const accountAddress = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)

      await factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)

      const account = await ethers.getContractAt('SimpleAccount', accountAddress)

      const guardianList = await account.getGuardians()
      expect(guardianList.length).to.equal(0)

      const accountGuardianThreshold = await account.guardianThreshold()
      expect(accountGuardianThreshold).to.equal(0)

      const isEnabled = await account.isSocialRecoveryEnabled()
      expect(isEnabled).to.be.false

      console.log('\n无 Guardian 账户创建成功 ✓')
    })
  })

  describe('多账户测试', function () {
    it('应该能创建多个不同的账户', async function () {
      const accounts = []

      // 创建 3 个不同的账户
      for (let i = 0; i < 3; i++) {
        const signers = [owner1.address, owner2.address]
        const threshold = 2
        const guardians = i === 0 ? [] : [guardian1.address, guardian2.address]
        const guardianThreshold = i === 0 ? 0 : 2
        const salt = i + 100

        const address = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)
        accounts.push(address)

        // 向每个账户发送不同金额
        await owner1.sendTransaction({
          to: address,
          value: ethers.utils.parseEther((i + 1).toString())
        })

        await factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      }

      console.log('\n=== 创建的账户列表 ===')
      for (let i = 0; i < accounts.length; i++) {
        const balance = await ethers.provider.getBalance(accounts[i])
        const account = await ethers.getContractAt('SimpleAccount', accounts[i])
        const guardians = await account.getGuardians()
        console.log(`账户 ${i}:`, accounts[i])
        console.log(`  余额: ${ethers.utils.formatEther(balance)} ETH`)
        console.log(`  Guardians: ${guardians.length}`)
      }

      // 验证所有地址都不同
      expect(accounts[0]).to.not.equal(accounts[1])
      expect(accounts[1]).to.not.equal(accounts[2])
      expect(accounts[0]).to.not.equal(accounts[2])
    })
  })

  describe('Owner 管理测试', function () {
    let account: SimpleAccount
    let accountAddress: string

    beforeEach(async function () {
      const signers = [owner1.address, owner2.address]
      const threshold = 2
      const guardians = [guardian1.address, guardian2.address, guardian3.address]
      const guardianThreshold = 2
      const salt = 789

      accountAddress = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)
      await factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      account = await ethers.getContractAt('SimpleAccount', accountAddress)
    })

    it('应该能添加新的 owner', async function () {
      const newOwner = ethers.Wallet.createRandom()

      const addOwnerData = account.interface.encodeFunctionData('addOwner', [newOwner.address])
      await account.connect(owner1).execute(accountAddress, 0, addOwnerData)

      const isOwner = await account.isOwner(newOwner.address)
      expect(isOwner).to.be.true

      const owners = await account.getOwners()
      expect(owners).to.include(newOwner.address)

      console.log('\n添加 Owner 成功 ✓')
      console.log('新 Owner:', newOwner.address)
    })

    it('应该能移除 owner', async function () {
      const newOwner = ethers.Wallet.createRandom()
      const addOwnerData = account.interface.encodeFunctionData('addOwner', [newOwner.address])
      await account.connect(owner1).execute(accountAddress, 0, addOwnerData)

      const removeOwnerData = account.interface.encodeFunctionData('removeOwner', [owner2.address])
      await account.connect(owner1).execute(accountAddress, 0, removeOwnerData)

      const isOwner = await account.isOwner(owner2.address)
      expect(isOwner).to.be.false

      console.log('\n移除 Owner 成功 ✓')
    })

    it('不应该允许移除会破坏阈值的 owner', async function () {
      const removeOwnerData = account.interface.encodeFunctionData('removeOwner', [owner2.address])

      await expect(
          account.connect(owner1).execute(accountAddress, 0, removeOwnerData)
      ).to.be.reverted

      console.log('\n正确阻止了破坏阈值的操作 ✓')
    })

    it('应该能更新整个 owner 列表', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwner3 = ethers.Wallet.createRandom()

      const newOwners = [newOwner1.address, newOwner2.address, newOwner3.address]
      const newThreshold = 2

      const updateData = account.interface.encodeFunctionData('updateOwners', [newOwners, newThreshold])
      await account.connect(owner1).execute(accountAddress, 0, updateData)

      const owners = await account.getOwners()
      expect(owners.length).to.equal(3)
      expect(owners).to.include(newOwner1.address)

      const threshold = await account.threshold()
      expect(threshold).to.equal(2)

      console.log('\n更新 Owner 列表成功 ✓')
      console.log('新 Owners:', newOwners)
      console.log('新 Threshold:', newThreshold)
    })

    it('应该能添加单个 owner 并验证', async function () {
      const newOwner = ethers.Wallet.createRandom()

      const beforeCount = (await account.getOwners()).length

      const addOwnerData = account.interface.encodeFunctionData('addOwner', [newOwner.address])
      await account.connect(owner1).execute(accountAddress, 0, addOwnerData)

      const afterCount = (await account.getOwners()).length
      expect(afterCount).to.equal(beforeCount + 1)

      console.log('\nOwner 数量从', beforeCount, '增加到', afterCount, '✓')
    })
  })

  describe('Guardian 管理测试', function () {
    let account: SimpleAccount
    let accountAddress: string

    beforeEach(async function () {
      const signers = [owner1.address, owner2.address]
      const threshold = 2
      const guardians = [guardian1.address, guardian2.address]
      const guardianThreshold = 2
      const salt = 890

      accountAddress = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)
      await factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      account = await ethers.getContractAt('SimpleAccount', accountAddress)
    })

    it('应该能添加新的 guardian', async function () {
      const newGuardian = ethers.Wallet.createRandom()

      const addGuardianData = account.interface.encodeFunctionData('addGuardian', [newGuardian.address])
      await account.connect(owner1).execute(accountAddress, 0, addGuardianData)

      const isGuardian = await account.isGuardian(newGuardian.address)
      expect(isGuardian).to.be.true

      const guardians = await account.getGuardians()
      expect(guardians).to.include(newGuardian.address)

      console.log('\n添加 Guardian 成功 ✓')
      console.log('新 Guardian:', newGuardian.address)
    })

    it('应该能移除 guardian', async function () {
      const removeGuardianData = account.interface.encodeFunctionData('removeGuardian', [guardian2.address])
      await account.connect(owner1).execute(accountAddress, 0, removeGuardianData)

      const isGuardian = await account.isGuardian(guardian2.address)
      expect(isGuardian).to.be.false

      console.log('\n移除 Guardian 成功 ✓')
    })

    it('应该能更新整个 guardian 列表', async function () {
      const newGuardian1 = ethers.Wallet.createRandom()
      const newGuardian2 = ethers.Wallet.createRandom()
      const newGuardian3 = ethers.Wallet.createRandom()

      const newGuardians = [newGuardian1.address, newGuardian2.address, newGuardian3.address]
      const newThreshold = 2

      const updateData = account.interface.encodeFunctionData('updateGuardians', [newGuardians, newThreshold])
      await account.connect(owner1).execute(accountAddress, 0, updateData)

      const guardians = await account.getGuardians()
      expect(guardians.length).to.equal(3)
      expect(guardians).to.include(newGuardian1.address)

      const guardianThreshold = await account.guardianThreshold()
      expect(guardianThreshold).to.equal(2)

      console.log('\n更新 Guardian 列表成功 ✓')
      console.log('新 Guardians:', newGuardians)
    })

    it('应该能禁用社交恢复（设置空 guardians）', async function () {
      const updateData = account.interface.encodeFunctionData('updateGuardians', [[], 0])
      await account.connect(owner1).execute(accountAddress, 0, updateData)

      const guardians = await account.getGuardians()
      expect(guardians.length).to.equal(0)

      const isEnabled = await account.isSocialRecoveryEnabled()
      expect(isEnabled).to.be.false

      console.log('\n禁用社交恢复成功 ✓')
    })

    it('移除所有 guardians 后阈值应该为 0', async function () {
      const removeGuardian1Data = account.interface.encodeFunctionData('removeGuardian', [guardian1.address])
      await account.connect(owner1).execute(accountAddress, 0, removeGuardian1Data)

      const removeGuardian2Data = account.interface.encodeFunctionData('removeGuardian', [guardian2.address])
      await account.connect(owner1).execute(accountAddress, 0, removeGuardian2Data)

      const guardianThreshold = await account.guardianThreshold()
      expect(guardianThreshold).to.equal(0)

      const guardians = await account.getGuardians()
      expect(guardians.length).to.equal(0)

      console.log('\n移除所有 Guardians 后阈值正确设为 0 ✓')
    })
  })

  describe('社交恢复测试', function () {
    let account: SimpleAccount
    let accountAddress: string

    beforeEach(async function () {
      const signers = [owner1.address, owner2.address]
      const threshold = 2
      const guardians = [guardian1.address, guardian2.address, guardian3.address]
      const guardianThreshold = 2
      const salt = 901

      accountAddress = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)
      await factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      account = await ethers.getContractAt('SimpleAccount', accountAddress)
    })

    it('guardian 应该能批准恢复请求', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwners = [newOwner1.address, newOwner2.address]
      const newThreshold = 2

      await account.connect(guardian1).approveRecovery(newOwners, newThreshold)

      const hasApproved = await account.hasApprovedRecovery(guardian1.address, newOwners, newThreshold)
      expect(hasApproved).to.be.true

      const approvalCount = await account.getRecoveryApprovalCount(newOwners, newThreshold)
      expect(approvalCount).to.equal(1)

      console.log('\nGuardian 批准恢复成功 ✓')
      console.log('批准数量:', approvalCount.toString())
    })

    it('多个 guardians 批准后应该能执行恢复', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwners = [newOwner1.address, newOwner2.address]
      const newThreshold = 1

      console.log('\n=== 执行社交恢复 ===')
      console.log('原 Owners:', [owner1.address, owner2.address])
      console.log('新 Owners:', newOwners)

      await account.connect(guardian1).approveRecovery(newOwners, newThreshold)
      console.log('Guardian1 批准 ✓')

      await account.connect(guardian2).approveRecovery(newOwners, newThreshold)
      console.log('Guardian2 批准 ✓')

      const approvalCount = await account.getRecoveryApprovalCount(newOwners, newThreshold)
      expect(approvalCount).to.equal(2)
      console.log('批准数量:', approvalCount.toString())

      await account.connect(guardian1).executeRecovery(newOwners, newThreshold)
      console.log('执行恢复 ✓')

      const owners = await account.getOwners()
      expect(owners).to.include(newOwner1.address)
      expect(owners).to.include(newOwner2.address)

      const threshold = await account.threshold()
      expect(threshold).to.equal(1)

      const isOwner1 = await account.isOwner(owner1.address)
      expect(isOwner1).to.be.false

      console.log('恢复成功，旧 Owners 已失效 ✓')
    })

    it('批准数量不足时不应该能执行恢复', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwners = [newOwner1.address, newOwner2.address]
      const newThreshold = 2

      await account.connect(guardian1).approveRecovery(newOwners, newThreshold)

      await expect(
          account.connect(guardian1).executeRecovery(newOwners, newThreshold)
      ).to.be.revertedWith('insufficient guardian approvals')

      console.log('\n正确阻止了批准数量不足的恢复 ✓')
    })

    it('非 guardian 不应该能批准恢复', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwners = [newOwner1.address, newOwner2.address]
      const newThreshold = 2

      await expect(
          account.connect(beneficiary).approveRecovery(newOwners, newThreshold)
      ).to.be.revertedWith('not a guardian')

      console.log('\n正确阻止了非 Guardian 的批准 ✓')
    })

    it('guardian 应该能撤销批准', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwners = [newOwner1.address, newOwner2.address]
      const newThreshold = 2

      await account.connect(guardian1).approveRecovery(newOwners, newThreshold)

      let approvalCount = await account.getRecoveryApprovalCount(newOwners, newThreshold)
      expect(approvalCount).to.equal(1)
      console.log('\n批准后数量:', approvalCount.toString())

      await account.connect(guardian1).revokeRecoveryApproval(newOwners, newThreshold)

      approvalCount = await account.getRecoveryApprovalCount(newOwners, newThreshold)
      expect(approvalCount).to.equal(0)
      console.log('撤销后数量:', approvalCount.toString())

      const hasApproved = await account.hasApprovedRecovery(guardian1.address, newOwners, newThreshold)
      expect(hasApproved).to.be.false

      console.log('撤销批准成功 ✓')
    })

    it('guardian 不应该能重复批准同一个恢复请求', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwners = [newOwner1.address, newOwner2.address]
      const newThreshold = 2

      await account.connect(guardian1).approveRecovery(newOwners, newThreshold)

      await expect(
          account.connect(guardian1).approveRecovery(newOwners, newThreshold)
      ).to.be.revertedWith('already approved')

      console.log('\n正确阻止了重复批准 ✓')
    })

    it('执行恢复后应该清除批准记录', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwners = [newOwner1.address, newOwner2.address]
      const newThreshold = 1

      await account.connect(guardian1).approveRecovery(newOwners, newThreshold)
      await account.connect(guardian2).approveRecovery(newOwners, newThreshold)
      await account.connect(guardian1).executeRecovery(newOwners, newThreshold)

      const approvalCount = await account.getRecoveryApprovalCount(newOwners, newThreshold)
      expect(approvalCount).to.equal(0)

      const hasApproved1 = await account.hasApprovedRecovery(guardian1.address, newOwners, newThreshold)
      expect(hasApproved1).to.be.false

      const hasApproved2 = await account.hasApprovedRecovery(guardian2.address, newOwners, newThreshold)
      expect(hasApproved2).to.be.false

      console.log('\n恢复后批准记录已清除 ✓')
    })

    it('不同的恢复请求应该有独立的批准记录', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwner3 = ethers.Wallet.createRandom()

      const request1 = [newOwner1.address, newOwner2.address]
      const request2 = [newOwner2.address, newOwner3.address]

      await account.connect(guardian1).approveRecovery(request1, 2)
      await account.connect(guardian2).approveRecovery(request2, 2)

      const count1 = await account.getRecoveryApprovalCount(request1, 2)
      const count2 = await account.getRecoveryApprovalCount(request2, 2)

      expect(count1).to.equal(1)
      expect(count2).to.equal(1)

      console.log('\n不同恢复请求的批准记录独立 ✓')
    })
  })

  describe('无 Guardian 账户测试', function () {
    let account: SimpleAccount
    let accountAddress: string

    beforeEach(async function () {
      const signers = [owner1.address, owner2.address]
      const threshold = 2
      const guardians: string[] = []
      const guardianThreshold = 0
      const salt = 1012

      accountAddress = await factory.getAddress(signers, threshold, guardians, guardianThreshold, salt)
      await factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      account = await ethers.getContractAt('SimpleAccount', accountAddress)
    })

    it('应该能创建没有 guardians 的账户', async function () {
      const guardians = await account.getGuardians()
      expect(guardians.length).to.equal(0)

      const guardianThreshold = await account.guardianThreshold()
      expect(guardianThreshold).to.equal(0)

      const isEnabled = await account.isSocialRecoveryEnabled()
      expect(isEnabled).to.be.false

      console.log('\n创建无 Guardian 账户成功 ✓')
    })

    it('没有 guardians 时不应该能执行社交恢复', async function () {
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwners = [newOwner1.address, newOwner2.address]
      const newThreshold = 2

      await expect(
          account.connect(guardian1).approveRecovery(newOwners, newThreshold)
      ).to.be.revertedWith('social recovery not enabled')

      console.log('\n正确阻止了无 Guardian 账户的恢复 ✓')
    })

    it('应该能后续添加 guardians 启用社交恢复', async function () {
      const newGuardians = [guardian1.address, guardian2.address]
      const newThreshold = 2

      const updateData = account.interface.encodeFunctionData('updateGuardians', [newGuardians, newThreshold])
      await account.connect(owner1).execute(accountAddress, 0, updateData)

      const isEnabled = await account.isSocialRecoveryEnabled()
      expect(isEnabled).to.be.true

      const guardians = await account.getGuardians()
      expect(guardians.length).to.equal(2)

      const guardianThreshold = await account.guardianThreshold()
      expect(guardianThreshold).to.equal(2)

      console.log('\n成功启用社交恢复 ✓')
      console.log('Guardians:', guardians)
    })

    it('启用社交恢复后应该能正常使用', async function () {
      // 先启用社交恢复
      const newGuardians = [guardian1.address, guardian2.address]
      const newThreshold = 2

      const updateData = account.interface.encodeFunctionData('updateGuardians', [newGuardians, newThreshold])
      await account.connect(owner1).execute(accountAddress, 0, updateData)

      // 测试恢复功能
      const newOwner1 = ethers.Wallet.createRandom()
      const newOwner2 = ethers.Wallet.createRandom()
      const newOwners = [newOwner1.address, newOwner2.address]
      const recoveryThreshold = 1

      await account.connect(guardian1).approveRecovery(newOwners, recoveryThreshold)
      await account.connect(guardian2).approveRecovery(newOwners, recoveryThreshold)

      const approvalCount = await account.getRecoveryApprovalCount(newOwners, recoveryThreshold)
      expect(approvalCount).to.equal(2)

      console.log('\n启用后社交恢复功能正常 ✓')
    })
  })

  describe('边界情况测试', function () {
    it('不应该允许创建没有 owners 的账户', async function () {
      const signers: string[] = []
      const threshold = 0
      const guardians = [guardian1.address]
      const guardianThreshold = 1
      const salt = 2000

      await expect(
          factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      ).to.be.reverted

      console.log('\n正确阻止了创建无 Owner 账户 ✓')
    })

    it('不应该允许阈值大于 owner 数量', async function () {
      const signers = [owner1.address, owner2.address]
      const threshold = 3
      const guardians = [guardian1.address]
      const guardianThreshold = 1
      const salt = 2001

      await expect(
          factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      ).to.be.reverted

      console.log('\n正确阻止了阈值大于 Owner 数量 ✓')
    })

    it('不应该允许 guardian 阈值大于 guardian 数量', async function () {
      const signers = [owner1.address, owner2.address]
      const threshold = 2
      const guardians = [guardian1.address, guardian2.address]
      const guardianThreshold = 3
      const salt = 2002

      await expect(
          factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      ).to.be.reverted

      console.log('\n正确阻止了 Guardian 阈值大于数量 ✓')
    })

    it('有 guardians 时阈值不能为 0', async function () {
      const signers = [owner1.address, owner2.address]
      const threshold = 2
      const guardians = [guardian1.address, guardian2.address]
      const guardianThreshold = 0
      const salt = 2003

      await expect(
          factory.createAccount(signers, threshold, guardians, guardianThreshold, salt)
      ).to.be.reverted

      console.log('\n正确阻止了 Guardian 阈值为 0 ✓')
    })
  })
})
