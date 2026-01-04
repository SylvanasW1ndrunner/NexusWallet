# JSON 同步机制说明

本文档说明 Nexus AA Service 如何自动同步本地 JSON 配置文件。

## 📁 JSON 文件结构

### 1. Wallet 配置文件 (`wallet_{name}.json`)

存储钱包和账户信息：

```json
{
  "wallet_name": "default",
  "key_manager_address": "0x...",
  "accounts": {
    "sepolia": [
      {
        "network_name": "sepolia",
        "name": "My Main Account",
        "contract_address": "0x...",
        "owners": ["0x..."],
        "threshold": 1,
        "guardians": [],
        "guardian_threshold": 0,
        "salt": 0,
        "bundler_url": null,
        "paymaster_url": null
      }
    ]
  }
}
```

### 2. Network 配置文件 (`config.json`)

存储网络配置：

```json
{
  "networks": {
    "sepolia": {
      "chain_id": 11155111,
      "rpc_url": "https://rpc.sepolia.org",
      "entrypoint_address": "0x...",
      "factory_address": "0x...",
      "name": "Sepolia Testnet"
    }
  }
}
```

### 3. KeyStore 文件 (`keystore.json`)

加密存储私钥（已有机制，不需修改）

---

## ✅ 自动同步场景

### Account 操作

| 操作 | API 端点 | 自动同步 | 说明 |
|------|---------|---------|------|
| **新增账户** | `POST /api/v1/chain/accounts` | ✅ | `wallet.add_account(save=True)` |
| **删除账户** | `DELETE /api/v1/chain/accounts` | ✅ | `wallet.remove_account(save=True)` |
| **更新账户** | `PATCH /api/v1/chain/accounts` | ✅ | `wallet.update_account(save=True)` |
| **加载账户** | 服务启动时 | ✅ | `Wallet(auto_load=True)` |

### Network Config 操作

| 操作 | API 端点 | 自动同步 | 说明 |
|------|---------|---------|------|
| **新增网络** | `POST /api/v1/chain/networks` | ✅ | `config.add_network(save=True)` |
| **更新网络** | `PATCH /api/v1/chain/networks` | ✅ | `config.save_to_json()` |
| **删除网络** | `DELETE /api/v1/chain/networks` | ✅ | `config.remove_network(save=True)` |
| **加载网络** | 服务启动时 | ✅ | `Config()` 自动加载 |

---

## 🔄 同步机制详解

### 1. Account 同步

#### 新增账户
```python
# API 调用
POST /api/v1/chain/accounts
{
  "network_name": "sepolia",
  "name": "My Account",
  "owners": ["0x..."],
  "threshold": 1
}

# 内部流程
wallet.add_account(
    network_name="sepolia",
    name="My Account",
    owners=["0x..."],
    threshold=1,
    save=True  # ✅ 自动保存到 JSON
)
```

#### 更新账户
```python
# API 调用
PATCH /api/v1/chain/accounts
{
  "network_name": "sepolia",
  "account_address": "0x...",
  "name": "New Name",
  "bundler_url": "https://new-bundler.com"
}

# 内部流程
wallet.update_account(
    network_name="sepolia",
    contract_address="0x...",
    name="New Name",
    bundler_url="https://new-bundler.com",
    save=True  # ✅ 自动保存到 JSON
)
```

#### 删除账户
```python
# API 调用
DELETE /api/v1/chain/accounts
{
  "network_name": "sepolia",
  "account_address": "0x..."
}

# 内部流程
wallet.remove_account(
    network_name="sepolia",
    contract_address="0x...",
    save=True  # ✅ 自动保存到 JSON
)
```

### 2. Network Config 同步

#### 新增网络
```python
# API 调用
POST /api/v1/chain/networks
{
  "network_name": "custom_network",
  "chain_id": 12345,
  "rpc_url": "https://rpc.custom.network",
  "entrypoint_address": "0x...",
  "factory_address": "0x...",
  "name": "Custom Network"
}

# 内部流程
config.add_network(
    network_name="custom_network",
    network_config=NetworkConfig(...),
    save=True  # ✅ 自动保存到 JSON
)
```

#### 更新网络
```python
# API 调用
PATCH /api/v1/chain/networks
{
  "network_name": "sepolia",
  "rpc_url": "https://new-rpc.sepolia.org",
  "entrypoint_address": "0xNewEntryPoint..."
}

# 内部流程
network = config.get_network("sepolia")
network.rpc_url = "https://new-rpc.sepolia.org"
network.entrypoint_address = "0xNewEntryPoint..."
config.save_to_json()  # ✅ 保存到 JSON
```

