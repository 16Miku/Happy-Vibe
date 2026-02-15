"""成就数据定义模块

定义游戏中所有成就的配置，包括编程、农场、社交、经济、特殊等类别。
总计 50+ 成就，支持不同稀有度等级。
"""

import json
from dataclasses import dataclass
from typing import Any

from src.storage.models import AchievementCategory, AchievementTier


@dataclass
class AchievementConfig:
    """成就配置数据类

    Attributes:
        achievement_id: 成就唯一标识符
        category: 成就类别
        tier: 稀有度
        title: 英文标题
        title_zh: 中文标题
        description: 成就描述
        requirement_type: 条件类型
        requirement_param: 条件参数 (JSON)
        reward: 奖励配置
        is_hidden: 是否隐藏
        is_secret: 是否秘密
        icon: 图标
        display_order: 显示顺序
    """

    achievement_id: str
    category: AchievementCategory
    tier: AchievementTier
    title: str
    title_zh: str
    description: str
    requirement_type: str
    requirement_param: dict[str, Any] | None
    reward: dict[str, int]
    is_hidden: bool = False
    is_secret: bool = False
    icon: str = "🏆"
    display_order: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "achievement_id": self.achievement_id,
            "category": self.category.value,
            "tier": self.tier.value,
            "title": self.title,
            "title_zh": self.title_zh,
            "description": self.description,
            "requirement_type": self.requirement_type,
            "requirement_param": (
                json.dumps(self.requirement_param) if self.requirement_param else None
            ),
            "reward_json": json.dumps(self.reward),
            "is_hidden": self.is_hidden,
            "is_secret": self.is_secret,
            "icon": self.icon,
            "display_order": self.display_order,
        }


# ============================================================
# 成就配置列表 - 总计 50+ 成就
# ============================================================

