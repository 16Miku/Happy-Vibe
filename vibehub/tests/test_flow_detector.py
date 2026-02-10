"""心流检测器单元测试"""

import pytest
from datetime import datetime, timedelta

from src.core.models import Activity, QualityMetrics, ToolUsage
from src.core.flow_detector import FlowDetector


class TestFlowDetector:
    """心流检测器测试"""

    @pytest.fixture
    def detector(self) -> FlowDetector:
        """创建检测器实例"""
        return FlowDetector(
            min_duration=45,
            max_gap=300,
            min_success_rate=0.8,
            min_tool_variety=3,
            min_output_per_30min=100,
        )

    @pytest.fixture
    def flow_activity(self) -> Activity:
        """创建满足心流条件的活动"""
        now = datetime.now()
        return Activity(
            session_id="flow-session",
            started_at=now - timedelta(minutes=60),
            ended_at=now,
            duration_minutes=60,
            consecutive_minutes=60,
            quality=QualityMetrics(
                success_rate=0.9,
                iteration_count=3,
                lines_changed=250,  # 250行/60分钟 = 125行/30分钟
                languages=["python", "typescript"],
                tool_usage=ToolUsage(read=10, write=8, bash=5, search=3),
            ),
        )

    @pytest.fixture
    def non_flow_activity(self) -> Activity:
        """创建不满足心流条件的活动"""
        now = datetime.now()
        return Activity(
            session_id="non-flow-session",
            started_at=now - timedelta(minutes=20),
            ended_at=now,
            duration_minutes=20,
            consecutive_minutes=20,
            quality=QualityMetrics(
                success_rate=0.5,
                iteration_count=10,
                lines_changed=30,
                languages=["python"],
                tool_usage=ToolUsage(read=5, write=2),
            ),
        )

    def test_detect_flow_state(self, detector: FlowDetector, flow_activity: Activity):
        """测试心流状态检测"""
        flow_state = detector.detect(flow_activity)

        assert flow_state.is_active is True
        assert flow_state.duration_met is True
        assert flow_state.gap_met is True
        assert flow_state.success_rate_met is True
        assert flow_state.tool_variety_met is True
        assert flow_state.output_met is True
        assert flow_state.trigger_reason == "所有心流条件满足"

    def test_detect_non_flow_state(self, detector: FlowDetector, non_flow_activity: Activity):
        """测试非心流状态检测"""
        flow_state = detector.detect(non_flow_activity)

        assert flow_state.is_active is False
        assert flow_state.duration_met is False  # 20分钟 < 45分钟
        assert flow_state.success_rate_met is False  # 0.5 < 0.8
        assert flow_state.tool_variety_met is False  # 2种 < 3种
        assert flow_state.output_met is False  # 45行/30分钟 < 100行/30分钟

    def test_check_duration(self, detector: FlowDetector):
        """测试时长条件检查"""
        assert detector._check_duration(44) is False
        assert detector._check_duration(45) is True
        assert detector._check_duration(60) is True

    def test_check_gap(self, detector: FlowDetector):
        """测试交互间隔检查"""
        assert detector._check_gap(300) is True
        assert detector._check_gap(301) is False
        assert detector._check_gap(0) is True

    def test_check_success_rate(self, detector: FlowDetector):
        """测试成功率检查"""
        assert detector._check_success_rate(0.79) is False
        assert detector._check_success_rate(0.8) is True
        assert detector._check_success_rate(1.0) is True

    def test_check_tool_variety(self, detector: FlowDetector):
        """测试工具多样性检查"""
        # 2种工具 - 不满足
        quality_2_tools = QualityMetrics(
            tool_usage=ToolUsage(read=5, write=3)
        )
        assert detector._check_tool_variety(quality_2_tools) is False

        # 3种工具 - 满足
        quality_3_tools = QualityMetrics(
            tool_usage=ToolUsage(read=5, write=3, bash=2)
        )
        assert detector._check_tool_variety(quality_3_tools) is True

        # 4种工具 - 满足
        quality_4_tools = QualityMetrics(
            tool_usage=ToolUsage(read=5, write=3, bash=2, search=1)
        )
        assert detector._check_tool_variety(quality_4_tools) is True

    def test_check_output(self, detector: FlowDetector):
        """测试产出检查"""
        # 100行/30分钟 - 刚好满足
        assert detector._check_output(100, 30) is True

        # 50行/30分钟 - 不满足
        assert detector._check_output(50, 30) is False

        # 200行/60分钟 = 100行/30分钟 - 满足
        assert detector._check_output(200, 60) is True

        # 0分钟 - 不满足
        assert detector._check_output(100, 0) is False

    def test_get_progress(self, detector: FlowDetector, non_flow_activity: Activity):
        """测试进度获取"""
        progress = detector.get_progress(non_flow_activity)

        # 检查时长进度
        assert progress["duration"]["current"] == 20
        assert progress["duration"]["target"] == 45
        assert progress["duration"]["progress"] == pytest.approx(20 / 45)
        assert progress["duration"]["met"] is False

        # 检查成功率进度
        assert progress["success_rate"]["current"] == 0.5
        assert progress["success_rate"]["target"] == 0.8
        assert progress["success_rate"]["progress"] == pytest.approx(0.5 / 0.8)
        assert progress["success_rate"]["met"] is False

        # 检查工具多样性进度
        assert progress["tool_variety"]["current"] == 2
        assert progress["tool_variety"]["target"] == 3
        assert progress["tool_variety"]["progress"] == pytest.approx(2 / 3)
        assert progress["tool_variety"]["met"] is False

    def test_get_progress_flow_activity(self, detector: FlowDetector, flow_activity: Activity):
        """测试心流活动的进度"""
        progress = detector.get_progress(flow_activity)

        # 所有条件都应该满足
        assert progress["duration"]["met"] is True
        assert progress["success_rate"]["met"] is True
        assert progress["tool_variety"]["met"] is True
        assert progress["output"]["met"] is True

        # 进度应该都是1.0或更高
        assert progress["duration"]["progress"] >= 1.0
        assert progress["success_rate"]["progress"] >= 1.0
        assert progress["tool_variety"]["progress"] >= 1.0
        assert progress["output"]["progress"] >= 1.0

    def test_unmet_reason(self, detector: FlowDetector, non_flow_activity: Activity):
        """测试未满足条件的原因"""
        flow_state = detector.detect(non_flow_activity)

        assert "编码时长不足45分钟" in flow_state.trigger_reason
        assert "成功率低于80%" in flow_state.trigger_reason
        assert "工具种类少于3种" in flow_state.trigger_reason
        assert "代码产出低于100行/30分钟" in flow_state.trigger_reason

    def test_flow_start_time(self, detector: FlowDetector, flow_activity: Activity):
        """测试心流开始时间计算"""
        flow_state = detector.detect(flow_activity)

        assert flow_state.started_at is not None
        # 心流开始时间应该在活动结束前 (60 - 45) = 15分钟
        expected_start = flow_activity.ended_at - timedelta(minutes=15)
        assert abs((flow_state.started_at - expected_start).total_seconds()) < 1

    def test_reset(self, detector: FlowDetector):
        """测试重置功能"""
        detector._current_flow = "some_state"
        detector._last_activity_time = datetime.now()

        detector.reset()

        assert detector._current_flow is None
        assert detector._last_activity_time is None

    def test_gap_condition_with_explicit_gap(self, detector: FlowDetector, flow_activity: Activity):
        """测试显式提供间隔参数"""
        # 间隔在范围内
        flow_state = detector.detect(flow_activity, last_interaction_gap=100)
        assert flow_state.gap_met is True

        # 间隔超出范围
        flow_state = detector.detect(flow_activity, last_interaction_gap=400)
        assert flow_state.gap_met is False
        assert flow_state.is_active is False

    def test_partial_conditions_met(self, detector: FlowDetector):
        """测试部分条件满足的情况"""
        now = datetime.now()
        # 时长满足，但其他条件不满足
        activity = Activity(
            session_id="partial",
            started_at=now - timedelta(minutes=60),
            ended_at=now,
            duration_minutes=60,
            consecutive_minutes=60,
            quality=QualityMetrics(
                success_rate=0.5,  # 不满足
                lines_changed=50,  # 不满足
                tool_usage=ToolUsage(read=1),  # 不满足
            ),
        )

        flow_state = detector.detect(activity)

        assert flow_state.is_active is False
        assert flow_state.duration_met is True
        assert flow_state.success_rate_met is False
        assert flow_state.tool_variety_met is False
        assert flow_state.output_met is False
