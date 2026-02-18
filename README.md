# Happy Vibe 🎮

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/user/Happy-Vibe/releases)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![Godot](https://img.shields.io/badge/godot-4.2+-purple.svg)](https://godotengine.org)
[![Tests](https://img.shields.io/badge/tests-639%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-82.74%25-yellow.svg)]()

将 Vibe-Coding 体验游戏化的开放世界养成游戏。通过真实的编程活动，建设你的虚拟家园。

## 特性

- **编程即游戏** - 你的 Claude Code 编程活动自动转化为游戏内能量和奖励
- **农场养成** - 种植代码作物，建造梦想工作室
- **成就系统** - 解锁成就，收集勋章，展示你的编程旅程
- **社交互动** - 好友系统、公会、排行榜，与其他开发者竞技
- **PVP 竞技场** - ELO 匹配系统，实时对战
- **任务系统** - 日常/周常任务，成就任务
- **季节系统** - 50 级通行证，季节专属奖励
- **装饰系统** - 33 种装饰物，打造个性化农场

## 系统要求

- Python 3.11+
- Godot Engine 4.2+ (游戏客户端)
- Windows / macOS / Linux

## 快速开始

### 方式一：使用启动脚本 (推荐)

```bash
# Windows
scripts\run_all.bat

# Linux/macOS
./scripts/run_all.sh
```

### 方式二：手动启动

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/Happy-Vibe.git
cd Happy-Vibe
```

#### 2. 启动 VibeHub 服务

```bash
cd vibehub
uv venv
uv pip install -e ".[dev]"
python -m src.main
```

服务运行在 http://127.0.0.1:8765

#### 3. 启动桌面监控器 (可选)

```bash
cd monitor
uv venv
uv pip install -e ".[dev]"
happy-vibe-monitor
```

#### 4. 运行游戏客户端

使用 Godot Engine 打开 `game/project.godot`，点击运行。

或下载预编译版本：[Releases](https://github.com/user/Happy-Vibe/releases)

## 项目结构

```
Happy-Vibe/
├── vibehub/          # 本地服务 (FastAPI)
├── game/             # 游戏客户端 (Godot 4.2)
├── monitor/          # 桌面监控器
├── scripts/          # 启动脚本
├── docs/             # 文档
└── Note/             # 设计文档
```

## API 端点

| 端点 | 描述 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /api/player/{id}` | 获取玩家信息 |
| `POST /api/activity` | 提交编程活动 |
| `GET /api/farm/{player_id}` | 获取农场数据 |
| `GET /api/achievements` | 获取成就列表 |
| `GET /api/leaderboard` | 排行榜 |
| `GET /api/quests` | 任务列表 |
| `GET /api/guild` | 公会信息 |
| `POST /api/pvp/match` | PVP 匹配 |

完整 API 文档：启动服务后访问 http://127.0.0.1:8765/docs

## 文档

- [用户指南](docs/user-guide.md) - 安装和使用说明
- [开发者指南](docs/developer-guide.md) - 架构和开发规范
- [贡献指南](CONTRIBUTING.md) - 如何参与贡献
- [更新日志](CHANGELOG.md) - 版本变更记录

## 技术栈

| 组件 | 技术 |
|------|------|
| 游戏引擎 | Godot 4.2 (GDScript) |
| 后端服务 | FastAPI (Python) |
| 数据库 | SQLite |
| 通信协议 | HTTP + WebSocket |

## 测试

```bash
cd vibehub
pytest tests/ -v --cov=src
```

当前状态：639 测试通过，82.74% 覆盖率

## 许可证

MIT License

## 致谢

灵感来源于《星露谷物语》的温馨养成机制，献给所有热爱 Vibe-Coding 的开发者。
