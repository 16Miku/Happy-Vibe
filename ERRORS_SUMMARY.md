# Happy Vibe 项目错误总结

## 项目启动过程中的错误及解决方案

### 错误 1: SQLAlchemy 重复表定义错误

**错误信息：**
```
sqlalchemy.exc.InvalidRequestError: Table 'friend_requests' is already defined for this MetaData instance.
```

**根本原因：**
- `src/storage/models.py` 中 `FriendRequest` 类定义混乱
- `src/multiplayer/models.py` 中也存在重复的 `FriendRequest` 类定义
- 两个文件都使用相同的 `__tablename__ = "friend_requests"`

**解决方案：**
1. 删除 `src/storage/models.py` 中错误的双重类定义结构
2. 从 `src/multiplayer/models.py` 中删除重复的 `FriendRequest` 类和 `FriendRequestStatus` 枚举
3. 更新 `src/multiplayer/__init__.py` 从 `src.storage.models` 导入这两个类型
4. 更新 `src/api/__init__.py` 删除重复的路由名称

**修改文件：**
- `src/storage/models.py`
- `src/multiplayer/models.py`
- `src/multiplayer/__init__.py`
- `src/api/__init__.py`
- `src/main.py`

---

### 错误 2: 代理导致 API 调用失败

**错误信息：**
```
Internal Server Error (500)
连接超时
```

**根本原因：**
- 系统设置了 Clash 代理（HTTP_PROXY 和 HTTPS_PROXY）
- NO_PROXY 环境变量未设置
- 所有本地请求（127.0.0.1:8765）都被发送到代理服务器
- 代理服务器无法访问本地服务

**解决方案：**
1. 在 Windows 系统环境变量中设置：
   ```
   变量名: NO_PROXY
   变量值: localhost,127.0.0.1,0.0.0.0
   ```

2. 或在 Clash 配置中添加绕过规则

**修改文件：**
- Windows 系统环境变量设置

---

### 错误 3: 数据库表未创建

**错误信息：**
```
Internal Server Error (500) on POST /api/player
数据库文件不存在
```

**根本原因：**
- `src/main.py` 中缺少数据库初始化代码
- 应用启动时没有调用 `db.create_tables()`
- 虽然创建了 Database 实例，但从未创建表结构

**解决方案：**
1. 在 `src/main.py` 中导入 `Database` 类
2. 在 `lifespan` 函数中添加数据库初始化：
   ```python
   from src.storage.database import Database

   # 在 lifespan 中:
   db = Database()
   db.create_tables()
   ```

**修改文件：**
- `src/main.py`

---

### 错误 4: SQLAlchemy 无效参数错误

**错误信息：**
```
TypeError: Invalid argument(s) 'extend_existing' sent to create_engine()
```

**根本原因：**
- 在 `src/storage/database.py` 中使用了不存在的参数 `extend_existing=True`
- SQLAlchemy 的 `create_engine()` 不支持此参数

**解决方案：**
从 `create_engine()` 调用中删除 `extend_existing=True` 参数

**修改文件：**
- `src/storage/database.py`

---

### 错误 5: 路由前缀不匹配

**错误信息：**
```
404 Not Found on:
- /api/achievements/player
- /api/shops/items
- /api/economy/metrics
- /api/leaderboards
```

**根本原因：**
API 路由定义的前缀与测试调用时的路径不一致

**解决方案：**
需要检查并统一路由前缀定义：
- `/api/achievements` vs `/api/achievement`
- `/api/shops` vs `/api/shop`
- `/api/economy` vs 其他经济相关路由

**待修改文件：**
- `src/api/achievement.py`
- `src/api/shop.py`
- `src/api/economy.py`
- `src/api/leaderboards.py`

---

## API 测试结果

**测试日期：** 2026-02-14
**测试通过率：** 9/15 (60%)

### ✅ 正常工作的端点
- GET /api/health
- GET /api/player
- GET /api/activity/current
- GET /api/farm
- GET /api/farm/crops
- GET /api/energy/status
- GET /api/check-in/status
- GET /api/market/listings
- GET /api/auctions

### ⚠️ 需要修复的端点
- POST /api/player (409 - 需要更好的错误处理)
- GET /api/player/{id} (404 - 路由定义问题)
- GET /api/achievements/player (404 - 前缀不匹配)
- GET /api/shops/items (404 - 前缀不匹配)
- GET /api/economy/metrics (404 - 路由缺失)
- GET /api/leaderboards (404 - 路由缺失)

---

## 经验教训

1. **避免重复定义**：确保每个表只在一个模型文件中定义
2. **环境变量配置**：开发时设置 NO_PROXY 避免代理干扰
3. **数据库初始化**：应用启动时必须调用表创建方法
4. **参数验证**：使用第三方库参数前先查阅文档
5. **路由一致性**：保持 API 路由前缀在整个项目中一致