#### 删除网络
```python
# API 调用
DELETE /api/v1/chain/networks
{
  "network_name": "old_network"
}

# 内部流程
config.remove_network(
    network_name="old_network",
    save=True  # ✅ 自动保存到 JSON
)
```

---

## 🚀 启动加载流程

### 1. 服务启动时

```python
# backend/service/api.py
@app.on_event("startup")
async def startup_event():
    # 1. 检查 keystore
    if os.path.exists("keystore.json"):
        print("✓ Keystore found")

    # 2. 用户解锁后，自动加载 wallet
    # POST /api/v1/chain/auth/unlock
    singleton.init_from_keystore(password)
    # ↓
    # Wallet(key_manager=km, auto_load=True)
    # ↓
    # 自动加载 wallet_default.json ✅
```

### 2. Config 自动加载

```python
# Config 是单例，首次创建时自动加载
config = Config()
# ↓
# 检查 config.json 是否存在
# ↓
# 自动加载网络配置 ✅
```

---

## 📝 使用示例

### Python 代码示例

```python
from backend.utils.wallet import Wallet
from backend.keymanager.keyManager import KeyManager
from backend.config.config import Config, NetworkConfig

# 1. 初始化
km = KeyManager()
km.unlock("password")
wallet = Wallet(key_manager=km, auto_load=True)  # ✅ 自动加载

# 2. 添加账户
account = wallet.add_account(
    network_name="sepolia",
    name="My Savings Account",
    owners=[km.address],
    threshold=1
)  # ✅ 自动保存到 wallet_default.json

# 3. 修改账户
wallet.update_account(
    network_name="sepolia",
    contract_address=account.contract_address,
    name="Updated Name",
    bundler_url="https://new-bundler.com"
)  # ✅ 自动保存

# 4. 添加网络
config = Config()
config.add_network(
    "polygon",
    NetworkConfig(
        chain_id=137,
        rpc_url="https://polygon-rpc.com",
        name="Polygon Mainnet"
    )
)  # ✅ 自动保存到 config.json
```

### API 调用示例

```bash
# 1. 解锁钱包（加载 wallet JSON）
curl -X POST http://localhost:8000/api/v1/chain/auth/unlock \
  -H "Content-Type: application/json" \
  -d '{"password":"MyPassword123"}'

# 2. 创建账户（自动保存）
curl -X POST http://localhost:8000/api/v1/chain/accounts \
  -H "X-Session-Token: YOUR_TOKEN" \
  -d '{
    "network_name": "sepolia",
    "name": "My Account",
    "threshold": 1
  }'

# 3. 更新账户名称（自动保存）
curl -X PATCH http://localhost:8000/api/v1/chain/accounts \
  -H "X-Session-Token: YOUR_TOKEN" \
  -d '{
    "network_name": "sepolia",
    "account_address": "0x...",
    "name": "New Account Name"
  }'

# 4. 添加自定义网络（自动保存）
curl -X POST http://localhost:8000/api/v1/chain/networks \
  -H "X-Session-Token: YOUR_TOKEN" \
  -d '{
    "network_name": "polygon",
    "chain_id": 137,
    "rpc_url": "https://polygon-rpc.com",
    "name": "Polygon Mainnet"
  }'
```

---

## ⚠️ 注意事项

### 1. 并发安全

- 当前实现是**单进程安全**的
- 如果多个进程同时修改，可能导致数据覆盖
- **建议**：生产环境使用单一服务实例

### 2. 备份建议

定期备份 JSON 文件：

```bash
# 备份脚本示例
cp wallet_default.json wallet_default.json.backup.$(date +%Y%m%d_%H%M%S)
cp config.json config.json.backup.$(date +%Y%m%d_%H%M%S)
cp keystore.json keystore.json.backup.$(date +%Y%m%d_%H%M%S)
```

### 3. 迁移数据

如果需要迁移到新机器：

```bash
# 复制这些文件即可
wallet_default.json  # 账户配置
config.json          # 网络配置
keystore.json        # 私钥（加密的）
```

---

## 🎯 总结

✅ **所有修改操作都会自动同步到 JSON 文件**

| 文件 | 存储内容 | 自动同步 | 加载时机 |
|------|---------|---------|---------|
| `wallet_*.json` | 账户信息 | ✅ | 解锁钱包时 |
| `config.json` | 网络配置 | ✅ | 服务启动时 |
| `keystore.json` | 加密私钥 | ✅ | 创建/导入时 |

**无需手动保存**，所有 API 操作都会立即同步到磁盘！
