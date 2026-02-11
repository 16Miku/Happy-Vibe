"""活动追踪 API 路由

提供活动记录、能量计算触发、心流状态查询等端点。
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.energy_calculator import EnergyCalculator
from src.core.flow_detector import FlowDetector
from src.core.models import Activity, QualityMetrics, ToolUsage
from src.storage.database import get_db
from src.storage.models import CodingActivity, Player

router = APIRouter(prefix="/api/activity", tags=["activity"])

# 全局实例
_energy_calculator = EnergyCalculator()
_flow_detector = FlowDetector()

# 内存中的活动会话存储（简化实现，生产环境应使用 Redis）
_active_sessions: dict[str, dict] = {}


# ============== Pydantic 模型 ==============


class ToolUsageSchema(BaseModel):
    """工具使用统计"""

    read: int = Field(default=0, ge=0, description="文件读取次数")
    write: int = Field(default=0, ge=0, description="文件写入次数")
    bash: int = Field(default=0, ge=0, description="命令执行次数")
    search: int = Field(default=0, ge=0, description="搜索次数")


class QualityMetricsSchema(BaseModel):
    """代码质量指标"""

    success_rate: float = Field(default=0.5, ge=0, le=1, description="成功执行率")
    iteration_count: int = Field(default=1, ge=1, description="迭代次数")
    lines_changed: int = Field(default=0, ge=0, description="改动代码行数")
    files_affected: int = Field(default=0, ge=0, description="影响文件数")
    languages: list[str] = Field(default_factory=list, description="使用的编程语言")
    tool_usage: ToolUsageSchema = Field(
        default_factory=ToolUsageSchema, description="工具使用统计"
    )


class StartActivityRequest(BaseModel):
    """开始活动请求"""

    player_id: str = Field(default="default", description="玩家ID")
    source: str = Field(default="claude_code", description="数据来源")


class StartActivityResponse(BaseModel):
    """开始活动响应"""

    session_id: str = Field(..., description="会话ID")
    started_at: datetime = Field(..., description="开始时间")
    message: str = Field(..., description="消息")


class UpdateActivityRequest(BaseModel):
    """更新活动请求"""

    session_id: str = Field(..., description="会话ID")
    quality: Optional[QualityMetricsSchema] = Field(
        default=None, description="质量指标"
    )
    last_interaction_gap: Optional[float] = Field(
        default=None, ge=0, description="距离上次交互的间隔(秒)"
    )


class FlowProgressItem(BaseModel):
    """心流进度项"""

    current: float = Field(..., description="当前值")
    target: float = Field(..., description="目标值")
    progress: float = Field(..., ge=0, le=1, description="进度 (0-1)")
    met: bool = Field(..., description="是否满足条件")


class FlowStatusResponse(BaseModel):
    """心流状态响应"""

    is_active: bool = Field(..., description="是否处于心流状态")
    started_at: Optional[datetime] = Field(default=None, description="心流开始时间")
    duration_minutes: float = Field(default=0, description="心流持续时长")
    trigger_reason: str = Field(default="", description="触发原因")
    progress: dict[str, FlowProgressItem] = Field(
        default_factory=dict, description="各条件进度"
    )


class UpdateActivityResponse(BaseModel):
    """更新活动响应"""

    session_id: str = Field(..., description="会话ID")
    duration_minutes: float = Field(..., description="持续时长(分钟)")
    flow_status: FlowStatusResponse = Field(..., description="心流状态")
    estimated_energy: int = Field(..., description="预估能量")


class EnergyBreakdownSchema(BaseModel):
    """能量计算分解"""

    base: float = Field(..., description="基础能量")
    time_bonus: float = Field(..., description="时间加成倍数")
    quality_bonus: float = Field(..., description="质量加成倍数")
    streak_bonus: float = Field(..., description="连续签到加成倍数")
    flow_bonus: float = Field(..., description="心流状态加成倍数")


class RewardSchema(BaseModel):
    """奖励结果"""

    vibe_energy: int = Field(..., description="Vibe能量")
    experience: int = Field(..., description="经验值")
    code_essence: int = Field(..., description="代码精华")
    breakdown: EnergyBreakdownSchema = Field(..., description="能量分解")


class EndActivityRequest(BaseModel):
    """结束活动请求"""

    session_id: str = Field(..., description="会话ID")
    quality: Optional[QualityMetricsSchema] = Field(
        default=None, description="最终质量指标"
    )


class EndActivityResponse(BaseModel):
    """结束活动响应"""

    session_id: str = Field(..., description="会话ID")
    started_at: datetime = Field(..., description="开始时间")
    ended_at: datetime = Field(..., description="结束时间")
    duration_minutes: float = Field(..., description="持续时长(分钟)")
    was_in_flow: bool = Field(..., description="是否处于心流状态")
    reward: RewardSchema = Field(..., description="奖励")
    message: str = Field(..., description="消息")


class CurrentActivityResponse(BaseModel):
    """当前活动状态响应"""

    has_active_session: bool = Field(..., description="是否有活动会话")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    duration_minutes: float = Field(default=0, description="持续时长(分钟)")
    flow_status: Optional[FlowStatusResponse] = Field(
        default=None, description="心流状态"
    )
    estimated_energy: int = Field(default=0, description="预估能量")


class ActivityHistoryItem(BaseModel):
    """活动历史项"""

    activity_id: str = Field(..., description="活动ID")
    started_at: datetime = Field(..., description="开始时间")
    ended_at: Optional[datetime] = Field(default=None, description="结束时间")
    duration_seconds: int = Field(..., description="持续时长(秒)")
    source: str = Field(..., description="数据来源")
    energy_earned: int = Field(..., description="获得能量")
    exp_earned: int = Field(..., description="获得经验")
    essence_earned: int = Field(..., description="获得代码精华")
    is_flow_state: bool = Field(..., description="是否心流状态")


class ActivityHistoryResponse(BaseModel):
    """活动历史响应"""

    total: int = Field(..., description="总数")
    items: list[ActivityHistoryItem] = Field(..., description="活动列表")


# ============== 辅助函数 ==============


def get_db_session():
    """获取数据库会话依赖"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


