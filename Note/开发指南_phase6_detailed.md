# Phase 6 - 运营/优化系统开发文档

## 一、概述

Phase 6 是 Happy Vibe 的长期运营阶段，旨在通过持续的内容更新、竞技玩法和社交互动来保持玩家活跃度。该阶段包含以下核心功能模块：
- 成就系统完善：50+ 成就定义与奖励系统
- 公会战系统：团队竞技与协作玩法
- 排行榜与赛季：实时竞技排名系统
- PVP 竞技场：玩家对战与观战功能
- 数据分析与运营工具：运营决策支持

## 二、项目背景

Happy Vibe 经过 Phase 0-5 的开发，已完成核心功能：
- ✅ Phase 0: 项目初始化
- ✅ Phase 1: 技术验证（VibeHub、能量计算、心流检测）
- ✅ Phase 2: MVP核心（玩家系统、农场、种植）
- ✅ Phase 3: 社交扩展（好友、签到、联机）
- ✅ Phase 4: 经济生态（商店、市场、拍卖）
- ✅ Phase 5.5: 任务活动系统

Phase 6 的目标是：
1. 完善长期留存机制（成就系统）
2. 增强社交竞技维度（公会战、排行榜）
3. 提供持续的更新内容（赛季系统）
4. 建立运营数据基础（数据分析工具）

## 三、技术栈

### 3.1 后端技术

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| **框架** | FastAPI 0.115+ | 高性能异步 Web 框架 |
| **数据库** | SQLite 3.45+ | 本地开发（生产可迁移至 PostgreSQL） |
| **ORM** | SQLAlchemy 2.0+ | 数据库抽象层 |
| **缓存** | Redis（可选） | 热点数据缓存 |
| **任务队列** | Celery / asyncio | 异步任务处理 |

### 3.2 前端技术（Godot）

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| **引擎** | Godot 4.2+ | 跨平台游戏引擎 |
| **脚本** | GDScript 2.0 | 官方脚本语言 |
| **网络** | HTTPRequest + WebSocket | 与 VibeHub 通信 |

### 3.3 数据分析

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| **数据处理** | Pandas | 数据分析 |
| **可视化** | Matplotlib / Plotly | 报表生成 |
| **导出** | OpenPyXL | Excel 报表 |

## 四、功能模块详细设计

### 4.1 成就系统完善

#### 4.1.1 成就分类

```
成就系统分类架构：
├── 编程成就
│   ├── 初级程序员（完成10次编程活动）
│   ├── 代码大师（累计编程100小时）
│   ├── 心流达人（进入心流状态50次）
│   └── 全栈开发者（完成所有类型的编程任务）
│
├── 农场成就
│   ├── 播种希望（种植100株作物）
│   ├── 丰收庆典（收获1000株作物）
│   ├── 品质追求者（收获100株⭐⭐⭐以上作物）
│   └── 农场大亨（解锁所有地块）
│
├── 社交成就
│   ├── 社交新星（添加10个好友）
│   ├── 乐于助人（帮助好友浇水50次）
│   ├── 社区领袖（创建公会）
│   └── 人气之星（获得100个点赞）
│
├── 经济成就
│   ├── 第一桶金（累计获得10000金币）
│   ├── 交易达人（完成100次交易）
│   ├── 拍卖之王（赢得50次拍卖）
│   └── 百万富翁（拥有100万金币）
│
└── 特殊成就
    ├── 早起鸟（连续7天在早上8点前完成活动）
    ├── 夜猫子（连续7天在晚上11点后完成活动）
    ├── 完美主义者（一天内完成所有日常任务）
    └── 幸运儿（获得传说品质作物）
```

#### 4.1.2 成就数据模型

```python
# vibehub/src/storage/models.py

class Achievement(Base):
    """成就定义表"""
    __tablename__ = "achievements"

    achievement_id = Column(String, primary_key=True)
    category = Column(String, nullable=False)  # 编程/农场/社交/经济/特殊
    tier = Column(String, nullable=False)       # 普通/稀有/史诗/传说

    # 成就信息
    title = Column(String, nullable=False)
    title_zh = Column(String, nullable=False)
    description = Column(Text)
    icon = Column(String)  # 成就图标路径

    # 解锁条件
    requirement_type = Column(String)  # count/sum/max/min/combination
    requirement_param = Column(JSON)   # 条件参数

    # 奖励
    reward_json = Column(JSON)  # {energy, gold, exp, diamonds, items}
    exp_reward = Column(Integer, default=0)

    # 显示
    display_order = Column(Integer, default=0)
    is_hidden = Column(Boolean, default=False)  # 隐藏成就
    is_secret = Column(Boolean, default=False)  # 解锁前不显示内容

    # 元数据
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    progress_records = relationship("AchievementProgress", back_populates="achievement")


class AchievementProgress(Base):
    """玩家成就进度表"""
    __tablename__ = "achievement_progress"

    progress_id = Column(String, primary_key=True)
    player_id = Column(String, ForeignKey("players.player_id"), nullable=False)
    achievement_id = Column(String, ForeignKey("achievements.achievement_id"), nullable=False)

    # 进度数据
    current_value = Column(Integer, default=0)  # 当前进度值
    target_value = Column(Integer, default=1)    # 目标值
    progress_percent = Column(Integer, default=0)  # 进度百分比

    # 状态
    is_unlocked = Column(Boolean, default=False)   # 已解锁
    is_completed = Column(Boolean, default=False)  # 已完成
    is_claimed = Column(Boolean, default=False)    # 已领取奖励

    # 时间记录
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    claimed_at = Column(DateTime)

    # 元数据
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    player = relationship("Player", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="progress_records")

    __table_args__ = (
        UniqueConstraint('player_id', 'achievement_id', name='uq_player_achievement'),
        Index('idx_achievement_player', 'player_id', 'is_completed'),
    )
```

