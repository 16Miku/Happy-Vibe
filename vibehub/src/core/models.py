"""核心数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ActivityType(str, Enum):
    """活动类型"""
    PROMPT = "prompt"      # 提示/对话
    EDIT = "edit"          # 编辑代码
    READ = "read"          # 读取文件
    EXECUTE = "execute"    # 执行命令


@dataclass
class ToolUsage:
    """工具使用统计"""
    read: int = 0          # 文件读取次数
    write: int = 0         # 文件写入次数
    bash: int = 0          # 命令执行次数
    search: int = 0        # 搜索次数

    def total(self) -> int:
        """总使用次数"""
        return self.read + self.write + self.bash + self.search

    def variety_count(self) -> int:
        """使用的工具种类数"""
        count = 0
        if self.read > 0:
            count += 1
        if self.write > 0:
            count += 1
        if self.bash > 0:
            count += 1
        if self.search > 0:
            count += 1
        return count


@dataclass
class QualityMetrics:
    """代码质量指标"""
    success_rate: float = 0.5      # 成功执行率 (0-1)
    iteration_count: int = 1       # 迭代次数
    lines_changed: int = 0         # 改动代码行数
    files_affected: int = 0        # 影响文件数
    languages: list[str] = field(default_factory=list)  # 使用的编程语言
    tool_usage: ToolUsage = field(default_factory=ToolUsage)


@dataclass
class Activity:
    """编码活动数据"""
    session_id: str                          # 会话ID
    started_at: datetime                     # 开始时间
    ended_at: Optional[datetime] = None      # 结束时间
    duration_minutes: float = 0              # 持续时长(分钟)
    consecutive_minutes: float = 0           # 连续编码时长(分钟)
    consecutive_days: int = 0                # 连续签到天数
    activity_type: ActivityType = ActivityType.PROMPT
    quality: QualityMetrics = field(default_factory=QualityMetrics)
    is_in_flow_state: bool = False           # 是否处于心流状态

    def __post_init__(self):
        """计算持续时长"""
        if self.ended_at and self.started_at:
            delta = self.ended_at - self.started_at
            self.duration_minutes = delta.total_seconds() / 60


@dataclass
class FlowState:
    """心流状态"""
    is_active: bool = False                  # 是否处于心流状态
    started_at: Optional[datetime] = None    # 心流开始时间
    duration_minutes: float = 0              # 心流持续时长
    trigger_reason: str = ""                 # 触发原因

    # 心流判定条件状态
    duration_met: bool = False               # 时长条件满足
    gap_met: bool = False                    # 间隔条件满足
    success_rate_met: bool = False           # 成功率条件满足
    tool_variety_met: bool = False           # 工具多样性条件满足
    output_met: bool = False                 # 产出条件满足


@dataclass
class EnergyBreakdown:
    """能量计算分解"""
    base: float = 0                          # 基础能量
    time_bonus: float = 1.0                  # 时间加成倍数
    quality_bonus: float = 1.0               # 质量加成倍数
    streak_bonus: float = 1.0                # 连续签到加成倍数
    flow_bonus: float = 1.0                  # 心流状态加成倍数


@dataclass
class VibeReward:
    """Vibe奖励结果"""
    vibe_energy: int = 0                     # Vibe能量
    experience: int = 0                      # 经验值
    code_essence: int = 0                    # 代码精华(稀有资源)
    breakdown: EnergyBreakdown = field(default_factory=EnergyBreakdown)

    def __str__(self) -> str:
        return (
            f"VibeReward(energy={self.vibe_energy}, "
            f"exp={self.experience}, essence={self.code_essence})"
        )