def _convert_to_core_quality(schema: QualityMetricsSchema) -> QualityMetrics:
    """将 Pydantic 模型转换为核心模型"""
    tool_usage = ToolUsage(
        read=schema.tool_usage.read,
        write=schema.tool_usage.write,
        bash=schema.tool_usage.bash,
        search=schema.tool_usage.search,
    )
    return QualityMetrics(
        success_rate=schema.success_rate,
        iteration_count=schema.iteration_count,
        lines_changed=schema.lines_changed,
        files_affected=schema.files_affected,
        languages=schema.languages,
        tool_usage=tool_usage,
    )


def _build_flow_status_response(
    activity: Activity, last_interaction_gap: Optional[float] = None
) -> FlowStatusResponse:
    """构建心流状态响应"""
    flow_state = _flow_detector.detect(activity, last_interaction_gap)
    progress = _flow_detector.get_progress(activity)

    progress_items = {}
    for key, value in progress.items():
        progress_items[key] = FlowProgressItem(
            current=value["current"],
            target=value["target"],
            progress=value["progress"],
            met=value["met"],
        )

    return FlowStatusResponse(
        is_active=flow_state.is_active,
        started_at=flow_state.started_at,
        duration_minutes=flow_state.duration_minutes,
        trigger_reason=flow_state.trigger_reason,
        progress=progress_items,
    )


# ============== API 端点 ==============


@router.post("/start", response_model=StartActivityResponse)
async def start_activity(
    request: StartActivityRequest,
    db_session: Session = Depends(get_db_session),
) -> StartActivityResponse:
    """开始活动追踪

    创建新的活动会话，开始记录编码活动。
    """
    # 获取玩家ID（可选，不传则使用默认）
    player_id = request.player_id if request.player_id else "default"

    # 检查玩家是否存在，不存在则创建
    player = db_session.query(Player).filter_by(player_id=player_id).first()
    if not player:
        # 自动创建默认玩家
        player = Player(
            player_id=player_id,
            username="DefaultPlayer",
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
        )
        db_session.add(player)
        db_session.commit()

    # 检查是否已有活动会话
    for existing_session_id, session_data in _active_sessions.items():
        if session_data["player_id"] == player_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"玩家已有活动会话: {existing_session_id}",
            )

    # 创建新会话
    new_session_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    _active_sessions[new_session_id] = {
        "player_id": player_id,
        "source": request.source,
        "started_at": started_at,
        "quality": QualityMetrics(),
        "consecutive_days": player.consecutive_days,
        "last_interaction_gap": None,
    }

    return StartActivityResponse(
        session_id=new_session_id,
        started_at=started_at,
        message="活动追踪已开始",
    )