#### 4.1.3 成就管理器

```python
# vibehub/src/core/achievement_manager.py

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_

from src.storage.models import Achievement, AchievementProgress, Player
from src.storage.database import get_db


class AchievementManager:
    """成就系统管理器"""

    def __init__(self, db_session):
        self.db = db_session

    async def get_player_achievements(
        self,
        player_id: str,
        category: Optional[str] = None,
        include_hidden: bool = False,
        include_completed: bool = True
    ) -> List[dict]:
        """获取玩家的成就列表

        Args:
            player_id: 玩家ID
            category: 成就分类过滤
            include_hidden: 是否包含隐藏成就
            include_completed: 是否包含已完成成就

        Returns:
            成就列表
        """
        query = select(Achievement).outerjoin(
            AchievementProgress,
            and_(
                AchievementProgress.player_id == player_id,
                AchievementProgress.achievement_id == Achievement.achievement_id
            )
        )

        if not include_hidden:
            query = query.where(Achievement.is_hidden == False)

        if category:
            query = query.where(Achievement.category == category)

        query = query.order_by(Achievement.display_order, Achievement.tier)

        result = await self.db.execute(query)
        achievements = result.scalars().all()

        # 构建返回数据
        achievement_list = []
        for ach in achievements:
            # 查找进度
            progress = await self._get_player_progress(player_id, ach.achievement_id)

            data = {
                "achievement_id": ach.achievement_id,
                "category": ach.category,
                "tier": ach.tier,
                "title": ach.title_zh if ach.title_zh else ach.title,
                "description": ach.description,
                "icon": ach.icon,
                "current_value": progress.current_value if progress else 0,
                "target_value": ach.requirement_param.get("target", 1) if ach.requirement_param else 1,
                "progress_percent": progress.progress_percent if progress else 0,
                "is_unlocked": progress.is_unlocked if progress else False,
                "is_completed": progress.is_completed if progress else False,
                "is_claimed": progress.is_claimed if progress else False,
                "reward": ach.reward_json,
                "display_order": ach.display_order,
            }

            # 隐藏成就处理
            if ach.is_hidden and not data["is_unlocked"]:
                data["title"] = "???"
                data["description"] = "继续探索以解锁此成就"
                data["reward"] = None

            achievement_list.append(data)

        return achievement_list

    async def update_progress(
        self,
        player_id: str,
        event_type: str,
        event_data: dict
    ) -> List[dict]:
        """更新成就进度

        Args:
            player_id: 玩家ID
            event_type: 事件类型
            event_data: 事件数据

        Returns:
            新解锁或完成的成就列表
        """
        # 获取所有相关的成就定义
        query = select(Achievement).where(
            Achievement.requirement_type == event_type
        )
        result = await self.db.execute(query)
        achievements = result.scalars().all()

        unlocked_or_completed = []

        for achievement in achievements:
            # 获取或创建进度记录
            progress = await self._get_or_create_progress(player_id, achievement.achievement_id)

            if progress.is_completed:
                continue

            # 检查是否满足解锁条件
            if not progress.is_unlocked:
                if await self._check_unlock_condition(player_id, achievement):
                    progress.is_unlocked = True
                    progress.started_at = datetime.utcnow()
                    unlocked_or_completed.append({
                        "achievement_id": achievement.achievement_id,
                        "event": "unlocked",
                        "title": achievement.title_zh,
                    })

            # 更新进度
            if progress.is_unlocked and not progress.is_completed:
                new_value = await self._calculate_new_value(player_id, achievement, event_data)
                old_value = progress.current_value
                progress.current_value = new_value

                # 计算进度百分比
                target = achievement.requirement_param.get("target", 1)
                progress.progress_percent = min(int((new_value / target) * 100), 100)

                # 检查是否完成
                if new_value >= target:
                    progress.is_completed = True
                    progress.completed_at = datetime.utcnow()
                    unlocked_or_completed.append({
                        "achievement_id": achievement.achievement_id,
                        "event": "completed",
                        "title": achievement.title_zh,
                        "reward": achievement.reward_json,
                    })

        await self.db.commit()
        return unlocked_or_completed

    async def claim_reward(
        self,
        player_id: str,
        achievement_id: str
    ) -> dict:
        """领取成就奖励

        Args:
            player_id: 玩家ID
            achievement_id: 成就ID

        Returns:
            奖励信息
        """
        progress = await self._get_player_progress(player_id, achievement_id)

        if not progress or not progress.is_completed:
            raise ValueError("成就未完成")

        if progress.is_claimed:
            raise ValueError("奖励已领取")

        # 获取成就定义
        achievement = await self.db.get(Achievement, achievement_id)
        reward = achievement.reward_json

        # 发放奖励（调用玩家系统）
        # TODO: 整合 PlayerSystem 进行奖励发放

        progress.is_claimed = True
        progress.claimed_at = datetime.utcnow()
        await self.db.commit()

        return {
            "achievement_id": achievement_id,
            "reward": reward,
            "claimed_at": progress.claimed_at.isoformat(),
        }

    async def _get_player_progress(
        self,
        player_id: str,
        achievement_id: str
    ) -> Optional[AchievementProgress]:
        """获取玩家成就进度"""
        query = select(AchievementProgress).where(
            and_(
                AchievementProgress.player_id == player_id,
                AchievementProgress.achievement_id == achievement_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_or_create_progress(
        self,
        player_id: str,
        achievement_id: str
    ) -> AchievementProgress:
        """获取或创建成就进度"""
        progress = await self._get_player_progress(player_id, achievement_id)

        if not progress:
            progress = AchievementProgress(
                progress_id=f"{player_id}_{achievement_id}",
                player_id=player_id,
                achievement_id=achievement_id,
                current_value=0,
                target_value=1,
                progress_percent=0,
            )
            self.db.add(progress)
            await self.db.flush()

        return progress

    async def _check_unlock_condition(
        self,
        player_id: str,
        achievement: Achievement
    ) -> bool:
        """检查成就解锁条件"""
        # 默认自动解锁
        if not achievement.requirement_param:
            return True

        unlock_conditions = achievement.requirement_param.get("unlock_conditions")
        if not unlock_conditions:
            return True

        # TODO: 实现复杂的解锁条件检查
        return True

    async def _calculate_new_value(
        self,
        player_id: str,
        achievement: Achievement,
        event_data: dict
    ) -> int:
        """计算新的进度值"""
        # 根据事件类型和成就要求计算进度
        # TODO: 实现具体的进度计算逻辑
        return 0
```

