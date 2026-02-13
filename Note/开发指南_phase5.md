# Phase 5 - 任务活动系统开发文档

## 概述
实现游戏内的任务/活动系统，为玩家提供日常目标和奖励机制。

## 功能模块

### 1. 日常任务系统
- 每日签到奖励
- 编程 N 分钟任务
- 提交 N 个作物任务
- 收获 N 个作物任务

### 2. 成就任务系统
- 解锁 X 个成就
- 获得 Y 金币
- 种植 Z 种作物

### 3. 限时活动系统
- 双倍经验活动
- 特殊作物活动
- 节日主题活动

## API 端点

### 日常任务 API
- `GET /api/quest/daily` - 获取日常任务列表
- `GET /api/quest/{id}/progress` - 查询任务进度
- `POST /api/quest/{id}/complete` - 完成任务

### 活动 API
- `GET /api/activity/active` - 获取当前活动

## 数据库模型

### Quest
- `quest_id`: str - 唯一标识
- `quest_type`: str - 任务类型
- `title`: str - 任务标题
- `description`: str - 任务描述
- `reward`: dict - 奖励配置
- `target_value`: int - 目标值
- `daily_refresh`: bool - 是否每日刷新

### QuestProgress
- `progress_id`: str - 进度 ID
- `current_value`: int - 当前进度
- `completed`: bool - 是否完成
- `last_refresh_time`: datetime - 最后刷新时间

### Activity
- `activity_id`: str - 活动 ID
- `activity_type`: str - 活动类型
- `start_time`: datetime - 开始时间
- `end_time`: datetime - 结束时间
- `multiplier`: float - 经验倍数

## 实现步骤

### 第一步：数据模型
创建 `src/storage/models.py` 中添加：
- Quest 类
- QuestType 枚丼
- QuestProgress 类

### 第二步：任务 API
创建 `src/api/quest.py`：
- 任务列表查询
- 任务详情获取
- 任务完成提交

### 第三步：任务管理器
创建 `src/core/quest.py`：
- 任务生成逻辑
- 奖励发放逻辑
- 任务验证逻辑

### 第四步：活动系统
扩展 `src/core/activity.py`：
- 限时活动配置
- 活动状态管理
- 特殊奖励计算

## 验收标准
- [ ] 数据模型创建完成
- [ ] 任务 API 实现完成
- [ ] 任务管理器完成
- [ ] 单元测试通过 (覆盖率 ≥ 80%)
- [ ] 功能测试验证
