"""成就系统 API 路由

提供成就列表、进度查询、解锁等功能的 REST API 端点。
"""

from datetime import UTC, datetime
from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.storage.database import get_db
from src.storage.models import Achievement, Player

# ============ 成就类型枚举 ============


class AchievementCategory(StrEnum):
    """成就类别"""

    CODING = "coding"  # 编码相关
    FARMING = "farming"  # 农场相关
    SOCIAL = "social"  # 社交相关
    COLLECTION = "collection"  # 收集相关
    MILESTONE = "milestone"  # 里程碑


class AchievementRarity(StrEnum):
    """成就稀有度"""

    COMMON = "common"  # 普通
    RARE = "rare"  # 稀有
    EPIC = "epic"  # 史诗
    LEGENDARY = "legendary"  # 传说


# ============ 成就配置 ============

ACHIEVEMENT_CONFIG: dict[str, dict] = {
    # 编码成就
    "first_code": {
        "name": "初次编码",
        "description": "完成第一次编码活动",
        "category": AchievementCategory.CODING,
        "rarity": AchievementRarity.COMMON,
        "target": 1,
        "reward_gold": 100,
        "reward_exp": 50,
        "icon": "🎯",
    },
    "code_hour": {
        "name": "一小时程序员",
        "description": "累计编码 1 小时",
        "category": AchievementCategory.CODING,
        "rarity": AchievementRarity.COMMON,
        "target": 3600,  # 秒
        "reward_gold": 200,
        "reward_exp": 100,
        "icon": "⏱️",
    },
    "code_master": {
        "name": "编码大师",
        "description": "累计编码 100 小时",
        "category": AchievementCategory.CODING,
        "rarity": AchievementRarity.EPIC,
        "target": 360000,
        "reward_gold": 5000,
        "reward_exp": 2000,
        "icon": "👨‍💻",
    },
    "flow_state": {
        "name": "心流体验",
        "description": "首次进入心流状态",
        "category": AchievementCategory.CODING,
        "rarity": AchievementRarity.RARE,
        "target": 1,
        "reward_gold": 500,
        "reward_exp": 200,
        "icon": "🌊",
    },
    "flow_master": {
        "name": "心流大师",
        "description": "累计心流时间达到 10 小时",
        "category": AchievementCategory.CODING,
        "rarity": AchievementRarity.LEGENDARY,
        "target": 36000,
        "reward_gold": 10000,
        "reward_exp": 5000,
        "icon": "🧘",
    },
    # 农场成就
    "first_harvest": {
        "name": "初次收获",
        "description": "收获第一株作物",
        "category": AchievementCategory.FARMING,
        "rarity": AchievementRarity.COMMON,
        "target": 1,
        "reward_gold": 50,
        "reward_exp": 25,
        "icon": "🌾",
    },
    "harvest_100": {
        "name": "丰收农场主",
        "description": "累计收获 100 株作物",
        "category": AchievementCategory.FARMING,
        "rarity": AchievementRarity.RARE,
        "target": 100,
        "reward_gold": 1000,
        "reward_exp": 500,
        "icon": "🚜",
    },
    "legendary_crop": {
        "name": "传说品质",
        "description": "收获一株传说品质的作物",
        "category": AchievementCategory.FARMING,
        "rarity": AchievementRarity.EPIC,
        "target": 1,
        "reward_gold": 2000,
        "reward_exp": 1000,
        "icon": "⭐",
    },
    # 收集成就
    "crop_collector": {
        "name": "作物收藏家",
        "description": "收集所有类型的作物",
        "category": AchievementCategory.COLLECTION,
        "rarity": AchievementRarity.EPIC,
        "target": 8,  # 8 种作物
        "reward_gold": 3000,
        "reward_exp": 1500,
        "icon": "📚",
    },
    # 里程碑成就
    "level_10": {
        "name": "初露锋芒",
        "description": "达到 10 级",
        "category": AchievementCategory.MILESTONE,
        "rarity": AchievementRarity.COMMON,
        "target": 10,
        "reward_gold": 500,
        "reward_exp": 0,
        "icon": "📈",
    },
    "level_50": {
        "name": "经验丰富",
        "description": "达到 50 级",
        "category": AchievementCategory.MILESTONE,
        "rarity": AchievementRarity.RARE,
        "target": 50,
        "reward_gold": 2000,
        "reward_exp": 0,
        "icon": "🏆",
    },
    "level_100": {
        "name": "传奇玩家",
        "description": "达到 100 级",
        "category": AchievementCategory.MILESTONE,
        "rarity": AchievementRarity.LEGENDARY,
        "target": 100,
        "reward_gold": 10000,
        "reward_exp": 0,
        "icon": "👑",
    },
    # 社交成就
    "first_friend": {
        "name": "初识好友",
        "description": "添加第一个好友",
        "category": AchievementCategory.SOCIAL,
        "rarity": AchievementRarity.COMMON,
        "target": 1,
        "reward_gold": 100,
        "reward_exp": 50,
        "icon": "🤝",
    },
    "social_butterfly": {
        "name": "社交达人",
        "description": "拥有 10 个好友",
        "category": AchievementCategory.SOCIAL,
        "rarity": AchievementRarity.RARE,
        "target": 10,
        "reward_gold": 1000,
        "reward_exp": 500,
        "icon": "🦋",
    },
}