### 4.2 公会战系统

#### 4.2.1 公会数据模型

```python
# vibehub/src/storage/models.py

class Guild(Base):
    """公会表"""
    __tablename__ = "guilds"

    guild_id = Column(String, primary_key=True)
    guild_name = Column(String, unique=True, nullable=False)
    guild_name_zh = Column(String, nullable=False)

    # 公会信息
    leader_id = Column(String, ForeignKey("players.player_id"))
    description = Column(Text)
    icon = Column(String)
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)

    # 成员统计
    member_count = Column(Integer, default=1)
    max_members = Column(Integer, default=20)

    # 公会资源
    contribution_points = Column(Integer, default=0)  # 贡献点
    guild_funds = Column(Integer, default=0)           # 公会资金

    # 权限设置
    join_type = Column(String, default="open")  # open/closed/invite_only
    min_level = Column(Integer, default=1)

    # 时间记录
    created_at = Column(DateTime, server_default=func.now())
    disbanded_at = Column(DateTime, nullable=True)

    # 关系
    leader = relationship("Player", foreign_keys=[leader_id])
    members = relationship("GuildMember", back_populates="guild")
    war_participations = relationship("GuildWar", back_populates="guilds")


class GuildMember(Base):
    """公会成员表"""
    __tablename__ = "guild_members"

    membership_id = Column(String, primary_key=True)
    guild_id = Column(String, ForeignKey("guilds.guild_id"), nullable=False)
    player_id = Column(String, ForeignKey("players.player_id"), nullable=False)

    # 角色与权限
    role = Column(String, default="member")  # leader/officer/member
    title = Column(String)  # 自定义头衔

    # 贡献数据
    contribution_points = Column(Integer, default=0)
    weekly_contribution = Column(Integer, default=0)

    # 状态
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, server_default=func.now())
    left_at = Column(DateTime, nullable=True)

    # 关系
    guild = relationship("Guild", back_populates="members")
    player = relationship("Player", back_populates="guild_membership")


class GuildWar(Base):
    """公会战表"""
    __tablename__ = "guild_wars"

    war_id = Column(String, primary_key=True)
    war_name = Column(String, nullable=False)
    war_type = Column(String, default="territory")  # territory/resource/honor

    # 对战双方
    guild_a_id = Column(String, ForeignKey("guilds.guild_id"))
    guild_b_id = Column(String, ForeignKey("guilds.guild_id"))

    # 战况
    score_a = Column(Integer, default=0)
    score_b = Column(Integer, default=0)
    target_score = Column(Integer, default=1000)

    # 状态
    status = Column(String, default="preparing")  # preparing/active/finished
    winner_id = Column(String, ForeignKey("guilds.guild_id"), nullable=True)

    # 时间
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    duration_hours = Column(Integer, default=24)

    # 奖励
    reward_pool = Column(JSON)  # 胜利方奖励

    # 关系
    guild_a = relationship("Guild", foreign_keys=[guild_a_id])
    guild_b = relationship("Guild", foreign_keys=[guild_b_id])
    winner = relationship("Guild", foreign_keys=[winner_id])
    participants = relationship("GuildWarParticipant", back_populates="war")


class GuildWarParticipant(Base):
    """公会战参与记录"""
    __tablename__ = "guild_war_participants"

    participation_id = Column(String, primary_key=True)
    war_id = Column(String, ForeignKey("guild_wars.war_id"), nullable=False)
    player_id = Column(String, ForeignKey("players.player_id"), nullable=False)
    guild_id = Column(String, ForeignKey("guilds.guild_id"), nullable=False)

    # 个人贡献
    score = Column(Integer, default=0)
    battles_won = Column(Integer, default=0)
    damage_dealt = Column(Integer, default=0)

    # 奖励
    personal_reward_claimed = Column(Boolean, default=False)

    # 关系
    war = relationship("GuildWar", back_populates="participants")
    player = relationship("Player")
    guild = relationship("Guild")
```

#### 4.2.2 公会战管理器

