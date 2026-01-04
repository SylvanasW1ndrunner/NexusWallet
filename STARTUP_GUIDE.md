# Nexus AA Service - 启动指南

## 📋 应用程序启动流程

Nexus AA Service 遵循以下初始化顺序，确保所有组件正确加载：

### 启动顺序

```
1. 加载网络配置 (config.json)
   ↓
2. 初始化数据库 (PostgreSQL)
   ↓
3. 连接缓存服务 (Redis)
   ↓
4. 检查并加载 Keystore
   ↓
5. 初始化 KeyManager (锁定状态)
   ↓
6. 检查 Wallet 配置文件
   ↓
7. 启动 API 服务器
```

---

## 🚀 首次启动步骤

### 1. 环境配置

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

必需的环境变量：
```bash
# 数据库
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nexus_aa

# Redis
REDIS_URL=redis://localhost:6379/0

# 网络配置
INFURA_ID=your_infura_project_id

# Bundler
PIMLICO_API_KEY=your_pimlico_api_key

# API服务器
API_HOST=0.0.0.0
API_PORT=8000
```

### 2. 配置网络

创建或编辑 `config.json`（或通过 API 配置）：

```json
{
  "networks": {
    "sepolia": {
      "chain_id": 11155111,
      "rpc_url": "https://sepolia.infura.io/v3/YOUR_INFURA_ID",
      "entrypoint_address": "0x...",
      "factory_address": "0x...",
      "name": "Sepolia Testnet"
    }
  }
}
```

**自动加载方式：**
如果你已经部署了合约，可以从部署文件自动加载：
```bash
# 部署文件位置
backend/test/sepolia_deployment.json

# API 启动时会自动读取 config.json
# 如果 config.json 不存在，可以通过 API 添加网络
```

### 3. 启动依赖服务

```bash
# 启动 PostgreSQL (如果使用 Docker)
docker run -d --name nexus-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=nexus_aa \
  -p 5432:5432 \
  postgres:15

# 启动 Redis (如果使用 Docker)
docker run -d --name nexus-redis \
  -p 6379:6379 \
  redis:7
```

### 4. 初始化数据库

```bash
cd backend/service
python init_db.py
```

### 5. 启动 API 服务器

```bash
python backend/service/api.py
```

**预期输出：**
```
============================================================
Starting Nexus AA Service...
============================================================

1. Loading Network Configuration...
   ✓ Loaded 1 network(s):
     - sepolia (Chain ID: 11155111)

2. Initializing Database...
   ✓ Database initialized

3. Connecting to Redis...
   ✓ Redis connected

4. Checking Wallet Status...
   ⚠️  No keystore found: backend/keystore.json

   📝 Initialize wallet using one of:
      - POST /api/v1/chain/init/create (create new wallet)
      - POST /api/v1/chain/init/import-private-key (import private key)
      - POST /api/v1/chain/init/import-keystore (import keystore)

============================================================
✓ API running on http://0.0.0.0:8000
✓ API docs: http://0.0.0.0:8000/docs
============================================================
```

---

## 🔄 后续启动（已有 Keystore）

如果已经初始化了钱包，启动输出会是：

```
4. Checking Wallet Status...
   ✓ Keystore found: backend/keystore.json
   ✓ KeyManager initialized (locked)
   ✓ Wallet config found: wallet_default.json
   ℹ️  Wallet will be loaded after authentication

   📝 To unlock wallet:
      POST /api/v1/chain/auth/unlock
```

---

## 📝 初始化 Wallet

### 方式1: 创建新钱包

```bash
curl -X POST http://localhost:8000/api/v1/chain/init/create \
  -H "Content-Type: application/json" \
  -d '{"password": "your_secure_password"}'
```

### 方式2: 导入私钥（仅测试环境）

```bash
curl -X POST http://localhost:8000/api/v1/chain/init/import-private-key \
  -H "Content-Type: application/json" \
  -d '{
    "private_key": "your_private_key_without_0x",
    "password": "your_secure_password"
  }'
```

⚠️ **安全警告**: 此方式仅用于开发/测试环境！

### 方式3: 导入 Keystore（推荐）

```bash
curl -X POST http://localhost:8000/api/v1/chain/init/import-keystore \
  -H "Content-Type: application/json" \
  -d '{
    "keystore_path": "/path/to/keystore.json",
    "password": "keystore_password"
  }'
```

---

## 🔓 解锁 Wallet