@router.post("/update", response_model=UpdateActivityResponse)
async def update_activity(request: UpdateActivityRequest) -> UpdateActivityResponse:
    """更新活动进度

    更新当前活动的质量指标和交互信息，返回心流状态和预估能量。
    """
    if request.session_id not in _active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {request.session_id}",
        )

    session_data = _active_sessions[request.session_id]

    # 更新质量指标
    if request.quality:
        session_data["quality"] = _convert_to_core_quality(request.quality)

    # 更新交互间隔
    if request.last_interaction_gap is not None:
        session_data["last_interaction_gap"] = request.last_interaction_gap

    # 计算持续时长
    started_at = session_data["started_at"]
    now = datetime.utcnow()
    duration_minutes = (now - started_at).total_seconds() / 60

    # 构建 Activity 对象
    activity = Activity(
        session_id=request.session_id,
        started_at=started_at,
        duration_minutes=duration_minutes,
        consecutive_minutes=duration_minutes,
        consecutive_days=session_data["consecutive_days"],
        quality=session_data["quality"],
    )

    # 检测心流状态
    flow_status = _build_flow_status_response(
        activity, session_data.get("last_interaction_gap")
    )
    activity.is_in_flow_state = flow_status.is_active

    # 预估能量
    estimated_energy = _energy_calculator.estimate_energy(
        duration_minutes=duration_minutes,
        consecutive_minutes=duration_minutes,
        quality_score=session_data["quality"].success_rate,
        consecutive_days=session_data["consecutive_days"],
        is_flow_state=flow_status.is_active,
    )

    return UpdateActivityResponse(
        session_id=request.session_id,
        duration_minutes=duration_minutes,
        flow_status=flow_status,
        estimated_energy=estimated_energy,
    )


@router.post("/end", response_model=EndActivityResponse)
async def end_activity(
    request: EndActivityRequest,
    db_session: Session = Depends(get_db_session),
) -> EndActivityResponse:
    """结束活动并计算奖励

    结束当前活动会话，计算最终奖励并保存到数据库。
    """
    if request.session_id not in _active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {request.session_id}",
        )

    session_data = _active_sessions[request.session_id]

    # 更新最终质量指标
    if request.quality:
        session_data["quality"] = _convert_to_core_quality(request.quality)

    # 计算时间
    started_at = session_data["started_at"]
    ended_at = datetime.utcnow()
    duration_minutes = (ended_at - started_at).total_seconds() / 60
    duration_seconds = int((ended_at - started_at).total_seconds())

    # 构建 Activity 对象
    activity = Activity(
        session_id=request.session_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_minutes=duration_minutes,
        consecutive_minutes=duration_minutes,
        consecutive_days=session_data["consecutive_days"],
        quality=session_data["quality"],
    )

    # 检测心流状态
    flow_state = _flow_detector.detect(
        activity, session_data.get("last_interaction_gap")
    )
    activity.is_in_flow_state = flow_state.is_active

    # 计算奖励
    reward = _energy_calculator.calculate(activity)

    # 保存到数据库
    quality = session_data["quality"]
    metrics_json = json.dumps(
        {
            "success_rate": quality.success_rate,
            "iteration_count": quality.iteration_count,
            "lines_changed": quality.lines_changed,
            "files_affected": quality.files_affected,
            "languages": quality.languages,
            "tool_usage": {
                "read": quality.tool_usage.read,
                "write": quality.tool_usage.write,
                "bash": quality.tool_usage.bash,
                "search": quality.tool_usage.search,
            },
        }
    )

    coding_activity = CodingActivity(
        player_id=session_data["player_id"],
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        source=session_data["source"],
        energy_earned=reward.vibe_energy,
        exp_earned=reward.experience,
        essence_earned=reward.code_essence,
        is_flow_state=flow_state.is_active,
        flow_duration_seconds=(
            int(flow_state.duration_minutes * 60) if flow_state.is_active else 0
        ),
        metrics_json=metrics_json,
    )

    db_session.add(coding_activity)

    # 更新玩家资源
    player = (
        db_session.query(Player)
        .filter_by(player_id=session_data["player_id"])
        .first()
    )
    if player:
        player.vibe_energy = min(
            player.vibe_energy + reward.vibe_energy, player.max_vibe_energy
        )
        player.experience += reward.experience

    db_session.commit()

    # 清理会话
    del _active_sessions[request.session_id]

    return EndActivityResponse(
        session_id=request.session_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_minutes=duration_minutes,
        was_in_flow=flow_state.is_active,
        reward=RewardSchema(
            vibe_energy=reward.vibe_energy,
            experience=reward.experience,
            code_essence=reward.code_essence,
            breakdown=EnergyBreakdownSchema(
                base=reward.breakdown.base,
                time_bonus=reward.breakdown.time_bonus,
                quality_bonus=reward.breakdown.quality_bonus,
                streak_bonus=reward.breakdown.streak_bonus,
                flow_bonus=reward.breakdown.flow_bonus,
            ),
        ),
        message="活动已结束，奖励已发放",
    )