```python
# vibehub/src/core/guild_war_manager.py

class GuildWarManager:
    """公会战管理器"""

    def __init__(self, db_session):
        self.db = db_session

    async def create_war(
        self,
        guild_a_id: str,
        guild_b_id: str,
        war_type: str = "territory",
        duration_hours: int = 24
    ) -> dict:
        """创建公会战

        Args:
            guild_a_id: 公会A ID
            guild_b_id: 公会B ID
            war_type: 战争类型
            duration_hours: 持续时间（小时）

        Returns:
            战争信息
        """
        war_id = f"war_{uuid.uuid4().hex[:8]}"

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=duration_hours)

        war = GuildWar(
            war_id=war_id,
            war_name=f"公会战 {start_time.strftime('%Y%m%d')}",
            war_type=war_type,
            guild_a_id=guild_a_id,
            guild_b_id=guild_b_id,
            start_time=start_time,
            end_time=end_time,
            duration_hours=duration_hours,
            status="preparing"
        )

        self.db.add(war)
        await self.db.commit()

        return await self.get_war_info(war_id)

    async def start_war(self, war_id: str) -> dict:
        """开始公会战"""
        war = await self.db.get(GuildWar, war_id)
        if not war:
            raise ValueError("战争不存在")

        if war.status != "preparing":
            raise ValueError("战争状态不正确")

        war.status = "active"
        await self.db.commit()

        return await self.get_war_info(war_id)

    async def update_score(
        self,
        war_id: str,
        player_id: str,
        score_delta: int
    ) -> dict:
        """更新公会战分数"""
        war = await self.db.get(GuildWar, war_id)
        if not war or war.status != "active":
            raise ValueError("战争不存在或已结束")

        # 获取玩家所属公会
        # TODO: 实现公会归属查询

        # 更新分数
        # TODO: 实现分数更新逻辑

        await self.db.commit()
        return await self.get_war_info(war_id)

    async def end_war(self, war_id: str) -> dict:
        """结束公会战并结算"""
        war = await self.db.get(GuildWar, war_id)
        if not war:
            raise ValueError("战争不存在")

        # 判定胜负
        if war.score_a > war.score_b:
            war.winner_id = war.guild_a_id
        elif war.score_b > war.score_a:
            war.winner_id = war.guild_b_id
        else:
            # 平局处理
            pass

        war.status = "finished"
        war.end_time = datetime.utcnow()

        # 发放奖励
        await self._distribute_rewards(war)

        await self.db.commit()
        return await self.get_war_info(war_id)

    async def get_war_info(self, war_id: str) -> dict:
        """获取公会战信息"""
        war = await self.db.get(GuildWar, war_id)
        if not war:
            raise ValueError("战争不存在")

        return {
            "war_id": war.war_id,
            "war_name": war.war_name,
            "war_type": war.war_type,
            "guild_a": await self._get_guild_info(war.guild_a_id),
            "guild_b": await self._get_guild_info(war.guild_b_id),
            "score_a": war.score_a,
            "score_b": war.score_b,
            "target_score": war.target_score,
            "status": war.status,
            "winner_id": war.winner_id,
            "start_time": war.start_time.isoformat(),
            "end_time": war.end_time.isoformat() if war.end_time else None,
            "reward_pool": war.reward_pool,
        }

    async def _get_guild_info(self, guild_id: str) -> dict:
        """获取公会信息"""
        guild = await self.db.get(Guild, guild_id)
        return {
            "guild_id": guild.guild_id,
            "guild_name": guild.guild_name_zh,
            "level": guild.level,
            "member_count": guild.member_count,
            "contribution_points": guild.contribution_points,
        }

    async def _distribute_rewards(self, war: GuildWar):
        """分发公会战奖励"""
        # TODO: 实现奖励分发逻辑
        pass
```

### 4.3 排行榜与赛季系统

#### 4.3.1 数据模型

```python
# vibehub/src/storage/models.py

class Season(Base):
    """赛季表"""
    __tablename__ = "seasons"

    season_id = Column(String, primary_key=True)
    season_name = Column(String, nullable=False)
    season_number = Column(Integer, nullable=False)

    # 赛季时间
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # 赛季类型
    season_type = Column(String, default="regular")  # regular/special/championship

    # 赛季奖励
    reward_tiers = Column(JSON)  # {rank_start: rank_end: reward}

    # 状态
    is_active = Column(Boolean, default=True)

    # 元数据
    created_at = Column(DateTime, server_default=func.now())


class Leaderboard(Base):
    """排行榜表"""
    __tablename__ = "leaderboards"

    leaderboard_id = Column(String, primary_key=True)
    season_id = Column(String, ForeignKey("seasons.season_id"))
    leaderboard_type = Column(String)  # individual/guild/achievement

    # 排行榜数据（JSON 格式存储，支持灵活查询）
    rankings_json = Column(JSON)  # [{rank, player_id, score, ...}]

    # 更新时间
    last_updated = Column(DateTime, server_default=func.now())
    update_frequency = Column(Integer, default=300)  # 更新频率（秒）

    # 元数据
    created_at = Column(DateTime, server_default=func.now())


class LeaderboardSnapshot(Base):
    """排行榜快照（用于历史记录）"""
    __tablename__ = "leaderboard_snapshots"

    snapshot_id = Column(String, primary_key=True)
    season_id = Column(String, nullable=False)
    snapshot_time = Column(DateTime, server_default=func.now())

    # 快照数据
    rankings_json = Column(JSON)

    # 元数据
    created_at = Column(DateTime, server_default=func.now())
```

#### 4.3.2 排行榜管理器

