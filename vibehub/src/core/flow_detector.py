"""心流状态检测器"""

from datetime import datetime, timedelta
from typing import Optional

from src.config.settings import settings
from src.core.models import Activity, FlowState, QualityMetrics


class FlowDetector:
    """心流状态检测器

    心流状态判定条件（需同时满足）:
    1. 连续编码时长 ≥ 45分钟
    2. 交互间隔 < 5分钟（无长时间停顿）
    3. 成功率 > 80%（无过多失败尝试）
    4. 工具使用活跃（至少3种不同工具）
    5. 代码产出 > 阈值（如100行/30分钟）

    心流状态效果:
    - Vibe能量获取 +50%
    - 传说品质作物概率提升至15%
    - 解锁特殊成就
    - 获得心流时段记录
    """

    def __init__(
        self,
        min_duration: Optional[int] = None,
        max_gap: Optional[int] = None,
        min_success_rate: Optional[float] = None,
        min_tool_variety: int = 3,
        min_output_per_30min: int = 100,
    ):
        """初始化心流检测器

        Args:
            min_duration: 最小编码时长(分钟)，默认从配置读取
            max_gap: 最大交互间隔(秒)，默认从配置读取
            min_success_rate: 最低成功率，默认从配置读取
            min_tool_variety: 最少工具种类数，默认3种
            min_output_per_30min: 每30分钟最低代码产出行数，默认100行
        """
        self.min_duration = min_duration or settings.FLOW_MIN_DURATION
        self.max_gap = max_gap or settings.FLOW_MAX_GAP
        self.min_success_rate = min_success_rate or settings.FLOW_MIN_SUCCESS_RATE
        self.min_tool_variety = min_tool_variety
        self.min_output_per_30min = min_output_per_30min

        # 内部状态
        self._current_flow: Optional[FlowState] = None
        self._last_activity_time: Optional[datetime] = None

    def detect(
        self,
        activity: Activity,
        last_interaction_gap: Optional[float] = None,
    ) -> FlowState:
        """检测是否处于心流状态

        Args:
            activity: 当前活动数据
            last_interaction_gap: 距离上次交互的间隔(秒)，如果为None则从活动推断

        Returns:
            FlowState: 心流状态信息
        """
        flow_state = FlowState()

        # 1. 检查时长条件
        flow_state.duration_met = self._check_duration(activity.consecutive_minutes)

        # 2. 检查交互间隔条件
        if last_interaction_gap is not None:
            flow_state.gap_met = self._check_gap(last_interaction_gap)
        else:
            # 如果没有提供间隔信息，假设满足条件
            flow_state.gap_met = True

        # 3. 检查成功率条件
        flow_state.success_rate_met = self._check_success_rate(
            activity.quality.success_rate
        )

        # 4. 检查工具多样性条件
        flow_state.tool_variety_met = self._check_tool_variety(activity.quality)

        # 5. 检查产出条件
        flow_state.output_met = self._check_output(
            activity.quality.lines_changed,
            activity.duration_minutes,
        )

        # 判断是否进入心流状态
        flow_state.is_active = all([
            flow_state.duration_met,
            flow_state.gap_met,
            flow_state.success_rate_met,
            flow_state.tool_variety_met,
            flow_state.output_met,
        ])

        # 设置触发原因
        if flow_state.is_active:
            flow_state.trigger_reason = "所有心流条件满足"
            flow_state.started_at = self._calculate_flow_start(activity)
            flow_state.duration_minutes = activity.consecutive_minutes
        else:
            flow_state.trigger_reason = self._get_unmet_reason(flow_state)

        return flow_state

    def _check_duration(self, consecutive_minutes: float) -> bool:
        """检查时长条件

        Args:
            consecutive_minutes: 连续编码时长(分钟)

        Returns:
            是否满足时长条件
        """
        return consecutive_minutes >= self.min_duration

    def _check_gap(self, gap_seconds: float) -> bool:
        """检查交互间隔条件

        Args:
            gap_seconds: 交互间隔(秒)

        Returns:
            是否满足间隔条件
        """
        return gap_seconds <= self.max_gap

    def _check_success_rate(self, success_rate: float) -> bool:
        """检查成功率条件

        Args:
            success_rate: 成功率 (0-1)

        Returns:
            是否满足成功率条件
        """
        return success_rate >= self.min_success_rate

    def _check_tool_variety(self, quality: QualityMetrics) -> bool:
        """检查工具多样性条件

        Args:
            quality: 质量指标

        Returns:
            是否满足工具多样性条件
        """
        return quality.tool_usage.variety_count() >= self.min_tool_variety

    def _check_output(self, lines_changed: int, duration_minutes: float) -> bool:
        """检查产出条件

        Args:
            lines_changed: 改动代码行数
            duration_minutes: 编码时长(分钟)

        Returns:
            是否满足产出条件
        """
        if duration_minutes <= 0:
            return False

        # 计算每30分钟的产出
        output_per_30min = (lines_changed / duration_minutes) * 30
        return output_per_30min >= self.min_output_per_30min

    def _calculate_flow_start(self, activity: Activity) -> datetime:
        """计算心流开始时间

        心流开始时间 = 当前时间 - 连续编码时长 + 最小心流时长

        Args:
            activity: 活动数据

        Returns:
            心流开始时间
        """
        if activity.ended_at:
            current_time = activity.ended_at
        else:
            current_time = datetime.now()

        # 心流开始于达到最小时长的那一刻
        flow_duration = activity.consecutive_minutes - self.min_duration
        return current_time - timedelta(minutes=flow_duration)

    def _get_unmet_reason(self, flow_state: FlowState) -> str:
        """获取未满足条件的原因

        Args:
            flow_state: 心流状态

        Returns:
            未满足条件的描述
        """
        reasons = []

        if not flow_state.duration_met:
            reasons.append(f"编码时长不足{self.min_duration}分钟")

        if not flow_state.gap_met:
            reasons.append(f"交互间隔超过{self.max_gap}秒")

        if not flow_state.success_rate_met:
            reasons.append(f"成功率低于{self.min_success_rate * 100:.0f}%")

        if not flow_state.tool_variety_met:
            reasons.append(f"工具种类少于{self.min_tool_variety}种")

        if not flow_state.output_met:
            reasons.append(f"代码产出低于{self.min_output_per_30min}行/30分钟")

        return "；".join(reasons) if reasons else "未知原因"

    def get_progress(self, activity: Activity) -> dict:
        """获取心流进度

        返回各条件的完成进度，用于UI显示

        Args:
            activity: 活动数据

        Returns:
            各条件的进度信息
        """
        quality = activity.quality

        # 计算产出率
        if activity.duration_minutes > 0:
            output_per_30min = (quality.lines_changed / activity.duration_minutes) * 30
        else:
            output_per_30min = 0

        return {
            "duration": {
                "current": activity.consecutive_minutes,
                "target": self.min_duration,
                "progress": min(activity.consecutive_minutes / self.min_duration, 1.0),
                "met": activity.consecutive_minutes >= self.min_duration,
            },
            "success_rate": {
                "current": quality.success_rate,
                "target": self.min_success_rate,
                "progress": min(quality.success_rate / self.min_success_rate, 1.0),
                "met": quality.success_rate >= self.min_success_rate,
            },
            "tool_variety": {
                "current": quality.tool_usage.variety_count(),
                "target": self.min_tool_variety,
                "progress": min(
                    quality.tool_usage.variety_count() / self.min_tool_variety, 1.0
                ),
                "met": quality.tool_usage.variety_count() >= self.min_tool_variety,
            },
            "output": {
                "current": output_per_30min,
                "target": self.min_output_per_30min,
                "progress": min(output_per_30min / self.min_output_per_30min, 1.0),
                "met": output_per_30min >= self.min_output_per_30min,
            },
        }

    def reset(self) -> None:
        """重置检测器状态"""
        self._current_flow = None
        self._last_activity_time = None