每次启动后，需要解锁 wallet：

```bash
curl -X POST http://localhost:8000/api/v1/chain/auth/unlock \
  -H "Content-Type: application/json" \
  -d '{"password": "your_password"}'
```

返回：
```json
{
  "success": true,
  "session_token": "abc123...",
  "eoa_address": "0x...",
  "expires_in": 1800,
  "networks": ["sepolia"]
}
```

保存 `session_token` 用于后续 API 调用。

---

## 🌐 配置网络（通过 API）

如果启动时没有网络配置，可以通过 API 添加：

```bash
# 需要先解锁 wallet 获取 session_token

curl -X POST http://localhost:8000/api/v1/chain/networks \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: your_session_token" \
  -d '{
    "network_name": "sepolia",
    "chain_id": 11155111,
    "rpc_url": "https://sepolia.infura.io/v3/YOUR_INFURA_ID",
    "entrypoint_address": "0x...",
    "factory_address": "0x...",
    "name": "Sepolia Testnet"
  }'
```

---

## 🧪 运行测试

测试脚本会自动处理网络配置：

```bash
# 确保 .env 配置正确
# INFURA_ID=...
# PIMLICO_API_KEY=...
# PRIVATE_KEY=... (可选)

# 启动 API 服务器
python backend/service/api.py

# 在另一个终端运行测试
python backend/service/test_api.py
```

测试脚本会：
1. ✅ 检查网络配置，如不存在则自动配置
2. ✅ 导入私钥或创建新钱包
3. ✅ 测试所有 API endpoint
4. ✅ 执行完整交易流程

---

## 📂 重要文件位置

```
Nexus/
├── .env                          # 环境变量
├── config.json                   # 网络配置（自动生成）
├── backend/
│   ├── keystore.json            # 加密的私钥（自动生成）
│   ├── wallet_default.json      # Wallet配置（自动生成）
│   ├── test/
│   │   └── sepolia_deployment.json  # 部署信息
│   └── service/
│       ├── api.py               # API 服务器
│       ├── test_api.py          # 测试脚本
│       └── init_db.py           # 数据库初始化
```

---

## 🔒 安全建议

### 生产环境

1. ✅ **使用 HTTPS**: 配置 SSL/TLS 证书
2. ✅ **禁用私钥导入**: 设置 `ENVIRONMENT=production`
3. ✅ **使用 Keystore**: 前端上传加密的 keystore 文件
4. ✅ **强密码**: 使用强密码加密 keystore
5. ✅ **定期备份**: 备份 keystore 和 wallet 配置

### 开发环境

- 可以使用私钥导入进行快速测试
- 使用测试网络 (Sepolia, Goerli)
- 不要使用真实资金

---

## 🆘 常见问题

### Q: 启动时提示 "No networks configured"
**A**: 需要配置网络。可以：
- 手动创建 `config.json`
- 通过 API 添加网络
- 测试脚本会自动配置

### Q: 启动时提示 "Redis connection failed"
**A**: 确保 Redis 正在运行：
```bash
# 检查 Redis
redis-cli ping
# 应返回 PONG

# 或启动 Redis
redis-server
```

### Q: 如何重置 wallet?
**A**: 删除相关文件：
```bash
rm backend/keystore.json
rm wallet_default.json
rm config.json  # 可选，如果要重置网络配置
```

### Q: Session token 过期了怎么办?
**A**: 重新调用 unlock API：
```bash
POST /api/v1/chain/auth/unlock
```

---

## 📖 相关文档

- [API 文档](http://localhost:8000/docs) - 启动后访问
- [Sepolia 部署指南](SEPOLIA_DEPLOYMENT.md)
- [本地测试指南](LOCAL_HARDHAT_TESTING.md)

---

## 🎯 快速开始检查清单

- [ ] 安装依赖: `pip install -r requirements.txt`
- [ ] 配置 `.env` 文件
- [ ] 启动 PostgreSQL
- [ ] 启动 Redis
- [ ] 初始化数据库: `python backend/service/init_db.py`
- [ ] 部署合约（如需要）: `npx hardhat run scripts/deploy-sepolia.ts --network sepolia`
- [ ] 启动 API: `python backend/service/api.py`
- [ ] 初始化 wallet (通过 API)
- [ ] 运行测试: `python backend/service/test_api.py`

完成以上步骤后，你的 Nexus AA Service 就可以正常运行了！🎉
