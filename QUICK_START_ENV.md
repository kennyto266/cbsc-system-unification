# 环境配置快速启动指南

## 立即开始

### 开发环境（最快）

```bash
# 1. 使用统一的开发配置
cp .env.development .env.local

# 2. 验证配置（可选但推荐）
python scripts/check_env.py

# 3. 启动服务
python src/api/main.py
```

### 生产环境部署

```bash
# 1. 复制生产配置模板
cp .env.production .env.local

# 2. 编辑并修改所有敏感配置
nano .env.local

# 3. 生成安全密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. 验证配置
python scripts/check_env.py

# 5. 启动服务
docker-compose up -d
```

## 需要修改的关键配置

### 生产环境必须修改（CHANGE_THIS）

- `DATABASE_URL` - 数据库连接字符串
- `JWT_SECRET` - JWT 签名密钥
- `SECRET_KEY` - 应用密钥
- `REDIS_PASSWORD` - Redis 密码
- `CORS_ORIGINS` - 允许的域名
- 所有 `CHANGE_THIS` 开头的值

### 密钥生成命令

```bash
# JWT 密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 加密密钥
python -c "import secrets; print(secrets.token_bytes(32).hex())"
```

## 验证清单

- [ ] 配置文件已创建（`.env.local`）
- [ ] 所有 `CHANGE_THIS` 值已修改
- [ ] 密钥长度至少 32 字符
- [ ] 数据库 URL 正确
- [ ] Redis 连接正常
- [ ] CORS 配置正确
- [ ] 验证脚本通过

## 故障排查

### 问题：验证失败

```bash
# 查看详细错误
python scripts/check_env.py
```

### 问题：连接数据库失败

```bash
# 检查数据库 URL
echo $DATABASE_URL

# 测试连接
python -c "from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); print(engine.connect())"
```

### 问题：CORS 错误

检查 `CORS_ORIGINS` 是否包含前端 URL。

## 完整文档

详细配置说明请参阅：`docs/ENVIRONMENT_CONFIGURATION_GUIDE.md`