```python
# vibehub/src/core/leaderboard_manager.py

class LeaderboardManager:
    """排行榜管理器"""

    def __init__(self, db_session):
        self.db = db_session

    async def get_leaderboard(
        self,
        leaderboard_type: str,
        season_id: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """获取排行榜

        Args:
            leaderboard_type: 排行榜类型
            season_id: 赛季ID（可选）
            limit: 返回数量

        Returns:
            排行榜数据
        """
        if not season_id:
            season_id = await self._get_current_season_id()

        # 查询排行榜
        query = select(Leaderboard).where(
            and_(
                Leaderboard.season_id == season_id,
                Leaderboard.leaderboard_type == leaderboard_type
            )
        )

        result = await self.db.execute(query)
        leaderboard = result.scalar_one_or_none()

        if not leaderboard:
            # 生成初始排行榜
            await self._generate_leaderboard(season_id, leaderboard_type)
            return await self.get_leaderboard(leaderboard_type, season_id, limit)

        rankings = leaderboard.rankings_json[:limit]
        return rankings

    async def update_leaderboard(
        self,
        leaderboard_type: str,
        season_id: Optional[str] = None
    ) -> dict:
        """更新排行榜数据"""
        if not season_id:
            season_id = await self._get_current_season_id()

        # 获取当前赛季所有玩家的分数
        rankings = await self._calculate_rankings(leaderboard_type, season_id)

        # 保存排行榜
        query = select(Leaderboard).where(
            and_(
                Leaderboard.season_id == season_id,
                Leaderboard.leaderboard_type == leaderboard_type
            )
        )

        result = await self.db.execute(query)
        leaderboard = result.scalar_one_or_none()

        if not leaderboard:
            leaderboard = Leaderboard(
                leaderboard_id=f"{season_id}_{leaderboard_type}",
                season_id=season_id,
                leaderboard_type=leaderboard_type,
                rankings_json=rankings
            )
            self.db.add(leaderboard)
        else:
            leaderboard.rankings_json = rankings
            leaderboard.last_updated = datetime.utcnow()

        await self.db.commit()

        return {
            "leaderboard_type": leaderboard_type,
            "season_id": season_id,
            "rankings": rankings,
            "last_updated": leaderboard.last_updated.isoformat(),
        }

    async def create_snapshot(
        self,
        season_id: str
    ) -> dict:
        """创建排行榜快照"""
        # 获取当前所有类型的排行榜
        leaderboard_types = ["individual", "guild", "achievement"]

        snapshots = []
        for lb_type in leaderboard_types:
            query = select(Leaderboard).where(
                and_(
                    Leaderboard.season_id == season_id,
                    Leaderboard.leaderboard_type == lb_type
                )
            )
            result = await self.db.execute(query)
            leaderboard = result.scalar_one_or_none()

            if leaderboard:
                snapshot = LeaderboardSnapshot(
                    snapshot_id=f"snapshot_{uuid.uuid4().hex[:8]}",
                    season_id=season_id,
                    rankings_json=leaderboard.rankings_json
                )
                self.db.add(snapshot)
                snapshots.append(snapshot)

        await self.db.commit()

        return {
            "season_id": season_id,
            "snapshot_count": len(snapshots),
            "created_at": datetime.utcnow().isoformat(),
        }

    async def _get_current_season_id(self) -> str:
        """获取当前赛季ID"""
        query = select(Season).where(
            and_(
                Season.is_active == True,
                Season.start_time <= datetime.utcnow(),
                Season.end_time >= datetime.utcnow()
            )
        ).order_by(Season.season_number.desc())

        result = await self.db.execute(query)
        season = result.first()

        if not season:
            # 创建默认赛季
            season = await self._create_default_season()

        return season.season_id

    async def _calculate_rankings(
        self,
        leaderboard_type: str,
        season_id: str
    ) -> List[dict]:
        """计算排行榜排名"""
        # TODO: 根据不同类型计算排名
        return []

    async def _generate_leaderboard(
        self,
        season_id: str,
        leaderboard_type: str
    ):
        """生成初始排行榜"""
        await self.update_leaderboard(leaderboard_type, season_id)

    async def _create_default_season(self) -> Season:
        """创建默认赛季"""
        season_id = f"season_{datetime.utcnow().year}_1"
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=90)  # 3个月一个赛季

        season = Season(
            season_id=season_id,
            season_name=f"S{datetime.utcnow().year}赛季1",
            season_number=1,
            start_time=start_time,
            end_time=end_time,
            season_type="regular"
        )

        self.db.add(season)
        await self.db.commit()

        return season
```

### 4.4 PVP 竞技场系统

#### 4.4.1 数据模型

