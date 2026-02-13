# Phase 5 - 任务活动系统开发文档

## 一、概述

实现游戏内的任务/活动系统，为玩家提供日常目标和奖励机制。该系统包含三个核心功能模块：
- 日常任务系统：每日可完成的活动任务
- 成就任务系统：长期目标导向的任务
- 限时活动系统：特殊时期的增益活动

## 二、项目背景

Happy Vibe 是一款将真实编程活动转化为游戏体验的项目。玩家通过编码获得能量、经验等奖励。任务活动系统旨在：
1. 提供明确的每日目标，增加玩家粘性
2. 通过长期成就任务引导玩家探索游戏内容
3. 通过限时活动创造特殊事件体验

## 三、技术栈

- **后端框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy ORM
- **Python 版本**: 3.14.3
- **包管理**: uv

## 四、功能模块详细设计

### 4.1 日常任务系统

#### 任务类型定义

```python
class QuestType(str, Enum):
    """任务类型枚举"""
    DAILY_CHECK_IN = "daily_check_in"      # 每日签到
    CODING_TIME = "coding_time"              # 编程 N 分钟
    SUBMIT_CROPS = "submit_crops"            # 提交 N 个作物
    HARVEST_CROPS = "harvest_crops"          # 收获 N 个作物
    EARN_GOLD = "earn_gold"                  # 获得 N 金币
    SOCIAL_INTERACTION = "social_interaction"  # 社交互动
```

#### 奖励配置结构

```python
class QuestReward:
    """任务奖励配置"""
    vibe_energy: int      # Vibe 能量奖励
    gold: int            # 金币奖励
    experience: int      # 经验奖励
    diamonds: int       # 钻石奖励（可选）
    special_item: str   # 特殊物品（可选）
```

### 4.2 成就任务系统

成就任务不自动刷新，由玩家主动完成解锁。

### 4.3 限时活动系统

活动类型：
- `DOUBLE_EXP` - 双倍经验活动
- `SPECIAL_CROP` - 特殊作物活动
- `FESTIVAL` - 节日主题活动

## 五、API 端点设计

### 5.1 日常任务 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/quest/daily` | 获取当前玩家的日常任务列表 |
| GET | `/api/quest/{quest_id}/progress` | 查询指定任务的进度 |
| POST | `/api/quest/{quest_id}/complete` | 完成任务并领取奖励 |
| GET | `/api/quest/available` | 获取所有可接受的任务 |

### 5.2 活动系统 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/event/active` | 获取当前活跃的活动列表 |
| GET | `/api/event/{event_id}` | 获取活动详情 |

## 六、数据库模型设计

### 6.1 Quest（任务定义表）

```python
class Quest(Base):
    """任务定义表"""
    __tablename__ = "quests"

    quest_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    quest_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 任务类型
    title: Mapped[str] = mapped_column(String(100), nullable=False)     # 任务标题
    description: Mapped[str] = mapped_column(Text, nullable=False)       # 任务描述

    # 目标条件
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)    # 目标值
    target_param: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 目标参数

    # 奖励配置 (JSON)
    reward_json: Mapped[str] = mapped_column(Text, nullable=False)       # 奖励配置

    # 刷新规则
    is_daily: Mapped[bool] = mapped_column(Boolean, default=True)         # 是否日常任务
    refresh_at: Mapped[datetime] = mapped_column(DateTime, nullable=True) # 刷新时间

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)         # 是否启用
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### 6.2 QuestProgress（任务进度表）

```python
class QuestProgress(Base):
    """任务进度表"""
    __tablename__ = "quest_progress"

    progress_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    player_id: Mapped[str] = mapped_column(String(36), ForeignKey("players.player_id"), nullable=False)
    quest_id: Mapped[str] = mapped_column(String(36), ForeignKey("quests.quest_id"), nullable=False)

    # 进度
    current_value: Mapped[int] = mapped_column(Integer, default=0)         # 当前进度
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)     # 是否完成
    is_claimed: Mapped[bool] = mapped_column(Boolean, default=False)      # 是否已领取奖励

    # 时间
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_refresh: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # 最后刷新时间

    # 关系
    player: Mapped["Player"] = relationship("Player", foreign_keys=[player_id])
    quest: Mapped["Quest"] = relationship("Quest", foreign_keys=[quest_id])
```

### 6.3 GameEvent（游戏活动表）

```python
class GameEvent(Base):
    """游戏活动表"""
    __tablename__ = "game_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)    # 活动类型
    title: Mapped[str] = mapped_column(String(100), nullable=False)        # 活动标题
    description: Mapped[str] = mapped_column(Text, nullable=False)         # 活动描述

    # 时间
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # 开始时间
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)    # 结束时间

    # 效果配置 (JSON)
    effects_json: Mapped[str] = mapped_column(Text, nullable=False)        # 效果配置

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

## 七、实现步骤

### 步骤 1：数据模型

