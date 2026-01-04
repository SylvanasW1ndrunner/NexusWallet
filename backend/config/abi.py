factory_abi =[
    {
        "inputs": [
            {
                "internalType": "contract IEntryPoint",
                "name": "_entryPoint",
                "type": "address"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [],
        "name": "accountImplementation",
        "outputs": [
            {
                "internalType": "contract SimpleAccount",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "ownerlist",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "threshold",
                "type": "uint256"
            },
            {
                "internalType": "address[]",
                "name": "guardians",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "guardianThreshold",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "salt",
                "type": "uint256"
            }
        ],
        "name": "createAccount",
        "outputs": [
            {
                "internalType": "contract SimpleAccount",
                "name": "ret",
                "type": "address"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "ownerlist",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "threshold",
                "type": "uint256"
            },
            {
                "internalType": "address[]",
                "name": "guardians",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "guardianThreshold",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "salt",
                "type": "uint256"
            }
        ],
        "name": "getAddress",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "owner",
                "type": "address"
            }
        ],
        "name": "getOwnedAccounts",
        "outputs": [
            {
                "internalType": "address[]",
                "name": "",
                "type": "address[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "ownedAccounts",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

entrypoint_abi = [{"inputs":[{"internalType":"bool","name":"success","type":"bool"},{"internalType":"bytes","name":"ret","type":"bytes"}],"name":"DelegateAndRevert","type":"error"}, {"inputs":[{"internalType":"uint256","name":"opIndex","type":"uint256"},{"internalType":"string","name":"reason","type":"string"}],"name":"FailedOp","type":"error"}, {"inputs":[{"internalType":"uint256","name":"opIndex","type":"uint256"},{"internalType":"string","name":"reason","type":"string"},{"internalType":"bytes","name":"inner","type":"bytes"}],"name":"FailedOpWithRevert","type":"error"}, {"inputs":[{"internalType":"bytes","name":"returnData","type":"bytes"}],"name":"PostOpReverted","type":"error"}, {"inputs":[],"name":"ReentrancyGuardReentrantCall","type":"error"}, {"inputs":[{"internalType":"address","name":"sender","type":"address"}],"name":"SenderAddressResult","type":"error"}, {"inputs":[{"internalType":"address","name":"aggregator","type":"address"}],"name":"SignatureValidationFailed","type":"error"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "bytes32", "name": "userOpHash", "type": "bytes32"}, {"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": False, "internalType": "address", "name": "factory", "type": "address"}, {"indexed": False, "internalType": "address", "name": "paymaster", "type": "address"}], "name": "AccountDeployed", "type": "event"}, {"anonymous": False, "inputs":[], "name": "BeforeExecution", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "address", "name": "account", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "totalDeposit", "type": "uint256"}], "name": "Deposited", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "bytes32", "name": "userOpHash", "type": "bytes32"}, {"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "nonce", "type": "uint256"}, {"indexed": False, "internalType": "bytes", "name": "revertReason", "type": "bytes"}], "name": "PostOpRevertReason", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "address", "name": "aggregator", "type": "address"}], "name": "SignatureAggregatorChanged", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "address", "name": "account", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "totalStaked", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "unstakeDelaySec", "type": "uint256"}], "name": "StakeLocked", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "address", "name": "account", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "withdrawTime", "type": "uint256"}], "name": "StakeUnlocked", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "address", "name": "account", "type": "address"}, {"indexed": False, "internalType": "address", "name": "withdrawAddress", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "StakeWithdrawn", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "bytes32", "name": "userOpHash", "type": "bytes32"}, {"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": True, "internalType": "address", "name": "paymaster", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "nonce", "type": "uint256"}, {"indexed": False, "internalType": "bool", "name": "success", "type": "bool"}, {"indexed": False, "internalType": "uint256", "name": "actualGasCost", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "actualGasUsed", "type": "uint256"}], "name": "UserOperationEvent", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "bytes32", "name": "userOpHash", "type": "bytes32"}, {"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "nonce", "type": "uint256"}], "name": "UserOperationPrefundTooLow", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "bytes32", "name": "userOpHash", "type": "bytes32"}, {"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "nonce", "type": "uint256"}, {"indexed": False, "internalType": "bytes", "name": "revertReason", "type": "bytes"}], "name": "UserOperationRevertReason", "type": "event"}, {"anonymous": False, "inputs":[{"indexed": True, "internalType": "address", "name": "account", "type": "address"}, {"indexed": False, "internalType": "address", "name": "withdrawAddress", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "Withdrawn", "type": "event"}, {"inputs":[{"internalType": "uint32", "name": "unstakeDelaySec", "type": "uint32"}], "name": "addStake", "outputs":[], "stateMutability": "payable", "type": "function"}, {"inputs":[{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs":[{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs":[{"internalType": "address", "name": "target", "type": "address"}, {"internalType": "bytes", "name": "data", "type": "bytes"}], "name": "delegateAndRevert", "outputs":[], "stateMutability": "nonpayable", "type": "function"}, {"inputs":[{"internalType": "address", "name": "account", "type": "address"}], "name": "depositTo", "outputs":[], "stateMutability": "payable", "type": "function"}, {"inputs":[{"internalType": "address", "name": "", "type": "address"}], "name": "deposits", "outputs":[{"internalType": "uint256", "name": "deposit", "type": "uint256"}, {"internalType": "bool", "name": "staked", "type": "bool"}, {"internalType": "uint112", "name": "stake", "type": "uint112"}, {"internalType": "uint32", "name": "unstakeDelaySec", "type": "uint32"}, {"internalType": "uint48", "name": "withdrawTime", "type": "uint48"}], "stateMutability": "view", "type": "function"}, {"inputs":[{"internalType": "address", "name": "account", "type": "address"}], "name": "getDepositInfo", "outputs":[{"components":[{"internalType": "uint256", "name": "deposit", "type": "uint256"}, {"internalType": "bool", "name": "staked", "type": "bool"}, {"internalType": "uint112", "name": "stake", "type": "uint112"}, {"internalType": "uint32", "name": "unstakeDelaySec", "type": "uint32"}, {"internalType": "uint48", "name": "withdrawTime", "type": "uint48"}], "internalType": "struct IStakeManager.DepositInfo", "name": "info", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs":[{"internalType": "address", "name": "sender", "type": "address"}, {"internalType": "uint192", "name": "key", "type": "uint192"}], "name": "getNonce", "outputs":[{"internalType": "uint256", "name": "nonce", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs":[{"internalType": "bytes", "name": "initCode", "type": "bytes"}], "name": "getSenderAddress", "outputs":[], "stateMutability": "nonpayable", "type": "function"}, {"inputs":[{"components":[{"internalType": "address", "name": "sender", "type": "address"}, {"internalType": "uint256", "name": "nonce", "type": "uint256"}, {"internalType": "bytes", "name": "initCode", "type": "bytes"}, {"internalType": "bytes", "name": "callData", "type": "bytes"}, {"internalType": "bytes32", "name": "accountGasLimits", "type": "bytes32"}, {"internalType": "uint256", "name": "preVerificationGas", "type": "uint256"}, {"internalType": "bytes32", "name": "gasFees", "type": "bytes32"}, {"internalType": "bytes", "name": "paymasterAndData", "type": "bytes"}, {"internalType": "bytes", "name": "signature", "type": "bytes"}], "internalType": "struct PackedUserOperation", "name": "userOp", "type": "tuple"}], "name": "getUserOpHash", "outputs":[{"internalType": "bytes32", "name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"}, {"inputs":[{"components":[{"components":[{"internalType": "address", "name": "sender", "type": "address"}, {"internalType": "uint256", "name": "nonce", "type": "uint256"}, {"internalType": "bytes", "name": "initCode", "type": "bytes"}, {"internalType": "bytes", "name": "callData", "type": "bytes"}, {"internalType": "bytes32", "name": "accountGasLimits", "type": "bytes32"}, {"internalType": "uint256", "name": "preVerificationGas", "type": "uint256"}, {"internalType": "bytes32", "name": "gasFees", "type": "bytes32"}, {"internalType": "bytes", "name": "paymasterAndData", "type": "bytes"}, {"internalType": "bytes", "name": "signature", "type": "bytes"}], "internalType": "struct PackedUserOperation[]", "name": "userOps", "type": "tuple[]"}, {"internalType": "contract IAggregator", "name": "aggregator", "type": "address"}, {"internalType": "bytes", "name": "signature", "type": "bytes"}], "internalType": "struct IEntryPoint.UserOpsPerAggregator[]", "name": "opsPerAggregator", "type": "tuple[]"}, {"internalType": "address payable", "name": "beneficiary", "type": "address"}], "name": "handleAggregatedOps", "outputs":[], "stateMutability": "nonpayable", "type": "function"}, {"inputs":[{"components":[{"internalType": "address", "name": "sender", "type": "address"}, {"internalType": "uint256", "name": "nonce", "type": "uint256"}, {"internalType": "bytes", "name": "initCode", "type": "bytes"}, {"internalType": "bytes", "name": "callData", "type": "bytes"}, {"internalType": "bytes32", "name": "accountGasLimits", "type": "bytes32"}, {"internalType": "uint256", "name": "preVerificationGas", "type": "uint256"}, {"internalType": "bytes32", "name": "gasFees", "type": "bytes32"}, {"internalType": "bytes", "name": "paymasterAndData", "type": "bytes"}, {"internalType": "bytes", "name": "signature", "type": "bytes"}], "internalType": "struct PackedUserOperation[]", "name": "ops", "type": "tuple[]"}, {"internalType": "address payable", "name": "beneficiary", "type": "address"}], "name": "handleOps", "outputs":[], "stateMutability": "nonpayable", "type": "function"}, {"inputs":[{"internalType": "uint192", "name": "key", "type": "uint192"}], "name": "incrementNonce", "outputs":[], "stateMutability": "nonpayable", "type": "function"}, {"inputs":[{"internalType": "bytes", "name": "callData", "type": "bytes"}, {"components":[{"components":[{"internalType": "address", "name": "sender", "type": "address"}, {"internalType": "uint256", "name": "nonce", "type": "uint256"}, {"internalType": "uint256", "name": "verificationGasLimit", "type": "uint256"}, {"internalType": "uint256", "name": "callGasLimit", "type": "uint256"}, {"internalType": "uint256", "name": "paymasterVerificationGasLimit", "type": "uint256"}, {"internalType": "uint256", "name": "paymasterPostOpGasLimit", "type": "uint256"}, {"internalType": "uint256", "name": "preVerificationGas", "type": "uint256"}, {"internalType": "address", "name": "paymaster", "type": "address"}, {"internalType": "uint256", "name": "maxFeePerGas", "type": "uint256"}, {"internalType": "uint256", "name": "maxPriorityFeePerGas", "type": "uint256"}], "internalType": "struct EntryPoint.MemoryUserOp", "name": "mUserOp", "type": "tuple"}, {"internalType": "bytes32", "name": "userOpHash", "type": "bytes32"}, {"internalType": "uint256", "name": "prefund", "type": "uint256"}, {"internalType": "uint256", "name": "contextOffset", "type": "uint256"}, {"internalType": "uint256", "name": "preOpGas", "type": "uint256"}], "internalType": "struct EntryPoint.UserOpInfo", "name": "opInfo", "type": "tuple"}, {"internalType": "bytes", "name": "context", "type": "bytes"}], "name": "innerHandleOp", "outputs":[{"internalType": "uint256", "name": "actualGasCost", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs":[{"internalType": "address", "name": "", "type": "address"}, {"internalType": "uint192", "name": "", "type": "uint192"}], "name": "nonceSequenceNumber", "outputs":[{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs":[{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}], "name": "supportsInterface", "outputs":[{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}, {"inputs":[], "name": "unlockStake", "outputs":[], "stateMutability": "nonpayable", "type": "function"}, {"inputs":[{"internalType": "address payable", "name": "withdrawAddress", "type": "address"}], "name": "withdrawStake", "outputs":[], "stateMutability": "nonpayable", "type": "function"}, {"inputs":[{"internalType": "address payable", "name": "withdrawAddress", "type": "address"}, {"internalType": "uint256", "name": "withdrawAmount", "type": "uint256"}], "name": "withdrawTo", "outputs":[], "stateMutability": "nonpayable", "type": "function"}, {"stateMutability": "payable", "type": "receive"}]
account_abi = [
    {
        "inputs": [
            {
                "internalType": "contract IEntryPoint",
                "name": "anEntryPoint",
                "type": "address"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "target",
                "type": "address"
            }
        ],
        "name": "AddressEmptyCode",
        "type": "error"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "implementation",
                "type": "address"
            }
        ],
        "name": "ERC1967InvalidImplementation",
        "type": "error"
    },
    {
        "inputs": [],
        "name": "ERC1967NonPayable",
        "type": "error"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "index",
                "type": "uint256"
            },
            {
                "internalType": "bytes",
                "name": "error",
                "type": "bytes"
            }
        ],
        "name": "ExecuteError",
        "type": "error"
    },
    {
        "inputs": [],
        "name": "FailedCall",
        "type": "error"
    },
    {
        "inputs": [],
        "name": "InvalidInitialization",
        "type": "error"
    },
    {
        "inputs": [],
        "name": "NotInitializing",
        "type": "error"
    },
    {
        "inputs": [],
        "name": "UUPSUnauthorizedCallContext",
        "type": "error"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "slot",
                "type": "bytes32"
            }
        ],
        "name": "UUPSUnsupportedProxiableUUID",
        "type": "error"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address[]",
                "name": "newGuardians",
                "type": "address[]"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "newGuardianThreshold",
                "type": "uint256"
            }
        ],
        "name": "GuardiansUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint64",
                "name": "version",
                "type": "uint64"
            }
        ],
        "name": "Initialized",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address[]",
                "name": "newOwners",
                "type": "address[]"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "newThreshold",
                "type": "uint256"
            }
        ],
        "name": "OwnersUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "recoveryHash",
                "type": "bytes32"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "guardian",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "approvalCount",
                "type": "uint256"
            }
        ],
        "name": "RecoveryApproved",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "recoveryHash",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "internalType": "address[]",
                "name": "newOwners",
                "type": "address[]"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "newThreshold",
                "type": "uint256"
            }
        ],
        "name": "RecoveryExecuted",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "contract IEntryPoint",
                "name": "entryPoint",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "address[]",
                "name": "owners",
                "type": "address[]"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "threshold",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "address[]",
                "name": "guardians",
                "type": "address[]"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "guardianThreshold",
                "type": "uint256"
            }
        ],
        "name": "SimpleAccountInitialized",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "implementation",
                "type": "address"
            }
        ],
        "name": "Upgraded",
        "type": "event"
    },
    {
        "inputs": [],
        "name": "UPGRADE_INTERFACE_VERSION",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "addDeposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "newGuardian",
                "type": "address"
            }
        ],
        "name": "addGuardian",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "newOwner",
                "type": "address"
            }
        ],
        "name": "addOwner",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "newOwners",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "newThreshold",
                "type": "uint256"
            }
        ],
        "name": "approveRecovery",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "entryPoint",
        "outputs": [
            {
                "internalType": "contract IEntryPoint",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "target",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "value",
                "type": "uint256"
            },
            {
                "internalType": "bytes",
                "name": "data",
                "type": "bytes"
            }
        ],
        "name": "execute",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "components": [
                    {
                        "internalType": "address",
                        "name": "target",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "value",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bytes",
                        "name": "data",
                        "type": "bytes"
                    }
                ],
                "internalType": "struct BaseAccount.Call[]",
                "name": "calls",
                "type": "tuple[]"
            }
        ],
        "name": "executeBatch",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "newOwners",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "newThreshold",
                "type": "uint256"
            }
        ],
        "name": "executeRecovery",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getDeposit",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getGuardians",
        "outputs": [
            {
                "internalType": "address[]",
                "name": "",
                "type": "address[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getNonce",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getOwners",
        "outputs": [
            {
                "internalType": "address[]",
                "name": "",
                "type": "address[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "newOwners",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "newThreshold",
                "type": "uint256"
            }
        ],
        "name": "getRecoveryApprovalCount",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "guardianThreshold",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "guardians",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "guardian",
                "type": "address"
            },
            {
                "internalType": "address[]",
                "name": "newOwners",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "newThreshold",
                "type": "uint256"
            }
        ],
        "name": "hasApprovedRecovery",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "_ownerlist",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "_threshold",
                "type": "uint256"
            },
            {
                "internalType": "address[]",
                "name": "_guardians",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "_guardianThreshold",
                "type": "uint256"
            }
        ],
        "name": "initialize",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "account",
                "type": "address"
            }
        ],
        "name": "isGuardian",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "account",
                "type": "address"
            }
        ],
        "name": "isOwner",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "isSocialRecoveryEnabled",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "uint256[]",
                "name": "",
                "type": "uint256[]"
            },
            {
                "internalType": "uint256[]",
                "name": "",
                "type": "uint256[]"
            },
            {
                "internalType": "bytes",
                "name": "",
                "type": "bytes"
            }
        ],
        "name": "onERC1155BatchReceived",
        "outputs": [
            {
                "internalType": "bytes4",
                "name": "",
                "type": "bytes4"
            }
        ],
        "stateMutability": "pure",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "bytes",
                "name": "",
                "type": "bytes"
            }
        ],
        "name": "onERC1155Received",
        "outputs": [
            {
                "internalType": "bytes4",
                "name": "",
                "type": "bytes4"
            }
        ],
        "stateMutability": "pure",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "bytes",
                "name": "",
                "type": "bytes"
            }
        ],
        "name": "onERC721Received",
        "outputs": [
            {
                "internalType": "bytes4",
                "name": "",
                "type": "bytes4"
            }
        ],
        "stateMutability": "pure",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "ownerlist",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "proxiableUUID",
        "outputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32"
            }
        ],
        "name": "recoveryApprovalCount",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32"
            },
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "name": "recoveryApprovals",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "guardianToRemove",
                "type": "address"
            }
        ],
        "name": "removeGuardian",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "ownerToRemove",
                "type": "address"
            }
        ],
        "name": "removeOwner",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "newOwners",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "newThreshold",
                "type": "uint256"
            }
        ],
        "name": "revokeRecoveryApproval",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes4",
                "name": "interfaceId",
                "type": "bytes4"
            }
        ],
        "name": "supportsInterface",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "threshold",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "newGuardians",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "newGuardianThreshold",
                "type": "uint256"
            }
        ],
        "name": "updateGuardians",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "newOwners",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "newThreshold",
                "type": "uint256"
            }
        ],
        "name": "updateOwners",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "newImplementation",
                "type": "address"
            },
            {
                "internalType": "bytes",
                "name": "data",
                "type": "bytes"
            }
        ],
        "name": "upgradeToAndCall",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "components": [
                    {
                        "internalType": "address",
                        "name": "sender",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "nonce",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bytes",
                        "name": "initCode",
                        "type": "bytes"
                    },
                    {
                        "internalType": "bytes",
                        "name": "callData",
                        "type": "bytes"
                    },
                    {
                        "internalType": "bytes32",
                        "name": "accountGasLimits",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "uint256",
                        "name": "preVerificationGas",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bytes32",
                        "name": "gasFees",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "bytes",
                        "name": "paymasterAndData",
                        "type": "bytes"
                    },
                    {
                        "internalType": "bytes",
                        "name": "signature",
                        "type": "bytes"
                    }
                ],
                "internalType": "struct PackedUserOperation",
                "name": "userOp",
                "type": "tuple"
            },
            {
                "internalType": "bytes32",
                "name": "userOpHash",
                "type": "bytes32"
            },
            {
                "internalType": "uint256",
                "name": "missingAccountFunds",
                "type": "uint256"
            }
        ],
        "name": "validateUserOp",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "validationData",
                "type": "uint256"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address payable",
                "name": "withdrawAddress",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "withdrawDepositTo",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "stateMutability": "payable",
        "type": "receive"
    }
]