```python
# vibehub/src/storage/models.py

class PVPMatch(Base):
    """PVP对战记录"""
    __tablename__ = "pvp_matches"

    match_id = Column(String, primary_key=True)
    match_type = Column(String, default="duel")  # duel/arena/tournament

    # 对战双方
    player_a_id = Column(String, ForeignKey("players.player_id"))
    player_b_id = Column(String, ForeignKey("players.player_id"))

    # 对战结果
    winner_id = Column(String, ForeignKey("players.player_id"))
    score_a = Column(Integer, default=0)
    score_b = Column(Integer, default=0)

    # 对战数据
    duration_seconds = Column(Integer)
    moves_a = Column(Integer, default=0)
    moves_b = Column(Integer, default=0)

    # 状态
    status = Column(String, default="waiting")  # waiting/active/finished/cancelled

    # 时间
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # 观战
    spectator_count = Column(Integer, default=0)
    allow_spectate = Column(Boolean, default=True)

    # 关系
    player_a = relationship("Player", foreign_keys=[player_a_id])
    player_b = relationship("Player", foreign_keys=[player_b_id])
    winner = relationship("Player", foreign_keys=[winner_id])
    spectators = relationship("PVPSpectator", back_populates="match")


class PVPSpectator(Base):
    """PVP观战记录"""
    __tablename__ = "pvp_spectators"

    spectator_id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("pvp_matches.match_id"), nullable=False)
    player_id = Column(String, ForeignKey("players.player_id"), nullable=False)

    # 观战时间
    joined_at = Column(DateTime, server_default=func.now())
    left_at = Column(DateTime, nullable=True)

    # 关系
    match = relationship("PVPMatch", back_populates="spectators")
    player = relationship("Player")


class PVPRanking(Base):
    """PVP积分排名"""
    __tablename__ = "pvp_rankings"

    ranking_id = Column(String, primary_key=True)
    season_id = Column(String, ForeignKey("seasons.season_id"), nullable=False)
    player_id = Column(String, ForeignKey("players.player_id"), nullable=False)

    # 积分数据
    rating = Column(Integer, default=1000)  # ELO积分
    max_rating = Column(Integer, default=1000)

    # 对战统计
    matches_played = Column(Integer, default=0)
    matches_won = Column(Integer, default=0)
    matches_lost = Column(Integer, default=0)
    matches_drawn = Column(Integer, default=0)

    # 连胜统计
    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)

    # 元数据
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    season = relationship("Season")
    player = relationship("Player")

    __table_args__ = (
        UniqueConstraint('season_id', 'player_id', name='uq_pvp_season_player'),
        Index('idx_pvp_rating', 'season_id', 'rating'),
    )
```

#### 4.4.2 PVP管理器

```python
# vibehub/src/core/pvp_manager.py

class PVPManager:
    """PVP竞技场管理器"""

    def __init__(self, db_session):
        self.db = db_session
        self.matchmaking_queue = []

    async def find_match(self, player_id: str, rating_range: int = 200) -> Optional[dict]:
        """寻找匹配对手

        Args:
            player_id: 玩家ID
            rating_range: 积分匹配范围

        Returns:
            匹配信息或 None
        """
        # 获取玩家当前积分
        player_rating = await self._get_player_rating(player_id)

        # 在队列中寻找匹配
        for queued_player in self.matchmaking_queue:
            queued_id = queued_player["player_id"]
            if queued_id == player_id:
                continue

            queued_rating = await self._get_player_rating(queued_id)

            # 检查积分是否在匹配范围内
            if abs(player_rating - queued_rating) <= rating_range:
                # 创建对战
                match = await self._create_match(player_id, queued_id)

                # 从队列移除
                self.matchmaking_queue.remove(queued_player)

                return match

        # 没有找到匹配，加入队列
        self.matchmaking_queue.append({
            "player_id": player_id,
            "rating": player_rating,
            "queued_at": datetime.utcnow()
        })

        return None

    async def _create_match(self, player_a_id: str, player_b_id: str) -> dict:
        """创建PVP对战"""
        match_id = f"pvp_{uuid.uuid4().hex[:8]}"

        match = PVPMatch(
            match_id=match_id,
            player_a_id=player_a_id,
            player_b_id=player_b_id,
            status="waiting"
        )

        self.db.add(match)
        await self.db.commit()

        return {
            "match_id": match_id,
            "player_a": await self._get_player_info(player_a_id),
            "player_b": await self._get_player_info(player_b_id),
            "status": "waiting"
        }

    async def start_match(self, match_id: str) -> dict:
        """开始对战"""
        match = await self.db.get(PVPMatch, match_id)
        if not match:
            raise ValueError("对战不存在")

        match.status = "active"
        match.started_at = datetime.utcnow()
        await self.db.commit()

        return {"match_id": match_id, "status": "active"}

    async def submit_result(
        self,
        match_id: str,
        winner_id: str,
        score_a: int,
        score_b: int
    ) -> dict:
        """提交对战结果"""
        match = await self.db.get(PVPMatch, match_id)
        if not match or match.status != "active":
            raise ValueError("对战不存在或已结束")

        # 更新对战结果
        match.winner_id = winner_id
        match.score_a = score_a
        match.score_b = score_b
        match.status = "finished"
        match.finished_at = datetime.utcnow()

        # 更新双方积分（ELO算法）
        await self._update_ratings(match)

        await self.db.commit()

        return await self._get_match_result(match_id)

    async def _get_player_rating(self, player_id: str) -> int:
        """获取玩家PVP积分"""
        season_id = await self._get_current_season_id()

        query = select(PVPRanking).where(
            and_(
                PVPRanking.season_id == season_id,
                PVPRanking.player_id == player_id
            )
        )

        result = await self.db.execute(query)
        ranking = result.scalar_one_or_none()

        if not ranking:
            # 创建初始排名
            ranking = PVPRanking(
                ranking_id=f"{season_id}_{player_id}",
                season_id=season_id,
                player_id=player_id,
                rating=1000
            )
            self.db.add(ranking)
            await self.db.commit()

        return ranking.rating if ranking else 1000

    async def _update_ratings(self, match: PVPMatch):
        """更新双方积分（ELO算法）"""
        # 获取双方当前积分
        rating_a = await self._get_player_rating(match.player_a_id)
        rating_b = await self._get_player_rating(match.player_b_id)

        # 计算预期胜率
        expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
        expected_b = 1 / (1 + 10 ** ((rating_a - rating_b) / 400))

        # K因子（根据积分调整）
        k = 32

        # 实际胜率
        actual_a = 1 if match.winner_id == match.player_a_id else 0
        actual_b = 1 if match.winner_id == match.player_b_id else 0

        # 计算新积分
        new_rating_a = rating_a + k * (actual_a - expected_a)
        new_rating_b = rating_b + k * (actual_b - expected_b)

        # 更新积分
        season_id = await self._get_current_season_id()

        await self._update_player_rating(season_id, match.player_a_id, int(new_rating_a), match)
        await self._update_player_rating(season_id, match.player_b_id, int(new_rating_b), match)

    async def _update_player_rating(
        self,
        season_id: str,
        player_id: str,
        new_rating: int,
        match: PVPMatch
    ):
        """更新玩家积分"""
        query = select(PVPRanking).where(
            and_(
                PVPRanking.season_id == season_id,
                PVPRanking.player_id == player_id
            )
        )

        result = await self.db.execute(query)
        ranking = result.scalar_one_or_none()

        if ranking:
            ranking.rating = new_rating
            ranking.max_rating = max(ranking.max_rating, new_rating)
            ranking.matches_played += 1

            # 更新胜负统计
            if match.winner_id == player_id:
                ranking.matches_won += 1
                ranking.current_streak = ranking.current_streak + 1 if ranking.current_streak > 0 else 1
            else:
                ranking.matches_lost += 1
                ranking.current_streak = ranking.current_streak - 1 if ranking.current_streak < 0 else -1

            ranking.max_streak = max(ranking.max_streak, abs(ranking.current_streak))
        else:
            ranking = PVPRanking(
                ranking_id=f"{season_id}_{player_id}",
                season_id=season_id,
                player_id=player_id,
                rating=new_rating,
                max_rating=new_rating,
                matches_played=1,
                matches_won=1 if match.winner_id == player_id else 0,
                matches_lost=0 if match.winner_id == player_id else 1,
                current_streak=1 if match.winner_id == player_id else -1,
                max_streak=1
            )
            self.db.add(ranking)

    async def _get_current_season_id(self) -> str:
        """获取当前赛季ID"""
        query = select(Season).where(Season.is_active == True).order_by(Season.season_number.desc())
        result = await self.db.execute(query)
        season = result.first()

        if not season:
            season_id = f"season_{datetime.utcnow().year}_1"
            season = Season(
                season_id=season_id,
                season_name=f"S{datetime.utcnow().year}赛季1",
                season_number=1,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(days=90)
            )
            self.db.add(season)
            await self.db.commit()
        else:
            season_id = season.season_id

        return season_id

    async def _get_player_info(self, player_id: str) -> dict:
        """获取玩家信息"""
        player = await self.db.get(Player, player_id)
        return {
            "player_id": player.player_id,
            "username": player.username,
            "level": player.level,
        }

    async def _get_match_result(self, match_id: str) -> dict:
        """获取对战结果"""
        match = await self.db.get(PVPMatch, match_id)
        return {
            "match_id": match.match_id,
            "winner_id": match.winner_id,
            "score_a": match.score_a,
            "score_b": match.score_b,
            "duration_seconds": match.duration_seconds,
        }
```

