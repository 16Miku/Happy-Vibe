# Changelog

本文件记录 Happy Vibe 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-02-18

### 新增

#### 核心系统
- VibeHub 本地服务 (FastAPI)
  - 健康检查 API
  - 玩家管理 API
  - 活动追踪 API
  - 农场系统 API
  - 成就系统 API
  - 好友系统 API
  - 公会系统 API
  - 排行榜 API
  - PVP 竞技场 API
  - 任务系统 API
  - 活动系统 API
  - 商店和市场 API
  - 拍卖系统 API

#### 游戏客户端 (Godot 4.2)
- 主菜单场景
- 游戏世界场景
- 农场系统
  - 种植/收获机制
  - 作物生长系统
  - 品质计算
- HUD 系统
  - 能量条显示
  - 经验值/等级显示
  - 货币显示
  - 心流状态指示器
  - 通知系统
- 新手引导系统 (7 步引导流程)
- 成就面板
- 公会面板
- 排行榜面板
- PVP 竞技场面板
- 任务系统
  - 日常任务
  - 周常任务
  - 成就任务
- 装饰系统 (33 种装饰物)
- 季节系统 (50 级通行证)

#### 桌面监控器
- 系统托盘应用
- Claude Code 日志监控
- 自动活动检测
- 状态通知

#### 数据采集
- Claude Code 日志适配器
- 能量计算算法
- 心流状态检测
- 质量评分系统

### 技术特性
- 639 个单元测试，100% 通过率
- 82.74% 代码覆盖率
- E2E 端到端测试
- 性能测试 (API 响应 < 100ms)
- 完整的 API 文档 (OpenAPI)

### 资源
- 83 张游戏精灵
- 10 个音效文件
- 16 个托盘图标
- 4 个启动脚本

---

## [0.1.0] - 2026-02-14

### 新增
- 项目初始化
- 基础架构搭建
- VibeHub 服务框架
- Godot 项目框架

[1.0.0]: https://github.com/user/Happy-Vibe/releases/tag/v1.0.0
[0.1.0]: https://github.com/user/Happy-Vibe/releases/tag/v0.1.0
