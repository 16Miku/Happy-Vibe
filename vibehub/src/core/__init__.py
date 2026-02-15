"""核心模块 - 能量计算与心流检测"""

from src.core.models import Activity, VibeReward, QualityMetrics, FlowState
from src.core.energy_calculator import EnergyCalculator
from src.core.flow_detector import FlowDetector
from src.core.achievement_data import (
    ACHIEVEMENT_DEFINITIONS,
    get_achievement_by_id,
    get_achievements_by_category,
)
from src.core.achievement_manager import AchievementManager, get_achievement_manager

__all__ = [
    "Activity",
    "VibeReward",
    "QualityMetrics",
    "FlowState",
    "EnergyCalculator",
    "FlowDetector",
    "ACHIEVEMENT_DEFINITIONS",
    "get_achievement_by_id",
    "get_achievements_by_category",
    "AchievementManager",
    "get_achievement_manager",
]