## 五、API 端点设计

### 5.1 成就系统 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/achievement/list` | 获取玩家成就列表 |
| GET | `/api/achievement/{achievement_id}` | 获取成就详情 |
| POST | `/api/achievement/{achievement_id}/claim` | 领取成就奖励 |
| GET | `/api/achievement/progress` | 获取成就进度 |

### 5.2 公会系统 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/guild/list` | 获取公会列表 |
| POST | `/api/guild/create` | 创建公会 |
| POST | `/api/guild/{guild_id}/join` | 加入公会 |
| POST | `/api/guild/{guild_id}/leave` | 离开公会 |
| GET | `/api/guild/{guild_id}/members` | 获取公会成员 |

### 5.3 公会战 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/guild-war/list` | 获取公会战列表 |
| POST | `/api/guild-war/create` | 创建公会战 |
| POST | `/api/guild-war/{war_id}/start` | 开始公会战 |
| POST | `/api/guild-war/{war_id}/score` | 更新分数 |
| POST | `/api/guild-war/{war_id}/end` | 结束公会战 |
| GET | `/api/guild-war/{war_id}/info` | 获取公会战信息 |

### 5.4 排行榜 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/leaderboard/{type}` | 获取排行榜 |
| GET | `/api/leaderboard/{type}/season/{season_id}` | 获取指定赛季排行榜 |
| GET | `/api/leaderboard/{type}/snapshot` | 获取排行榜快照 |
| GET | `/api/season/current` | 获取当前赛季信息 |

