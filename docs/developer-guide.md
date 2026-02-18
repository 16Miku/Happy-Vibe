# Happy Vibe 开发者指南

## 目录

- [项目架构](#项目架构)
- [开发环境配置](#开发环境配置)
- [代码规范](#代码规范)
- [模块说明](#模块说明)
- [API 文档](#api-文档)
- [测试指南](#测试指南)

---

## 项目架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Happy Vibe 架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │ 游戏客户端   │────│  VibeHub    │────│  数据采集    │   │
│  │ (Godot)     │     │  (FastAPI)  │     │  (Adapters) │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│        │                   │                   │            │
│        ▼                   ▼                   ▼            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │  GDScript   │     │   SQLite    │     │ Claude Code │   │
│  │  场景/UI    │     │   数据库    │     │   日志      │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构

```
Happy-Vibe/
├── vibehub/                    # VibeHub 本地服务
│   ├── src/
│   │   ├── api/                # API 路由
│   │   │   ├── player.py       # 玩家 API
│   │   │   ├── activity.py     # 活动 API
│   │   │   ├── farm.py         # 农场 API
│   │   │   ├── achievement.py  # 成就 API
│   │   │   ├── guild.py        # 公会 API
│   │   │   ├── pvp.py          # PVP API
│   │   │   └── ...
│   │   ├── core/               # 核心逻辑
│   │   │   ├── energy_calculator.py
│   │   │   ├── flow_detector.py
│   │   │   └── quality_scorer.py
│   │   ├── adapters/           # 数据源适配器
│   │   │   ├── base.py
│   │   │   └── claude_code.py
│   │   ├── storage/            # 存储层
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   └── multiplayer/        # 多人系统
│   └── tests/                  # 测试文件
│
├── game/                       # Godot 游戏客户端
│   ├── scenes/                 # 场景文件
│   ├── scripts/                # GDScript 脚本
│   └── assets/                 # 资源文件
│
├── monitor/                    # 桌面监控器
│   └── src/
│
└── docs/                       # 文档
```

---

## 开发环境配置

### 必需工具

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 后端开发 |
| uv | 最新 | Python 包管理 |
| Godot | 4.2+ | 游戏开发 |
| Git | 最新 | 版本控制 |

### 后端环境 (vibehub)

```bash
# 1. 进入目录
cd vibehub

# 2. 创建虚拟环境
uv venv

# 3. 安装依赖 (包括开发依赖)
uv pip install -e ".[dev]"

# 4. 验证安装
python -c "import fastapi; print('OK')"
```

### 游戏客户端 (game)

1. 下载 [Godot Engine 4.2+](https://godotengine.org/download)
2. 打开 Godot，选择 "Import" 导入 `game/project.godot`
3. 等待资源导入完成

### 监控器 (monitor)

```bash
cd monitor
uv venv
uv pip install -e ".[dev]"
```

---

## 代码规范

### Python 代码规范

使用 `ruff` 进行代码检查和格式化。

```bash
# 格式化代码
ruff format src/

# 检查代码
ruff check src/ --fix

# 类型检查
mypy src/
```

#### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `EnergyCalculator` |
| 函数名 | snake_case | `calculate_energy` |
| 常量 | UPPER_CASE | `MAX_ENERGY` |
| 私有成员 | _前缀 | `_internal_state` |

#### 文档字符串 (Google 风格)

```python
def calculate_energy(duration: int, quality: float) -> int:
    """计算编程活动产生的能量。

    Args:
        duration: 编程时长（分钟）
        quality: 代码质量评分 (0.0-1.0)

    Returns:
        计算得到的能量值

    Raises:
        ValueError: 当 duration 为负数时
    """
    if duration < 0:
        raise ValueError("duration must be non-negative")
    return int(duration * quality * 10)
```

### GDScript 代码规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `PlayerController` |
| 函数名 | snake_case | `move_player` |
| 常量 | UPPER_CASE | `MAX_SPEED` |
| 信号 | snake_case | `health_changed` |
| 私有变量 | _前缀 | `_velocity` |

```gdscript
class_name PlayerController
extends CharacterBody2D

signal health_changed(new_health: int)

const MAX_SPEED := 200.0

var _velocity := Vector2.ZERO
var health := 100

func _physics_process(delta: float) -> void:
    _handle_input()
    move_and_slide()

func _handle_input() -> void:
    var input_dir := Input.get_vector("left", "right", "up", "down")
    _velocity = input_dir * MAX_SPEED
    velocity = _velocity
```

---

## 模块说明

### 核心模块 (core/)

#### EnergyCalculator

计算编程活动产生的能量。

```python
from src.core.energy_calculator import EnergyCalculator

calculator = EnergyCalculator()
energy = calculator.calculate(
    duration_minutes=60,
    quality_score=0.8,
    flow_multiplier=2.0
)
```

#### FlowDetector

检测用户的心流状态。

```python
from src.core.flow_detector import FlowDetector

detector = FlowDetector()
state = detector.detect(activity_history)
# 返回: "normal" | "focused" | "flow" | "super_flow"
```

### 适配器模块 (adapters/)

#### 基类接口

```python
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    @abstractmethod
    async def get_activities(self, since: datetime) -> list[Activity]:
        """获取指定时间后的活动记录"""
        pass

    @abstractmethod
    async def start_monitoring(self) -> None:
        """开始监控"""
        pass
```

#### Claude Code 适配器

```python
from src.adapters.claude_code import ClaudeCodeAdapter

adapter = ClaudeCodeAdapter(log_path="~/.claude/logs/")
activities = await adapter.get_activities(since=datetime.now() - timedelta(hours=1))
```

### API 模块 (api/)

所有 API 使用 FastAPI 实现，支持自动生成 OpenAPI 文档。

```python
from fastapi import APIRouter, Depends
from src.api.schemas import PlayerResponse

router = APIRouter(prefix="/api/player", tags=["player"])

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: str):
    """获取玩家信息"""
    ...
```

---

## API 文档

### 启动服务后访问

- Swagger UI: http://127.0.0.1:8765/docs
- ReDoc: http://127.0.0.1:8765/redoc

### 主要端点

#### 玩家 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/player/{id}` | 获取玩家信息 |
| POST | `/api/player` | 创建玩家 |
| PUT | `/api/player/{id}` | 更新玩家 |

#### 活动 API

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/activity` | 提交活动 |
| GET | `/api/activity/history` | 获取活动历史 |

#### 农场 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/farm/{player_id}` | 获取农场数据 |
| POST | `/api/farm/plant` | 种植作物 |
| POST | `/api/farm/harvest` | 收获作物 |

#### 社交 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/friends` | 好友列表 |
| POST | `/api/friends/request` | 发送好友请求 |
| GET | `/api/guild/{id}` | 公会信息 |
| GET | `/api/leaderboard` | 排行榜 |

---

## 测试指南

### 运行测试

```bash
cd vibehub

# 运行所有测试
pytest tests/ -v

# 运行并生成覆盖率报告
pytest tests/ -v --cov=src --cov-report=term-missing

# 运行特定测试文件
pytest tests/test_energy_calculator.py -v

# 运行特定测试函数
pytest tests/test_energy_calculator.py::test_calculate_basic -v
```

### 测试规范

```python
# tests/test_energy_calculator.py

import pytest
from src.core.energy_calculator import EnergyCalculator

class TestEnergyCalculator:
    """能量计算器测试"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.calculator = EnergyCalculator()

    def test_calculate_basic(self):
        """测试基础能量计算"""
        result = self.calculator.calculate(duration_minutes=60)
        assert result > 0

    def test_calculate_with_quality(self):
        """测试带质量加成的计算"""
        result = self.calculator.calculate(
            duration_minutes=60,
            quality_score=0.9
        )
        assert result > 60  # 应该有加成

    def test_calculate_zero_duration(self):
        """测试零时长返回零"""
        result = self.calculator.calculate(duration_minutes=0)
        assert result == 0

    def test_calculate_negative_duration_raises(self):
        """测试负时长抛出异常"""
        with pytest.raises(ValueError):
            self.calculator.calculate(duration_minutes=-1)
```

### 覆盖率要求

| 模块类型 | 最低覆盖率 |
|----------|------------|
| 核心模块 | 80% |
| API 模块 | 70% |
| 其他模块 | 60% |

---

## 调试技巧

### 后端调试

```bash
# 启用调试模式
DEBUG=1 python -m src.main

# 查看详细日志
LOG_LEVEL=DEBUG python -m src.main
```

### 数据库调试

```python
# 查看 SQLite 数据库
import sqlite3
conn = sqlite3.connect("vibehub.db")
cursor = conn.execute("SELECT * FROM players")
for row in cursor:
    print(row)
```

### API 调试

使用 httpx 或 curl 测试 API：

```bash
# 健康检查
curl http://127.0.0.1:8765/health

# 获取玩家
curl http://127.0.0.1:8765/api/player/1
```

---

## 相关链接

- [用户指南](user-guide.md)
- [贡献指南](../CONTRIBUTING.md)
- [设计文档](../Note/Spec-Driven-Development.md)