ACHIEVEMENT_DEFINITIONS: list[AchievementConfig] = [
    # ========================================================
    # 编程成就 (Coding) - 14 个
    # ========================================================
    AchievementConfig(
        achievement_id="coding_first",
        category=AchievementCategory.CODING,
        tier=AchievementTier.COMMON,
        title="First Code",
        title_zh="初次编码",
        description="完成第一次编程活动",
        requirement_type="coding_count",
        requirement_param={"target": 1},
        reward={"gold": 100, "exp": 50},
        icon="🎯",
        display_order=1,
    ),
    AchievementConfig(
        achievement_id="coding_10",
        category=AchievementCategory.CODING,
        tier=AchievementTier.COMMON,
        title="Coder Novice",
        title_zh="编程新手",
        description="完成 10 次编程活动",
        requirement_type="coding_count",
        requirement_param={"target": 10},
        reward={"gold": 200, "exp": 100},
        icon="💻",
        display_order=2,
    ),
    AchievementConfig(
        achievement_id="coding_50",
        category=AchievementCategory.CODING,
        tier=AchievementTier.RARE,
        title="Coder Adept",
        title_zh="编程熟手",
        description="完成 50 次编程活动",
        requirement_type="coding_count",
        requirement_param={"target": 50},
        reward={"gold": 500, "exp": 250},
        icon="👨‍💻",
        display_order=3,
    ),
    AchievementConfig(
        achievement_id="coding_100",
        category=AchievementCategory.CODING,
        tier=AchievementTier.EPIC,
        title="Code Master",
        title_zh="编程大师",
        description="完成 100 次编程活动",
        requirement_type="coding_count",
        requirement_param={"target": 100},
        reward={"gold": 1000, "exp": 500},
        icon="🚀",
        display_order=4,
    ),
    AchievementConfig(
        achievement_id="coding_time_1h",
        category=AchievementCategory.CODING,
        tier=AchievementTier.COMMON,
        title="Hour Coder",
        title_zh="一小时程序员",
        description="累计编码 1 小时",
        requirement_type="coding_time",
        requirement_param={"target_seconds": 3600},
        reward={"gold": 150, "exp": 75},
        icon="⏱️",
        display_order=5,
    ),
    AchievementConfig(
        achievement_id="coding_time_10h",
        category=AchievementCategory.CODING,
        tier=AchievementTier.RARE,
        title="Dedicated Coder",
        title_zh="专注编程者",
        description="累计编码 10 小时",
        requirement_type="coding_time",
        requirement_param={"target_seconds": 36000},
        reward={"gold": 500, "exp": 250},
        icon="⌚",
        display_order=6,
    ),
    AchievementConfig(
        achievement_id="coding_time_100h",
        category=AchievementCategory.CODING,
        tier=AchievementTier.LEGENDARY,
        title="Code Legend",
        title_zh="代码传说",
        description="累计编码 100 小时",
        requirement_type="coding_time",
        requirement_param={"target_seconds": 360000},
        reward={"gold": 5000, "exp": 2500, "diamonds": 10},
        icon="👑",
        display_order=7,
    ),
    AchievementConfig(
        achievement_id="flow_first",
        category=AchievementCategory.CODING,
        tier=AchievementTier.RARE,
        title="Flow State",
        title_zh="心流体验",
        description="首次进入心流状态",
        requirement_type="flow_count",
        requirement_param={"target": 1},
        reward={"gold": 300, "exp": 150},
        icon="🌊",
        display_order=8,
    ),
    AchievementConfig(
        achievement_id="flow_10",
        category=AchievementCategory.CODING,
        tier=AchievementTier.EPIC,
        title="Flow Master",
        title_zh="心流大师",
        description="进入心流状态 10 次",
        requirement_type="flow_count",
        requirement_param={"target": 10},
        reward={"gold": 1000, "exp": 500},
        icon="🧘",
        display_order=9,
    ),
    AchievementConfig(
        achievement_id="flow_time_1h",
        category=AchievementCategory.CODING,
        tier=AchievementTier.EPIC,
        title="Deep Focus",
        title_zh="深度专注",
        description="累计心流时间达到 1 小时",
        requirement_type="flow_time",
        requirement_param={"target_seconds": 3600},
        reward={"gold": 800, "exp": 400},
        icon="🎯",
        display_order=10,
    ),
    AchievementConfig(
        achievement_id="coding_fullstack",
        category=AchievementCategory.CODING,
        tier=AchievementTier.EPIC,
        title="Full Stack",
        title_zh="全栈开发者",
        description="完成所有类型的编程任务",
        requirement_type="task_variety",
        requirement_param={"target_types": 5},
        reward={"gold": 1500, "exp": 750},
        icon="🔧",
        display_order=11,
    ),
    AchievementConfig(
        achievement_id="coding_streak_7",
        category=AchievementCategory.CODING,
        tier=AchievementTier.RARE,
        title="Week Warrior",
        title_zh="七日坚持",
        description="连续 7 天完成编程活动",
        requirement_type="coding_streak",
        requirement_param={"target_days": 7},
        reward={"gold": 700, "exp": 350},
        icon="🔥",
        display_order=12,
    ),
    AchievementConfig(
        achievement_id="coding_streak_30",
        category=AchievementCategory.CODING,
        tier=AchievementTier.LEGENDARY,
        title="Monthly Master",
        title_zh="月度冠军",
        description="连续 30 天完成编程活动",
        requirement_type="coding_streak",
        requirement_param={"target_days": 30},
        reward={"gold": 3000, "exp": 1500, "diamonds": 20},
        icon="💎",
        display_order=13,
    ),
    AchievementConfig(
        achievement_id="coding_lines_1000",
        category=AchievementCategory.CODING,
        tier=AchievementTier.COMMON,
        title="Thousand Lines",
        title_zh="千行代码",
        description="累计编写 1000 行代码",
        requirement_type="lines_written",
        requirement_param={"target": 1000},
        reward={"gold": 200, "exp": 100},
        icon="📝",
        display_order=14,
    ),
    # ========================================================
    # 农场成就 (Farming) - 14 个
    # ========================================================
    AchievementConfig(
        achievement_id="farm_first_plant",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.COMMON,
        title="First Seed",
        title_zh="初次播种",
        description="种植第一株作物",
        requirement_type="plant_count",
        requirement_param={"target": 1},
        reward={"gold": 50, "exp": 25},
        icon="🌱",
        display_order=101,
    ),
    AchievementConfig(
        achievement_id="farm_first_harvest",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.COMMON,
        title="First Harvest",
        title_zh="初次收获",
        description="收获第一株作物",
        requirement_type="harvest_count",
        requirement_param={"target": 1},
        reward={"gold": 100, "exp": 50},
        icon="🌾",
        display_order=102,
    ),
    AchievementConfig(
        achievement_id="farm_plant_100",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.COMMON,
        title="Planter",
        title_zh="播种者",
        description="种植 100 株作物",
        requirement_type="plant_count",
        requirement_param={"target": 100},
        reward={"gold": 300, "exp": 150},
        icon="🌿",
        display_order=103,
    ),
    AchievementConfig(
        achievement_id="farm_harvest_100",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.RARE,
        title="Harvester",
        title_zh="收获者",
        description="收获 100 株作物",
        requirement_type="harvest_count",
        requirement_param={"target": 100},
        reward={"gold": 500, "exp": 250},
        icon="🚜",
        display_order=104,
    ),
    AchievementConfig(
        achievement_id="farm_harvest_1000",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.EPIC,
        title="Farm Tycoon",
        title_zh="农场大亨",
        description="收获 1000 株作物",
        requirement_type="harvest_count",
        requirement_param={"target": 1000},
        reward={"gold": 2000, "exp": 1000},
        icon="🏡",
        display_order=105,
    ),
    AchievementConfig(
        achievement_id="farm_quality_excellent_10",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.RARE,
        title="Quality Seeker",
        title_zh="品质追求者",
        description="收获 10 株精品(⭐⭐⭐)以上作物",
        requirement_type="quality_harvest",
        requirement_param={"target": 10, "min_quality": 3},
        reward={"gold": 600, "exp": 300},
        icon="⭐",
        display_order=106,
    ),
    AchievementConfig(
        achievement_id="farm_quality_legendary",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.LEGENDARY,
        title="Legendary Harvest",
        title_zh="传说品质",
        description="收获一株传说(⭐⭐⭐⭐)品质作物",
        requirement_type="quality_harvest",
        requirement_param={"target": 1, "min_quality": 4},
        reward={"gold": 2000, "exp": 1000, "diamonds": 5},
        icon="💫",
        display_order=107,
    ),
    AchievementConfig(
        achievement_id="farm_unlock_all_plots",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.EPIC,
        title="Landlord",
        title_zh="土地主",
        description="解锁所有地块",
        requirement_type="plot_unlock",
        requirement_param={"target": 20},
        reward={"gold": 1500, "exp": 750},
        icon="🗺️",
        display_order=108,
    ),
    AchievementConfig(
        achievement_id="farm_all_types",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.EPIC,
        title="Botanist",
        title_zh="植物学家",
        description="收获所有类型的作物",
        requirement_type="crop_variety",
        requirement_param={"target_types": 8},
        reward={"gold": 1200, "exp": 600},
        icon="🌺",
        display_order=109,
    ),
    AchievementConfig(
        achievement_id="farm_water_100",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.COMMON,
        title="Water Boy",
        title_zh="浇水员",
        description="给作物浇水 100 次",
        requirement_type="water_count",
        requirement_param={"target": 100},
        reward={"gold": 200, "exp": 100},
        icon="💧",
        display_order=110,
    ),
    AchievementConfig(
        achievement_id="farm_daily_harvest_7",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.RARE,
        title="Daily Farmer",
        title_zh="每日农夫",
        description="连续 7 天收获作物",
        requirement_type="harvest_streak",
        requirement_param={"target_days": 7},
        reward={"gold": 700, "exp": 350},
        icon="📅",
        display_order=111,
    ),
    AchievementConfig(
        achievement_id="farm_sell_1000",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.RARE,
        title="Merchant",
        title_zh="作物商人",
        description="出售作物累计获得 10000 金币",
        requirement_type="gold_from_farm",
        requirement_param={"target": 10000},
        reward={"gold": 500, "exp": 250},
        icon="💰",
        display_order=112,
    ),
    AchievementConfig(
        achievement_id="farm decoration_100",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.COMMON,
        title="Decorator",
        title_zh="装饰师",
        description="农场装饰度达到 100",
        requirement_type="decoration_score",
        requirement_param={"target": 100},
        reward={"gold": 300, "exp": 150},
        icon="🎨",
        display_order=113,
    ),
    AchievementConfig(
        achievement_id="farm_crop_cycle_10",
        category=AchievementCategory.FARMING,
        tier=AchievementTier.RARE,
        title="Speed Farmer",
        title_zh="极速农夫",
        description="在单天内完成 10 个完整种植-收获周期",
        requirement_type="daily_cycles",
        requirement_param={"target": 10},
        reward={"gold": 800, "exp": 400},
        icon="⚡",
        display_order=114,
    ),
    # ========================================================
    # 社交成就 (Social) - 12 个
    # ========================================================
    AchievementConfig(
        achievement_id="social_first_friend",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.COMMON,
        title="First Friend",
        title_zh="初识好友",
        description="添加第一个好友",
        requirement_type="friend_count",
        requirement_param={"target": 1},
        reward={"gold": 100, "exp": 50},
        icon="🤝",
        display_order=201,
    ),
    AchievementConfig(
        achievement_id="social_friends_10",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.RARE,
        title="Social Star",
        title_zh="社交之星",
        description="拥有 10 个好友",
        requirement_type="friend_count",
        requirement_param={"target": 10},
        reward={"gold": 500, "exp": 250},
        icon="🌟",
        display_order=202,
    ),
    AchievementConfig(
        achievement_id="social_friends_50",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.EPIC,
        title="Popular",
        title_zh="人气王",
        description="拥有 50 个好友",
        requirement_type="friend_count",
        requirement_param={"target": 50},
        reward={"gold": 1500, "exp": 750},
        icon="👥",
        display_order=203,
    ),
    AchievementConfig(
        achievement_id="social_help_10",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.COMMON,
        title="Helper",
        title_zh="热心助手",
        description="帮助好友 10 次",
        requirement_type="help_count",
        requirement_param={"target": 10},
        reward={"gold": 200, "exp": 100},
        icon="🤗",
        display_order=204,
    ),
    AchievementConfig(
        achievement_id="social_help_100",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.EPIC,
        title="Super Helper",
        title_zh="超级助手",
        description="帮助好友 100 次",
        requirement_type="help_count",
        requirement_param={"target": 100},
        reward={"gold": 1000, "exp": 500},
        icon="😇",
        display_order=205,
    ),
    AchievementConfig(
        achievement_id="social_likes_100",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.RARE,
        title="Likable",
        title_zh="万人迷",
        description="获得 100 个点赞",
        requirement_type="like_count",
        requirement_param={"target": 100},
        reward={"gold": 600, "exp": 300},
        icon="👍",
        display_order=206,
    ),
    AchievementConfig(
        achievement_id="social_visit_10",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.COMMON,
        title="Visitor",
        title_zh="访客",
        description="访问好友农场 10 次",
        requirement_type="visit_count",
        requirement_param={"target": 10},
        reward={"gold": 200, "exp": 100},
        icon="🚪",
        display_order=207,
    ),
    AchievementConfig(
        achievement_id="social_guild_create",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.RARE,
        title="Guild Creator",
        title_zh="公会会长",
        description="创建一个公会",
        requirement_type="guild_create",
        requirement_param={"target": 1},
        reward={"gold": 800, "exp": 400},
        icon="🏰",
        display_order=208,
    ),
    AchievementConfig(
        achievement_id="social_guild_member_10",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.RARE,
        title="Team Player",
        title_zh="团队玩家",
        description="加入一个拥有 10+ 成员的公会",
        requirement_type="guild_member_count",
        requirement_param={"target": 10},
        reward={"gold": 500, "exp": 250},
        icon="🎖️",
        display_order=209,
    ),
    AchievementConfig(
        achievement_id="social_chat_100",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.COMMON,
        title="Chatterbox",
        title_zh="话匣子",
        description="发送 100 条聊天消息",
        requirement_type="chat_count",
        requirement_param={"target": 100},
        reward={"gold": 150, "exp": 75},
        icon="💬",
        display_order=210,
    ),
    AchievementConfig(
        achievement_id="social_gift_10",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.COMMON,
        title="Gifter",
        title_zh="送礼者",
        description="向好友赠送 10 份礼物",
        requirement_type="gift_count",
        requirement_param={"target": 10},
        reward={"gold": 250, "exp": 125},
        icon="🎁",
        display_order=211,
    ),
    AchievementConfig(
        achievement_id="social_refer_5",
        category=AchievementCategory.SOCIAL,
        tier=AchievementTier.RARE,
        title="Recruiter",
        title_zh="招募者",
        description="成功邀请 5 位好友加入游戏",
        requirement_type="refer_count",
        requirement_param={"target": 5},
        reward={"gold": 1000, "exp": 500, "diamonds": 5},
        icon="📧",
        display_order=212,
    ),
    # ========================================================
    # 经济成就 (Economy) - 12 个
    # ========================================================
    AchievementConfig(
        achievement_id="economy_gold_10k",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.COMMON,
        title="First Gold",
        title_zh="第一桶金",
        description="累计获得 10000 金币",
        requirement_type="total_gold_earned",
        requirement_param={"target": 10000},
        reward={"gold": 200, "exp": 100},
        icon="💵",
        display_order=301,
    ),
    AchievementConfig(
        achievement_id="economy_gold_100k",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.RARE,
        title="Wealthy",
        title_zh="富有者",
        description="累计获得 100000 金币",
        requirement_type="total_gold_earned",
        requirement_param={"target": 100000},
        reward={"gold": 1000, "exp": 500},
        icon="💰",
        display_order=302,
    ),
    AchievementConfig(
        achievement_id="economy_millionaire",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.LEGENDARY,
        title="Millionaire",
        title_zh="百万富翁",
        description="拥有 1000000 金币",
        requirement_type="current_gold",
        requirement_param={"target": 1000000},
        reward={"gold": 5000, "exp": 2500, "diamonds": 25},
        icon="🤑",
        display_order=303,
    ),
    AchievementConfig(
        achievement_id="economy_trade_10",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.COMMON,
        title="Trader",
        title_zh="交易员",
        description="完成 10 次市场交易",
        requirement_type="trade_count",
        requirement_param={"target": 10},
        reward={"gold": 200, "exp": 100},
        icon="🏪",
        display_order=304,
    ),
    AchievementConfig(
        achievement_id="economy_trade_100",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.EPIC,
        title="Master Trader",
        title_zh="交易大师",
        description="完成 100 次市场交易",
        requirement_type="trade_count",
        requirement_param={"target": 100},
        reward={"gold": 1500, "exp": 750},
        icon="📊",
        display_order=305,
    ),
    AchievementConfig(
        achievement_id="economy_auction_win_10",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.RARE,
        title="Bidder",
        title_zh="竞拍者",
        description="赢得 10 次拍卖",
        requirement_type="auction_win_count",
        requirement_param={"target": 10},
        reward={"gold": 600, "exp": 300},
        icon="🔨",
        display_order=306,
    ),
    AchievementConfig(
        achievement_id="economy_auction_win_50",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.EPIC,
        title="Auction King",
        title_zh="拍卖之王",
        description="赢得 50 次拍卖",
        requirement_type="auction_win_count",
        requirement_param={"target": 50},
        reward={"gold": 2000, "exp": 1000},
        icon="👑",
        display_order=307,
    ),
    AchievementConfig(
        achievement_id="economy_sell_1000",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.COMMON,
        title="Seller",
        title_zh="销售员",
        description="在市场出售物品 1000 次",
        requirement_type="sell_count",
        requirement_param={"target": 1000},
        reward={"gold": 300, "exp": 150},
        icon="🏷️",
        display_order=308,
    ),
    AchievementConfig(
        achievement_id="economy_shop_buy_50",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.COMMON,
        title="Customer",
        title_zh="顾客",
        description="从商店购买 50 件商品",
        requirement_type="shop_buy_count",
        requirement_param={"target": 50},
        reward={"gold": 200, "exp": 100},
        icon="🛒",
        display_order=309,
    ),
    AchievementConfig(
        achievement_id="economy_profit_10k",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.RARE,
        title="Profit Maker",
        title_zh="利润制造者",
        description="单笔交易利润超过 1000 金币",
        requirement_type="single_profit",
        requirement_param={"target": 1000},
        reward={"gold": 800, "exp": 400},
        icon="📈",
        display_order=310,
    ),
    AchievementConfig(
        achievement_id="economy_daily_profit_7",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.RARE,
        title="Daily Earner",
        title_zh="日赚千金",
        description="连续 7 天通过交易获得利润",
        requirement_type="daily_profit_streak",
        requirement_param={"target_days": 7, "min_profit": 500},
        reward={"gold": 1000, "exp": 500},
        icon="💹",
        display_order=311,
    ),
    AchievementConfig(
        achievement_id="economy_diamond_100",
        category=AchievementCategory.ECONOMY,
        tier=AchievementTier.LEGENDARY,
        title="Diamond Collector",
        title_zh="钻石收藏家",
        description="累计获得 100 钻石",
        requirement_type="total_diamonds",
        requirement_param={"target": 100},
        reward={"gold": 3000, "exp": 1500, "diamonds": 30},
        icon="💎",
        display_order=312,
    ),
    # ========================================================
    # 特殊成就 (Special) - 10 个
    # ========================================================
    AchievementConfig(
        achievement_id="special_early_bird_7",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.RARE,
        title="Early Bird",
        title_zh="早起鸟",
        description="连续 7 天在早上 8 点前完成活动",
        requirement_type="early_bird",
        requirement_param={"target_days": 7, "before_hour": 8},
        reward={"gold": 700, "exp": 350},
        icon="🐦",
        display_order=401,
    ),
    AchievementConfig(
        achievement_id="special_night_owl_7",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.RARE,
        title="Night Owl",
        title_zh="夜猫子",
        description="连续 7 天在晚上 11 点后完成活动",
        requirement_type="night_owl",
        requirement_param={"target_days": 7, "after_hour": 23},
        reward={"gold": 700, "exp": 350},
        icon="🦉",
        display_order=402,
    ),
    AchievementConfig(
        achievement_id="special_daily_complete",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.EPIC,
        title="Perfectionist",
        title_zh="完美主义者",
        description="在一天内完成所有日常任务",
        requirement_type="all_daily_quests",
        requirement_param={"target": 1},
        reward={"gold": 1000, "exp": 500, "diamonds": 3},
        icon="✨",
        display_order=403,
    ),
    AchievementConfig(
        achievement_id="special_daily_complete_7",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.LEGENDARY,
        title="Weekly Perfect",
        title_zh="周完美",
        description="连续 7 天完成所有日常任务",
        requirement_type="all_daily_streak",
        requirement_param={"target_days": 7},
        reward={"gold": 5000, "exp": 2500, "diamonds": 15},
        icon="🏆",
        display_order=404,
    ),
    AchievementConfig(
        achievement_id="special_lucky_crop",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.LEGENDARY,
        title="Lucky One",
        title_zh="幸运儿",
        description="随机获得传说品质作物",
        requirement_type="lucky_drop",
        requirement_param={"target": 1},
        reward={"gold": 3000, "exp": 1500, "diamonds": 10},
        icon="🍀",
        display_order=405,
        is_hidden=True,
    ),
    AchievementConfig(
        achievement_id="special_level_10",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.COMMON,
        title="Rising Star",
        title_zh="新星",
        description="达到 10 级",
        requirement_type="level_reach",
        requirement_param={"target": 10},
        reward={"gold": 500, "exp": 0},
        icon="⭐",
        display_order=406,
    ),
    AchievementConfig(
        achievement_id="special_level_50",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.RARE,
        title="Veteran",
        title_zh="老手",
        description="达到 50 级",
        requirement_type="level_reach",
        requirement_param={"target": 50},
        reward={"gold": 2000, "exp": 0},
        icon="🌟",
        display_order=407,
    ),
    AchievementConfig(
        achievement_id="special_level_100",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.EPIC,
        title="Legend",
        title_zh="传奇",
        description="达到 100 级",
        requirement_type="level_reach",
        requirement_param={"target": 100},
        reward={"gold": 5000, "exp": 0, "diamonds": 20},
        icon="👑",
        display_order=408,
    ),
    AchievementConfig(
        achievement_id="special_checkin_7",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.COMMON,
        title="Week Streak",
        title_zh="一周签到",
        description="连续签到 7 天",
        requirement_type="checkin_streak",
        requirement_param={"target_days": 7},
        reward={"gold": 300, "exp": 150},
        icon="📅",
        display_order=409,
    ),
    AchievementConfig(
        achievement_id="special_checkin_30",
        category=AchievementCategory.SPECIAL,
        tier=AchievementTier.EPIC,
        title="Month Streak",
        title_zh="一月签到",
        description="连续签到 30 天",
        requirement_type="checkin_streak",
        requirement_param={"target_days": 30},
        reward={"gold": 2000, "exp": 1000, "diamonds": 10},
        icon="🗓️",
        display_order=410,
    ),
]


