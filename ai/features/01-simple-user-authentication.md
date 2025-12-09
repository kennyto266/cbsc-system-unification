# 个人用户认证系统

## 🎯 功能概述
为个人使用者构建简单实用的认证系统，升级现有的基础JWT认证，提供安全可靠的登录体验。

## 📋 需求优先级：P0 (核心基础)

## 🔧 功能需求

### 1. 基础认证功能
- **用户名密码登录**: 简洁的登录表单
- **密码强度检测**: 实时密码安全度提示
- **记住登录状态**: 可选的自动登录
- **登录失败处理**: 安全的错误提示和锁定机制

### 2. 账户安全功能
- **密码修改**: 安全的密码更新流程
- **邮箱验证**: 基础的邮箱确认功能
- **登录历史**: 查看最近的登录记录
- **设备管理**: 查看和管理登录设备

### 3. 会话管理
- **JWT令牌**: 安全的令牌生成和验证
- **自动续期**: 无感知的登录状态维持
- **安全退出**: 清除所有登录状态
- **多设备支持**: 支持同时多个设备登录

## 🎨 UI/UX 设计

### 1. 登录界面
```typescript
// 简洁的登录页面
const LoginPage = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="max-w-md w-full space-y-8">
      <div className="text-center">
        <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
          登录到您的账户
        </h2>
      </div>

      <form className="mt-8 space-y-6">
        <div className="rounded-md shadow-sm -space-y-px">
          <div>
            <label htmlFor="username" className="sr-only">用户名</label>
            <Input
              id="username"
              name="username"
              type="text"
              required
              placeholder="用户名"
              className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="password" className="sr-only">密码</label>
            <Input
              id="password"
              name="password"
              type="password"
              required
              placeholder="密码"
              className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
              记住我
            </label>
          </div>

          <div className="text-sm">
            <a href="#" className="font-medium text-indigo-600 hover:text-indigo-500">
              忘记密码？
            </a>
          </div>
        </div>

        <div>
          <Button
            type="submit"
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            登录
          </Button>
        </div>
      </form>
    </div>
  </div>
);
```

### 2. 密码强度指示器
```typescript
const PasswordStrengthIndicator = ({ password }) => {
  const calculateStrength = (pwd) => {
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[a-z]/.test(pwd)) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^a-zA-Z0-9]/.test(pwd)) score++;

    return {
      score,
      level: score <= 2 ? 'weak' : score <= 4 ? 'medium' : 'strong',
      text: score <= 2 ? '弱' : score <= 4 ? '中等' : '强',
      color: score <= 2 ? 'bg-red-500' : score <= 4 ? 'bg-yellow-500' : 'bg-green-500'
    };
  };

  const { level, text, color } = calculateStrength(password);

  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-sm">
        <span>密码强度</span>
        <span className={color.replace('bg-', 'text-')}>{text}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${color} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${(calculateStrength(password).score / 5) * 100}%` }}
        />
      </div>
    </div>
  );
};
```

## 🔗 API 设计

### 认证端点
```python
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import jwt

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# JWT配置
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    # 验证用户凭据
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # 记录登录历史
    await record_login_history(user.id, get_client_ip())

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    # 记录登出事件
    await record_logout_history(current_user.id, get_client_ip())
    return {"message": "登出成功"}

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 检查新密码强度
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="新密码长度至少8位")

    # 更新密码
    current_user.password_hash = hash_password(new_password)
    current_user.updated_at = datetime.utcnow()

    # 保存到数据库
    await update_user(current_user)

    return {"message": "密码修改成功"}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user
```

## 📊 数据模型

### 简化的用户表
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- 登录历史记录
CREATE TABLE login_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    login_time TIMESTAMP DEFAULT NOW(),
    success BOOLEAN,
    failure_reason VARCHAR(100)
);

-- 设备记录
CREATE TABLE user_devices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    device_name VARCHAR(100),
    device_type VARCHAR(50), -- desktop, mobile, tablet
    user_agent TEXT,
    last_seen TIMESTAMP DEFAULT NOW(),
    is_trusted BOOLEAN DEFAULT FALSE
);
```

## 🔒 安全考虑

### 1. 密码安全
```python
import bcrypt

def hash_password(password: str) -> str:
    """安全地哈希密码"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
```

### 2. 登录保护
```python
async def check_login_attempts(username: str):
    """检查登录尝试次数"""
    user = get_user_by_username(username)
    if user and user.failed_login_attempts >= 5:
        if user.locked_until and datetime.utcnow() < user.locked_until:
            raise HTTPException(
                status_code=423,
                detail="账户已被锁定，请稍后再试"
            )

async def reset_login_attempts(user_id: int):
    """重置登录尝试次数"""
    await execute_query(
        "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = $1",
        user_id
    )

async def increment_failed_attempts(user_id: int):
    """增加失败登录次数"""
    await execute_query(
        """
        UPDATE users
        SET failed_login_attempts = failed_login_attempts + 1,
            locked_until = CASE
                WHEN failed_login_attempts >= 4 THEN NOW() + INTERVAL '30 minutes'
                ELSE NULL
            END
        WHERE id = $1
        """,
        user_id
    )
```

## 🧪 测试功能

### 1. 登录功能测试
```typescript
describe('Authentication', () => {
  test('successful login', async () => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'username=testuser&password=testpass'
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.access_token).toBeDefined();
    expect(data.user.username).toBe('testuser');
  });

  test('failed login with wrong password', async () => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'username=testuser&password=wrongpass'
    });

    expect(response.status).toBe(401);
  });

  test('password change', async () => {
    const token = await getAuthToken();

    const response = await fetch('/api/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        old_password: 'oldpass',
        new_password: 'newpass123'
      })
    });

    expect(response.status).toBe(200);
  });
});
```

## 📋 验收标准

### 功能验收
- [ ] 用户名密码登录正常工作
- [ ] 密码强度检测和提示
- [ ] 密码修改功能
- [ ] 登录历史查看
- [ ] 设备管理功能
- [ ] 安全退出功能

### 安全验收
- [ ] 密码使用bcrypt安全哈希
- [ ] JWT令牌安全生成和验证
- [ ] 登录失败保护机制
- [ ] 会话管理安全
- [ ] 输入验证和清理

### 用户体验验收
- [ ] 界面简洁易用
- [ ] 错误提示清晰
- [ ] 响应式设计
- [ ] 加载状态明确

## 🎯 成功指标

### 可用性指标
- **登录成功率**: > 99%
- **页面响应时间**: < 500ms
- **密码修改成功率**: > 95%

### 安全指标
- **密码破解防护**: 有效防止暴力破解
- **会话安全**: JWT令牌管理安全可靠
- **数据保护**: 敏感信息妥善保护

这个简化的认证系统专为个人使用设计，去除了企业级的复杂功能，保留了核心的安全性和易用性。