### 5.5 PVP竞技场 API

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/pvp/matchmaking` | 加入匹配队列 |
| GET | `/api/pvp/match/{match_id}` | 获取对战信息 |
| POST | `/api/pvp/match/{match_id}/start` | 开始对战 |
| POST | `/api/pvp/match/{match_id}/result` | 提交对战结果 |
| POST | `/api/pvp/match/{match_id}/spectate` | 观战 |
| GET | `/api/pvp/ranking/{player_id}` | 获取PVP积分 |

## 六、文件位置

### 6.1 数据模型
- `vibehub/src/storage/models.py` - 添加新模型定义

### 6.2 核心管理器
- `vibehub/src/core/achievement_manager.py` - 成就管理器
- `vibehub/src/core/guild_manager.py` - 公会管理器
- `vibehub/src/core/guild_war_manager.py` - 公会战管理器
- `vibehub/src/core/leaderboard_manager.py` - 排行榜管理器
- `vibehub/src/core/pvp_manager.py` - PVP竞技场管理器

### 6.3 API 路由
- `vibehub/src/api/achievement.py` - 成就系统API
- `vibehub/src/api/guild.py` - 公会系统API
- `vibehub/src/api/guild_war.py` - 公会战API
- `vibehub/src/api/leaderboard.py` - 排行榜API
- `vibehub/src/api/pvp.py` - PVP竞技场API

### 6.4 测试文件
- `vibehub/tests/test_achievement_manager.py`
- `vibehub/tests/test_guild_manager.py`
- `vibehub/tests/test_guild_war_manager.py`
- `vibehub/tests/test_leaderboard_manager.py`
- `vibehub/tests/test_pvp_manager.py`
- `vibehub/tests/test_achievement_api.py`
- `vibehub/tests/test_guild_api.py`
- `vibehub/tests/test_pvp_api.py`

### 6.5 Godot 客户端
- `game/scripts/ui/achievement/` - 成就UI组件
- `game/scripts/ui/guild/` - 公会UI组件
- `game/scripts/ui/pvp/` - PVP竞技场UI组件

## 七、实施步骤

### 步骤 1：数据模型创建（1-2天）
- [ ] 创建 Achievement 和 AchievementProgress 模型
- [ ] 创建 Guild 和 GuildMember 模型
- [ ] 创建 GuildWar 相关模型
- [ ] 创建 Season 和 Leaderboard 模型
- [ ] 创建 PVPMatch 和 PVPRanking 模型
- [ ] 运行数据库迁移

### 步骤 2：成就系统实现（3-5天）
- [ ] 实现 AchievementManager 类
- [ ] 实现成就进度检查逻辑
- [ ] 实现 50+ 成就定义
- [ ] 创建成就系统 API
- [ ] 编写单元测试

### 步骤 3：公会系统实现（5-7天）
- [ ] 实现 GuildManager 类
- [ ] 实现公会创建、加入、离开功能
- [ ] 实现公会成员管理
- [ ] 实现公会贡献系统
- [ ] 创建公会系统 API
- [ ] 编写单元测试

### 步骤 4：公会战系统实现（5-7天）
- [ ] 实现 GuildWarManager 类
- [ ] 实现匹配和对战逻辑
- [ ] 实现奖励分配系统
- [ ] 创建公会战 API
- [ ] 编写单元测试

### 步骤 5：排行榜与赛季实现（3-5天）
- [ ] 实现 LeaderboardManager 类
- [ ] 实现赛季管理系统
- [ ] 实现排行榜计算逻辑
- [ ] 创建排行榜 API
- [ ] 编写单元测试

### 步骤 6：PVP竞技场实现（7-10天）
- [ ] 实现 PVPManager 类
- [ ] 实现匹配系统
- [ ] 实现 ELO 积分算法
- [ ] 实现观战功能
- [ ] 创建 PVP API
- [ ] 编写单元测试

### 步骤 7：UI 实现（Godot 客户端）（10-15天）
- [ ] 实现成就界面
- [ ] 实现公会界面
- [ ] 实现排行榜界面
- [ ] 实现 PVP 竞技场界面
- [ ] 实现赛季选择界面

### 步骤 8：集成测试（3-5天）
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 压力测试
- [ ] 用户体验测试

### 步骤 9：文档与发布（2-3天）
- [ ] 更新 API 文档
- [ ] 编写用户手册
- [ ] 准备发布说明
- [ ] Git 提交和发布

## 八、验收标准

### 8.1 功能验收

- [ ] **成就系统**：50+ 成就定义，进度追踪正常，奖励发放正确
- [ ] **公会系统**：创建、加入、离开功能正常，成员管理正常
- [ ] **公会战**：匹配、对战、结算流程正常
- [ ] **排行榜**：实时更新正确，赛季切换正常
- [ ] **PVP 竞技场**：匹配系统正常，积分计算正确，观战功能可用

### 8.2 性能验收

- [ ] API 响应时间 < 500ms
- [ ] 排行榜更新频率 5 分钟
- [ ] 支持并发用户 ≥ 100
- [ ] PVP 匹配延迟 < 30 秒

### 8.3 代码质量验收

- [ ] 单元测试覆盖率 ≥ 70%
- [ ] 所有测试通过
- [ ] ruff 检查通过
- [ ] mypy 类型检查通过

### 8.4 用户体验验收

- [ ] UI 界面友好，操作流畅
- [ ] 新手引导完整
- [ ] 错误提示清晰
- [ ] 多语言支持（中文/英文）

## 九、风险评估与缓解

| 风险 | 可能性 | 影响 | 缓解策略 |
|------|--------|------|----------|
| 玩家匹配困难 | 中 | 中 | 扩大匹配范围，添加机器人 |
| 作弊刷分 | 高 | 高 | 多维度验证，异常检测，封号机制 |
| 服务器负载高 | 中 | 中 | 数据库优化，缓存，异步处理 |
| 平衡性问题 | 中 | 中 | 持续监控数据，动态调整 |

## 十、后续优化方向

1. **内容持续更新**：定期添加新成就、新活动
2. **数据分析工具**：运营数据看板，用户行为分析
3. **AI 匹配优化**：使用机器学习优化匹配算法
4. **跨平台支持**：移动端适配，Web 端支持

---

**文档版本**: v1.0
**创建日期**: 2026-02-16
**作者**: Happy Vibe 开发团队