@router.get("/current", response_model=CurrentActivityResponse)
async def get_current_activity(player_id: str) -> CurrentActivityResponse:
    """获取当前活动状态

    查询指定玩家的当前活动会话状态。
    """
    # 查找玩家的活动会话
    for session_id, session_data in _active_sessions.items():
        if session_data["player_id"] == player_id:
            started_at = session_data["started_at"]
            now = datetime.utcnow()
            duration_minutes = (now - started_at).total_seconds() / 60

            # 构建 Activity 对象
            activity = Activity(
                session_id=session_id,
                started_at=started_at,
                duration_minutes=duration_minutes,
                consecutive_minutes=duration_minutes,
                consecutive_days=session_data["consecutive_days"],
                quality=session_data["quality"],
            )

            # 获取心流状态
            flow_status = _build_flow_status_response(
                activity, session_data.get("last_interaction_gap")
            )

            # 预估能量
            estimated_energy = _energy_calculator.estimate_energy(
                duration_minutes=duration_minutes,
                consecutive_minutes=duration_minutes,
                quality_score=session_data["quality"].success_rate,
                consecutive_days=session_data["consecutive_days"],
                is_flow_state=flow_status.is_active,
            )

            return CurrentActivityResponse(
                has_active_session=True,
                session_id=session_id,
                started_at=started_at,
                duration_minutes=duration_minutes,
                flow_status=flow_status,
                estimated_energy=estimated_energy,
            )

    # 没有找到活动会话
    return CurrentActivityResponse(
        has_active_session=False,
        duration_minutes=0,
        estimated_energy=0,
    )


@router.get("/history", response_model=ActivityHistoryResponse)
async def get_activity_history(
    player_id: str,
    limit: int = 20,
    offset: int = 0,
    db_session: Session = Depends(get_db_session),
) -> ActivityHistoryResponse:
    """获取活动历史

    查询指定玩家的历史活动记录。
    """
    # 查询总数
    total = (
        db_session.query(CodingActivity).filter_by(player_id=player_id).count()
    )

    # 查询活动列表
    activities = (
        db_session.query(CodingActivity)
        .filter_by(player_id=player_id)
        .order_by(CodingActivity.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [
        ActivityHistoryItem(
            activity_id=activity.activity_id,
            started_at=activity.started_at,
            ended_at=activity.ended_at,
            duration_seconds=activity.duration_seconds,
            source=activity.source,
            energy_earned=activity.energy_earned,
            exp_earned=activity.exp_earned,
            essence_earned=activity.essence_earned,
            is_flow_state=activity.is_flow_state,
        )
        for activity in activities
    ]

    return ActivityHistoryResponse(total=total, items=items)


@router.get("/flow-status", response_model=FlowStatusResponse)
async def get_flow_status(player_id: str) -> FlowStatusResponse:
    """获取心流状态

    查询指定玩家当前的心流状态和进度。
    """
    # 查找玩家的活动会话
    for session_id, session_data in _active_sessions.items():
        if session_data["player_id"] == player_id:
            started_at = session_data["started_at"]
            now = datetime.utcnow()
            duration_minutes = (now - started_at).total_seconds() / 60

            # 构建 Activity 对象
            activity = Activity(
                session_id=session_id,
                started_at=started_at,
                duration_minutes=duration_minutes,
                consecutive_minutes=duration_minutes,
                consecutive_days=session_data["consecutive_days"],
                quality=session_data["quality"],
            )

            return _build_flow_status_response(
                activity, session_data.get("last_interaction_gap")
            )

    # 没有活动会话，返回默认状态
    return FlowStatusResponse(
        is_active=False,
        trigger_reason="没有活动会话",
        progress={},
    )