**文件**: `vibehub/src/storage/models.py`

在现有模型文件末尾添加：
1. `QuestType` 枚举
2. `Quest` 类
3. `QuestProgress` 类
4. `EventType` 枚举
5. `GameEvent` 类

**注意事项**：
- 使用与其他模型一致的风格
- 继承 `Base` 类
- 正确配置 relationship 和 foreign_keys
- 添加 `__repr__` 方法

### 步骤 2：任务管理器

**文件**: `vibehub/src/core/quest.py`

创建 `QuestManager` 类，包含以下方法：

```python
class QuestManager:
    """任务管理器"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_daily_quests(self, player_id: str) -> list[Quest]:
        """获取玩家的日常任务列表"""

    def get_or_create_progress(self, player_id: str, quest_id: str) -> QuestProgress:
        """获取或创建任务进度"""

    def update_progress(self, player_id: str, quest_type: str, delta: int = 1) -> bool:
        """更新任务进度"""

    def complete_quest(self, player_id: str, quest_id: str) -> QuestReward:
        """完成任务并返回奖励"""

    def claim_reward(self, player_id: str, quest_id: str) -> dict:
        """领取任务奖励"""

    def should_refresh_daily(self, player_id: str) -> bool:
        """检查是否需要刷新日常任务"""
```

### 步骤 3：活动管理器

**文件**: `vibehub/src/core/event.py`

创建 `EventManager` 类：

```python
class EventManager:
    """活动管理器"""

    def get_active_events(self) -> list[GameEvent]:
        """获取当前活跃的活动"""

    def get_event_effects(self, event_type: str) -> dict:
        """获取活动效果配置"""

    def apply_event_effects(self, base_reward: VibeReward) -> VibeReward:
        """应用活动效果到奖励"""
```

### 步骤 4：任务 API

**文件**: `vibehub/src/api/quest.py`

创建 FastAPI 路由，实现以下端点：

1. `GET /api/quest/daily` - 获取日常任务
2. `GET /api/quest/{quest_id}/progress` - 获取任务进度
3. `POST /api/quest/{quest_id}/complete` - 完成任务
4. `GET /api/quest/available` - 获取可接受任务

### 步骤 5：活动 API

**文件**: `vibehub/src/api/event.py`

创建 FastAPI 路由，实现：

1. `GET /api/event/active` - 获取活跃活动
2. `GET /api/event/{event_id}` - 获取活动详情

### 步骤 6：路由注册

**文件**: `vibehub/src/api/__init__.py`

添加路由导入和导出：
```python
from .quest import router as quest_router
from .event import router as event_router
```

**文件**: `vibehub/src/main.py`

注册新路由：
```python
from src.api.quest import router as quest_router
from src.api.event import router as event_router

app.include_router(quest_router)
app.include_router(event_router)
```

## 八、测试计划

### 单元测试文件

**文件**: `vibehub/tests/test_quest_manager.py`

测试用例：
1. `test_get_daily_quests` - 测试获取日常任务
2. `test_update_progress` - 测试进度更新
3. `test_complete_quest` - 测试任务完成
4. `test_claim_reward` - 测试奖励领取
5. `test_daily_refresh` - 测试日常刷新

**文件**: `vibehub/tests/test_event_manager.py`

测试用例：
1. `test_get_active_events` - 测试获取活跃活动
2. `test_apply_event_effects` - 测试效果应用
3. `test_expired_events` - 测试过期活动

**文件**: `vibehub/tests/test_quest_api.py`

测试用例：
1. `test_get_daily_quests` - 测试 API 端点
2. `test_get_progress` - 测试进度查询
3. `test_complete_quest` - 测试完成任务
4. `test_claim_reward` - 测试领取奖励

**文件**: `vibehub/tests/test_event_api.py`

测试用例：
1. `test_get_active_events` - 测试活动列表 API
2. `test_get_event_detail` - 测试活动详情 API

## 九、验收标准

- [ ] 数据模型创建完成（Quest, QuestProgress, GameEvent）
- [ ] 任务管理器实现完成
- [ ] 活动管理器实现完成
- [ ] 任务 API 端点实现（4个端点）
- [ ] 活动 API 端点实现（2个端点）
- [ ] 路由注册完成
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 所有测试通过
- [ ] 代码通过 ruff check 和 mypy 检查
- [ ] API 端点可通过 curl/Postman 测试

## 十、文件位置总结

| 模块 | 文件路径 |
|------|----------|
| 数据模型 | `vibehub/src/storage/models.py` |
| 任务管理器 | `vibehub/src/core/quest.py` |
| 活动管理器 | `vibehub/src/core/event.py` |
| 任务 API | `vibehub/src/api/quest.py` |
| 活动 API | `vibehub/src/api/event.py` |
| 路由注册 | `vibehub/src/api/__init__.py`, `vibehub/src/main.py` |
| 单元测试 | `vibehub/tests/test_quest_manager.py` 等 |