# ============ Pydantic 模型 ============

class AchievementConfigResponse(BaseModel):
    """成就配置响应模型"""
    achievement_id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    target: int
    reward_gold: int
    reward_exp: int
    icon: str


class AchievementProgressResponse(BaseModel):
    """成就进度响应模型"""
    achievement_id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    icon: str
    progress: int
    target: int
    is_unlocked: bool
    unlocked_at: datetime | None = None
    reward_gold: int
    reward_exp: int


class AchievementListResponse(BaseModel):
    """成就列表响应模型"""
    achievements: list[AchievementProgressResponse]
    total: int
    unlocked_count: int


class ProgressUpdateRequest(BaseModel):
    """进度更新请求模型"""
    increment: int = Field(default=1, ge=1, description="进度增量")


class ProgressUpdateResponse(BaseModel):
    """进度更新响应模型"""
    achievement_id: str
    previous_progress: int
    current_progress: int
    target: int
    is_unlocked: bool
    newly_unlocked: bool
    reward_gold: int = 0
    reward_exp: int = 0


class CheckAchievementsRequest(BaseModel):
    """检查成就请求模型"""
    player_id: str


class UnlockedAchievementInfo(BaseModel):
    """解锁成就信息"""
    achievement_id: str
    name: str
    icon: str
    reward_gold: int
    reward_exp: int


class CheckAchievementsResponse(BaseModel):
    """检查成就响应模型"""
    newly_unlocked: list[UnlockedAchievementInfo]
    total_reward_gold: int
    total_reward_exp: int


# ============ 依赖注入 ============