# ============================================================
# 辅助函数
# ============================================================

def get_achievement_by_id(achievement_id: str) -> AchievementConfig | None:
    """根据 ID 获取成就配置

    Args:
        achievement_id: 成就标识符

    Returns:
        成就配置，不存在则返回 None
    """
    for ach in ACHIEVEMENT_DEFINITIONS:
        if ach.achievement_id == achievement_id:
            return ach
    return None


def get_achievements_by_category(
    category: AchievementCategory,
) -> list[AchievementConfig]:
    """根据类别获取成就列表

    Args:
        category: 成就类别

    Returns:
        该类别的成就列表
    """
    return [ach for ach in ACHIEVEMENT_DEFINITIONS if ach.category == category]


def get_achievements_by_tier(tier: AchievementTier) -> list[AchievementConfig]:
    """根据稀有度获取成就列表

    Args:
        tier: 成就稀有度

    Returns:
        该稀有度的成就列表
    """
    return [ach for ach in ACHIEVEMENT_DEFINITIONS if ach.tier == tier]


def get_all_achievement_ids() -> list[str]:
    """获取所有成就 ID 列表"""
    return [ach.achievement_id for ach in ACHIEVEMENT_DEFINITIONS]


def get_achievement_count() -> int:
    """获取成就总数"""
    return len(ACHIEVEMENT_DEFINITIONS)


