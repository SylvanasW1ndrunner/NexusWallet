// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/* solhint-disable avoid-low-level-calls */
/* solhint-disable no-inline-assembly */
/* solhint-disable reason-string */

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import "@openzeppelin/contracts/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts/proxy/utils/UUPSUpgradeable.sol";
import "../core/BaseAccount.sol";
import "../core/Helpers.sol";
import "./callback/TokenCallbackHandler.sol";

/**
  * minimal account with social recovery.
  *  this is sample minimal account.
  *  has execute, eth handling methods
  *  has a single signer that can send requests through the entryPoint.
  *  supports social recovery through guardians (optional).
  */
contract SimpleAccount is BaseAccount, TokenCallbackHandler, UUPSUpgradeable, Initializable {
    address[] public ownerlist;
    uint256 public threshold;
    address[] public guardians;
    uint256 public guardianThreshold;

    IEntryPoint private immutable _entryPoint;

    // 社交恢复相关的映射
    mapping(bytes32 => mapping(address => bool)) public recoveryApprovals; // recoveryHash => guardian => approved
    mapping(bytes32 => uint256) public recoveryApprovalCount; // recoveryHash => count

    event SimpleAccountInitialized(
        IEntryPoint indexed entryPoint,
        address[] owners,
        uint256 threshold,
        address[] guardians,
        uint256 guardianThreshold
    );

    event OwnersUpdated(address[] newOwners, uint256 newThreshold);
    event GuardiansUpdated(address[] newGuardians, uint256 newGuardianThreshold);
    event RecoveryApproved(bytes32 indexed recoveryHash, address indexed guardian, uint256 approvalCount);
    event RecoveryExecuted(bytes32 indexed recoveryHash, address[] newOwners, uint256 newThreshold);

    modifier onlyOwner() {
        _onlyOwner();
        _;
    }

    /// @inheritdoc BaseAccount
    function entryPoint() public view virtual override returns (IEntryPoint) {
        return _entryPoint;
    }

    // solhint-disable-next-line no-empty-blocks
    receive() external payable {}

    constructor(IEntryPoint anEntryPoint) {
        _entryPoint = anEntryPoint;
        _disableInitializers();
    }

    function isOwner(address account) public view returns (bool) {
        uint256 length = ownerlist.length;
        for (uint256 i = 0; i < length; i++) {
            if (account == ownerlist[i]) {
                return true;
            }
        }
        return false;
    }

    function isGuardian(address account) public view returns (bool) {
        uint256 length = guardians.length;
        for (uint256 i = 0; i < length; i++) {
            if (account == guardians[i]) {
                return true;
            }
        }
        return false;
    }

    function _onlyOwner() internal view {
        // Directly from EOA owner, or through the account itself (which gets redirected through execute())
        require(isOwner(msg.sender) || msg.sender == address(this), "only owner");
    }

    /**
     * @dev The _entryPoint member is immutable, to reduce gas consumption.  To upgrade EntryPoint,
     * a new implementation of SimpleAccount must be deployed with the new EntryPoint address, then upgrading
      * the implementation by calling `upgradeTo()`
     */
    function initialize(
        address[] memory _ownerlist,
        uint256 _threshold,
        address[] memory _guardians,
        uint256 _guardianThreshold
    ) public virtual initializer {
        _initialize(_ownerlist, _threshold, _guardians, _guardianThreshold);
    }

    function _initialize(
        address[] memory _ownerlist,
        uint256 _threshold,
        address[] memory _guardians,
        uint256 _guardianThreshold
    ) internal virtual {
        require(_ownerlist.length > 0, "owners required");
        require(_threshold > 0 && _threshold <= _ownerlist.length, "invalid threshold");

        // guardians 可以为空
        if (_guardians.length > 0) {
            require(_guardianThreshold > 0 && _guardianThreshold <= _guardians.length, "invalid guardian threshold");
        } else {
            // 如果没有 guardians，guardianThreshold 应该为 0
            require(_guardianThreshold == 0, "guardian threshold must be 0 when no guardians");
        }

        ownerlist = _ownerlist;
        threshold = _threshold;
        guardians = _guardians;
        guardianThreshold = _guardianThreshold;

        emit SimpleAccountInitialized(_entryPoint, _ownerlist, _threshold, _guardians, _guardianThreshold);
    }

    // Require the function call went through EntryPoint or owner
    function _requireForExecute() internal view override virtual {
        require(msg.sender == address(entryPoint()) || isOwner(msg.sender), "account: not Owner or EntryPoint");
    }

    /// implement template method of BaseAccount
    function _validateSignature(PackedUserOperation calldata userOp, bytes32 userOpHash)
    internal override virtual returns (uint256 validationData) {

        // 验证 Schnorr 签名
        // userOp.signature 应该包含聚合的 Schnorr 签名
        bool isValid = _verifySchnorrSignature(userOpHash, userOp.signature);

        if (!isValid)
            return SIG_VALIDATION_FAILED;
        return SIG_VALIDATION_SUCCESS;
    }

    function _verifySchnorrSignature(bytes32 message, bytes memory signature)
    internal view returns (bool) {

        // 签名格式: 多个 ECDSA 签名拼接
        // 每个签名 65 字节 (r: 32, s: 32, v: 1)

        require(signature.length % 65 == 0, "invalid signature length");

        uint256 signatureCount = signature.length / 65;
        require(signatureCount >= threshold, "insufficient signatures");

        uint256 validCount = 0;

        for (uint256 i = 0; i < signatureCount; i++) {
            bytes32 r;
            bytes32 s;
            uint8 v;

            assembly {
                let offset := add(signature, add(32, mul(i, 65)))
                r := mload(offset)
                s := mload(add(offset, 32))
                v := byte(0, mload(add(offset, 64)))
            }

            address recovered = ecrecover(message, v, r, s);

            for (uint256 j = 0; j < ownerlist.length; j++) {
                if (recovered == ownerlist[j]) {
                    validCount++;
                    break;
                }
            }
        }

        return validCount >= threshold;
    }

    // ============================================
    // Owner Management Functions (只有 owner 可调用)
    // ============================================

    /**
     * @notice 更新 owner 列表和阈值
     * @param newOwners 新的 owner 地址列表
     * @param newThreshold 新的签名阈值
     */
    function updateOwners(address[] memory newOwners, uint256 newThreshold) external onlyOwner {
        require(newOwners.length > 0, "owners required");
        require(newThreshold > 0 && newThreshold <= newOwners.length, "invalid threshold");

        ownerlist = newOwners;
        threshold = newThreshold;

        emit OwnersUpdated(newOwners, newThreshold);
    }

    /**
     * @notice 更新 guardian 列表和阈值
     * @param newGuardians 新的 guardian 地址列表
     * @param newGuardianThreshold 新的 guardian 阈值
     */
    function updateGuardians(address[] memory newGuardians, uint256 newGuardianThreshold) external onlyOwner {
        // guardians 可以为空（禁用社交恢复）
        if (newGuardians.length > 0) {
            require(newGuardianThreshold > 0 && newGuardianThreshold <= newGuardians.length, "invalid guardian threshold");
        } else {
            require(newGuardianThreshold == 0, "guardian threshold must be 0 when no guardians");
        }

        guardians = newGuardians;
        guardianThreshold = newGuardianThreshold;

        emit GuardiansUpdated(newGuardians, newGuardianThreshold);
    }

    /**
     * @notice 添加单个 owner
     * @param newOwner 新 owner 地址
     */
    function addOwner(address newOwner) external onlyOwner {
        require(newOwner != address(0), "invalid owner");
        require(!isOwner(newOwner), "already owner");

        ownerlist.push(newOwner);

        emit OwnersUpdated(ownerlist, threshold);
    }

    /**
     * @notice 移除单个 owner
     * @param ownerToRemove 要移除的 owner 地址
     */
    function removeOwner(address ownerToRemove) external onlyOwner {
        require(isOwner(ownerToRemove), "not an owner");
        require(ownerlist.length > threshold, "cannot remove: would break threshold");

        uint256 length = ownerlist.length;
        for (uint256 i = 0; i < length; i++) {
            if (ownerlist[i] == ownerToRemove) {
                ownerlist[i] = ownerlist[length - 1];
                ownerlist.pop();
                break;
            }
        }

        emit OwnersUpdated(ownerlist, threshold);
    }

    /**
     * @notice 添加单个 guardian
     * @param newGuardian 新 guardian 地址
     */
    function addGuardian(address newGuardian) external onlyOwner {
        require(newGuardian != address(0), "invalid guardian");
        require(!isGuardian(newGuardian), "already guardian");

        guardians.push(newGuardian);

        // 如果是第一个 guardian，设置阈值为 1
        if (guardianThreshold == 0) {
            guardianThreshold = 1;
        }

        emit GuardiansUpdated(guardians, guardianThreshold);
    }

    /**
     * @notice 移除单个 guardian
     * @param guardianToRemove 要移除的 guardian 地址
     */
    function removeGuardian(address guardianToRemove) external onlyOwner {
        require(isGuardian(guardianToRemove), "not a guardian");

        uint256 length = guardians.length;
        for (uint256 i = 0; i < length; i++) {
            if (guardians[i] == guardianToRemove) {
                guardians[i] = guardians[length - 1];
                guardians.pop();
                break;
            }
        }

        // 如果移除后没有 guardians 了，将阈值设为 0
        if (guardians.length == 0) {
            guardianThreshold = 0;
        } else if (guardianThreshold > guardians.length) {
            // 确保阈值不超过 guardian 数量
            guardianThreshold = guardians.length;
        }

        emit GuardiansUpdated(guardians, guardianThreshold);
    }

    // ============================================
    // Social Recovery Functions (guardian 可调用)
    // ============================================

    /**
     * @notice Guardian 批准社交恢复
     * @param newOwners 恢复后的新 owner 列表
     * @param newThreshold 恢复后的新阈值
     */
    function approveRecovery(address[] memory newOwners, uint256 newThreshold) external {
        require(guardians.length > 0, "social recovery not enabled");
        require(isGuardian(msg.sender), "not a guardian");
        require(newOwners.length > 0, "owners required");
        require(newThreshold > 0 && newThreshold <= newOwners.length, "invalid threshold");

        // 计算恢复请求的唯一哈希
        bytes32 recoveryHash = keccak256(abi.encodePacked(newOwners, newThreshold));

        // 检查是否已经批准过
        require(!recoveryApprovals[recoveryHash][msg.sender], "already approved");

        // 记录批准
        recoveryApprovals[recoveryHash][msg.sender] = true;
        recoveryApprovalCount[recoveryHash]++;

        emit RecoveryApproved(recoveryHash, msg.sender, recoveryApprovalCount[recoveryHash]);
    }

    /**
     * @notice 执行社交恢复（达到阈值后任何人都可以调用）
     * @param newOwners 恢复后的新 owner 列表
     * @param newThreshold 恢复后的新阈值
     */
    function executeRecovery(address[] memory newOwners, uint256 newThreshold) external {
        require(guardians.length > 0, "social recovery not enabled");
        require(newOwners.length > 0, "owners required");
        require(newThreshold > 0 && newThreshold <= newOwners.length, "invalid threshold");

        // 计算恢复请求的唯一哈希
        bytes32 recoveryHash = keccak256(abi.encodePacked(newOwners, newThreshold));

        // 检查是否达到 guardian 阈值
        require(recoveryApprovalCount[recoveryHash] >= guardianThreshold, "insufficient guardian approvals");

        // 执行恢复
        ownerlist = newOwners;
        threshold = newThreshold;

        // 清除这次恢复的批准记录
        _clearRecoveryApprovals(recoveryHash);

        emit RecoveryExecuted(recoveryHash, newOwners, newThreshold);
    }

    /**
     * @notice 取消 guardian 的恢复批准
     * @param newOwners 要取消的恢复请求的 owner 列表
     * @param newThreshold 要取消的恢复请求的阈值
     */
    function revokeRecoveryApproval(address[] memory newOwners, uint256 newThreshold) external {
        require(isGuardian(msg.sender), "not a guardian");

        bytes32 recoveryHash = keccak256(abi.encodePacked(newOwners, newThreshold));

        require(recoveryApprovals[recoveryHash][msg.sender], "not approved");

        recoveryApprovals[recoveryHash][msg.sender] = false;
        recoveryApprovalCount[recoveryHash]--;
    }

    /**
     * @notice 清除恢复批准记录（内部函数）
     */
    function _clearRecoveryApprovals(bytes32 recoveryHash) internal {
        uint256 length = guardians.length;
        for (uint256 i = 0; i < length; i++) {
            if (recoveryApprovals[recoveryHash][guardians[i]]) {
                recoveryApprovals[recoveryHash][guardians[i]] = false;
            }
        }
        recoveryApprovalCount[recoveryHash] = 0;
    }

    // ============================================
    // View Functions
    // ============================================

    /**
     * @notice 检查社交恢复是否已启用
     */
    function isSocialRecoveryEnabled() external view returns (bool) {
        return guardians.length > 0 && guardianThreshold > 0;
    }

    /**
     * @notice 获取恢复请求的批准数量
     */
    function getRecoveryApprovalCount(address[] memory newOwners, uint256 newThreshold)
    external view returns (uint256)
    {
        bytes32 recoveryHash = keccak256(abi.encodePacked(newOwners, newThreshold));
        return recoveryApprovalCount[recoveryHash];
    }

    /**
     * @notice 检查 guardian 是否批准了某个恢复请求
     */
    function hasApprovedRecovery(
        address guardian,
        address[] memory newOwners,
        uint256 newThreshold
    ) external view returns (bool) {
        bytes32 recoveryHash = keccak256(abi.encodePacked(newOwners, newThreshold));
        return recoveryApprovals[recoveryHash][guardian];
    }

    /**
     * @notice 获取当前的 owner 列表
     */
    function getOwners() external view returns (address[] memory) {
        return ownerlist;
    }

    /**
     * @notice 获取当前的 guardian 列表
     */
    function getGuardians() external view returns (address[] memory) {
        return guardians;
    }

    // ============================================
    // Original Functions
    // ============================================

    /**
     * check current account deposit in the entryPoint
     */
    function getDeposit() public view returns (uint256) {
        return entryPoint().balanceOf(address(this));
    }

    /**
     * deposit more funds for this account in the entryPoint
     */
    function addDeposit() public payable {
        entryPoint().depositTo{value: msg.value}(address(this));
    }

    /**
     * withdraw value from the account's deposit
     * @param withdrawAddress target to send to
     * @param amount to withdraw
     */
    function withdrawDepositTo(address payable withdrawAddress, uint256 amount) public onlyOwner {
        entryPoint().withdrawTo(withdrawAddress, amount);
    }

    function _authorizeUpgrade(address newImplementation) internal view override {
        (newImplementation);
        _onlyOwner();
    }
}