def get_db_session():
    """获取数据库会话"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


# ============ 路由定义 ============

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


@router.get("", response_model=AchievementListResponse)
async def get_achievements(
    player_id: str,
    category: AchievementCategory | None = None,
    session: Session = Depends(get_db_session),
) -> AchievementListResponse:
    """获取所有成就列表

    Args:
        player_id: 玩家 ID
        category: 可选的成就类别筛选

    Returns:
        成就列表及统计信息
    """
    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    # 获取玩家的成就进度
    player_achievements = {
        a.achievement_id: a
        for a in session.query(Achievement)
        .filter(Achievement.player_id == player_id)
        .all()
    }

    achievements = []
    unlocked_count = 0

    for ach_id, config in ACHIEVEMENT_CONFIG.items():
        # 类别筛选
        if category and config["category"] != category:
            continue

        player_ach = player_achievements.get(ach_id)
        progress = player_ach.progress if player_ach else 0
        is_unlocked = player_ach.is_unlocked if player_ach else False
        unlocked_at = player_ach.unlocked_at if player_ach else None

        if is_unlocked:
            unlocked_count += 1

        achievements.append(
            AchievementProgressResponse(
                achievement_id=ach_id,
                name=config["name"],
                description=config["description"],
                category=config["category"],
                rarity=config["rarity"],
                icon=config["icon"],
                progress=progress,
                target=config["target"],
                is_unlocked=is_unlocked,
                unlocked_at=unlocked_at,
                reward_gold=config["reward_gold"],
                reward_exp=config["reward_exp"],
            )
        )

    return AchievementListResponse(
        achievements=achievements,
        total=len(achievements),
        unlocked_count=unlocked_count,
    )


@router.get("/config", response_model=list[AchievementConfigResponse])
async def get_achievement_configs(
    category: AchievementCategory | None = None,
) -> list[AchievementConfigResponse]:
    """获取成就配置列表（不需要玩家 ID）

    Args:
        category: 可选的成就类别筛选

    Returns:
        成就配置列表
    """
    configs = []
    for ach_id, config in ACHIEVEMENT_CONFIG.items():
        if category and config["category"] != category:
            continue
        configs.append(
            AchievementConfigResponse(
                achievement_id=ach_id,
                name=config["name"],
                description=config["description"],
                category=config["category"],
                rarity=config["rarity"],
                target=config["target"],
                reward_gold=config["reward_gold"],
                reward_exp=config["reward_exp"],
                icon=config["icon"],
            )
        )
    return configs


@router.get("/unlocked", response_model=list[AchievementProgressResponse])
async def get_unlocked_achievements(
    player_id: str,
    session: Session = Depends(get_db_session),
) -> list[AchievementProgressResponse]:
    """获取已解锁的成就列表

    Args:
        player_id: 玩家 ID

    Returns:
        已解锁的成就列表
    """
    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    # 获取已解锁的成就
    unlocked = (
        session.query(Achievement)
        .filter(Achievement.player_id == player_id, Achievement.is_unlocked.is_(True))
        .all()
    )

    achievements = []
    for ach in unlocked:
        config = ACHIEVEMENT_CONFIG.get(ach.achievement_id)
        if not config:
            continue
        achievements.append(
            AchievementProgressResponse(
                achievement_id=ach.achievement_id,
                name=config["name"],
                description=config["description"],
                category=config["category"],
                rarity=config["rarity"],
                icon=config["icon"],
                progress=ach.progress,
                target=config["target"],
                is_unlocked=True,
                unlocked_at=ach.unlocked_at,
                reward_gold=config["reward_gold"],
                reward_exp=config["reward_exp"],
            )
        )

    return achievements


@router.get("/{achievement_id}", response_model=AchievementProgressResponse)
async def get_achievement(
    achievement_id: str,
    player_id: str,
    session: Session = Depends(get_db_session),
) -> AchievementProgressResponse:
    """获取单个成就详情

    Args:
        achievement_id: 成就 ID
        player_id: 玩家 ID

    Returns:
        成就详情
    """
    # 验证成就存在
    config = ACHIEVEMENT_CONFIG.get(achievement_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"成就不存在: {achievement_id}",
        )

    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    # 获取玩家的成就进度
    player_ach = (
        session.query(Achievement)
        .filter(
            Achievement.player_id == player_id,
            Achievement.achievement_id == achievement_id,
        )
        .first()
    )

    return AchievementProgressResponse(
        achievement_id=achievement_id,
        name=config["name"],
        description=config["description"],
        category=config["category"],
        rarity=config["rarity"],
        icon=config["icon"],
        progress=player_ach.progress if player_ach else 0,
        target=config["target"],
        is_unlocked=player_ach.is_unlocked if player_ach else False,
        unlocked_at=player_ach.unlocked_at if player_ach else None,
        reward_gold=config["reward_gold"],
        reward_exp=config["reward_exp"],
    )


@router.post("/{achievement_id}/progress", response_model=ProgressUpdateResponse)
async def update_achievement_progress(
    achievement_id: str,
    player_id: str,
    request: ProgressUpdateRequest,
    session: Session = Depends(get_db_session),
) -> ProgressUpdateResponse:
    """更新成就进度

    Args:
        achievement_id: 成就 ID
        player_id: 玩家 ID
        request: 进度更新请求

    Returns:
        更新后的进度信息
    """
    # 验证成就存在
    config = ACHIEVEMENT_CONFIG.get(achievement_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"成就不存在: {achievement_id}",
        )

    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    # 获取或创建成就进度记录
    player_ach = (
        session.query(Achievement)
        .filter(
            Achievement.player_id == player_id,
            Achievement.achievement_id == achievement_id,
        )
        .first()
    )

    if not player_ach:
        player_ach = Achievement(
            player_id=player_id,
            achievement_id=achievement_id,
            progress=0,
            target=config["target"],
            is_unlocked=False,
        )
        session.add(player_ach)

    previous_progress = player_ach.progress
    was_unlocked = player_ach.is_unlocked

    # 如果已解锁，不再更新进度
    if was_unlocked:
        return ProgressUpdateResponse(
            achievement_id=achievement_id,
            previous_progress=previous_progress,
            current_progress=previous_progress,
            target=config["target"],
            is_unlocked=True,
            newly_unlocked=False,
        )

    # 更新进度
    player_ach.progress = min(previous_progress + request.increment, config["target"])

    # 检查是否解锁
    newly_unlocked = False
    reward_gold = 0
    reward_exp = 0

    if player_ach.progress >= config["target"] and not was_unlocked:
        player_ach.is_unlocked = True
        player_ach.unlocked_at = datetime.now(UTC)
        newly_unlocked = True
        reward_gold = config["reward_gold"]
        reward_exp = config["reward_exp"]

        # 发放奖励
        player.gold += reward_gold
        player.experience += reward_exp

    session.commit()

    return ProgressUpdateResponse(
        achievement_id=achievement_id,
        previous_progress=previous_progress,
        current_progress=player_ach.progress,
        target=config["target"],
        is_unlocked=player_ach.is_unlocked,
        newly_unlocked=newly_unlocked,
        reward_gold=reward_gold,
        reward_exp=reward_exp,
    )


@router.post("/check", response_model=CheckAchievementsResponse)
async def check_achievements(
    request: CheckAchievementsRequest,
    session: Session = Depends(get_db_session),
) -> CheckAchievementsResponse:
    """检查并解锁符合条件的成就

    根据玩家当前状态自动检查并解锁成就。

    Args:
        request: 检查请求

    Returns:
        新解锁的成就列表和奖励
    """
    player_id = request.player_id

    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    # 获取玩家现有成就
    existing_achievements = {
        a.achievement_id: a
        for a in session.query(Achievement)
        .filter(Achievement.player_id == player_id)
        .all()
    }

    newly_unlocked = []
    total_reward_gold = 0
    total_reward_exp = 0

    # 检查里程碑成就（等级相关）
    level_achievements = {
        "level_10": 10,
        "level_50": 50,
        "level_100": 100,
    }

    for ach_id, required_level in level_achievements.items():
        existing = existing_achievements.get(ach_id)
        if existing and existing.is_unlocked:
            continue

        if player.level >= required_level:
            config = ACHIEVEMENT_CONFIG[ach_id]

            if not existing:
                existing = Achievement(
                    player_id=player_id,
                    achievement_id=ach_id,
                    progress=player.level,
                    target=config["target"],
                    is_unlocked=True,
                    unlocked_at=datetime.now(UTC),
                )
                session.add(existing)
            else:
                existing.progress = player.level
                existing.is_unlocked = True
                existing.unlocked_at = datetime.now(UTC)

            reward_gold = config["reward_gold"]
            reward_exp = config["reward_exp"]
            player.gold += reward_gold
            player.experience += reward_exp
            total_reward_gold += reward_gold
            total_reward_exp += reward_exp

            newly_unlocked.append(
                UnlockedAchievementInfo(
                    achievement_id=ach_id,
                    name=config["name"],
                    icon=config["icon"],
                    reward_gold=reward_gold,
                    reward_exp=reward_exp,
                )
            )

    session.commit()

    return CheckAchievementsResponse(
        newly_unlocked=newly_unlocked,
        total_reward_gold=total_reward_gold,
        total_reward_exp=total_reward_exp,
    )