def get_achievement_count_by_category() -> dict[AchievementCategory, int]:
    """获取各类别成就数量统计"""
    counts: dict[AchievementCategory, int] = {
        AchievementCategory.CODING: 0,
        AchievementCategory.FARMING: 0,
        AchievementCategory.SOCIAL: 0,
        AchievementCategory.ECONOMY: 0,
        AchievementCategory.SPECIAL: 0,
    }
    for ach in ACHIEVEMENT_DEFINITIONS:
        counts[ach.category] += 1
    return counts


def get_achievement_count_by_tier() -> dict[AchievementTier, int]:
    """获取各稀有度成就数量统计"""
    counts: dict[AchievementTier, int] = {
        AchievementTier.COMMON: 0,
        AchievementTier.RARE: 0,
        AchievementTier.EPIC: 0,
        AchievementTier.LEGENDARY: 0,
    }
    for ach in ACHIEVEMENT_DEFINITIONS:
        counts[ach.tier] += 1
    return counts


# 初始化时验证配置
def _validate_achievements() -> None:
    """验证成就配置的完整性"""
    achievement_ids = set()

    for ach in ACHIEVEMENT_DEFINITIONS:
        # 检查 ID 唯一性
        if ach.achievement_id in achievement_ids:
            raise ValueError(f"重复的成就 ID: {ach.achievement_id}")
        achievement_ids.add(ach.achievement_id)

        # 检查必需字段
        if not ach.achievement_id:
            raise ValueError("成就 ID 不能为空")
        if not ach.title or not ach.title_zh:
            raise ValueError(f"成就 {ach.achievement_id} 缺少标题")
        if not ach.description:
            raise ValueError(f"成就 {ach.achievement_id} 缺少描述")
        if not ach.requirement_type:
            raise ValueError(f"成就 {ach.achievement_id} 缺少条件类型")
        if not ach.reward:
            raise ValueError(f"成就 {ach.achievement_id} 缺少奖励配置")


# 执行验证
_validate_achievements()
