"""能量计算与发放 API 路由

提供能量计算、发放、历史查询等端点。
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.energy_calculator import EnergyCalculator
from src.core.models import Activity, QualityMetrics, ToolUsage
from src.storage.database import get_db
from src.storage.models import CodingActivity, Player

router = APIRouter(prefix="/api/energy", tags=["energy"])

# 全局能量计算器实例
_energy_calculator = EnergyCalculator()

# 每日能量上限
DAILY_ENERGY_CAP = 5000


# ============== Pydantic 模型 ==============


class ToolUsageInput(BaseModel):
    """工具使用统计输入"""

    read: int = Field(default=0, ge=0, description="文件读取次数")
    write: int = Field(default=0, ge=0, description="文件写入次数")
    bash: int = Field(default=0, ge=0, description="命令执行次数")
    search: int = Field(default=0, ge=0, description="搜索次数")


class QualityMetricsInput(BaseModel):
    """代码质量指标输入"""

    success_rate: float = Field(default=0.5, ge=0, le=1, description="成功执行率")
    iteration_count: int = Field(default=1, ge=1, description="迭代次数")
    lines_changed: int = Field(default=0, ge=0, description="改动代码行数")
    files_affected: int = Field(default=0, ge=0, description="影响文件数")
    languages: list[str] = Field(default_factory=list, description="使用的编程语言")
    tool_usage: ToolUsageInput = Field(default_factory=ToolUsageInput, description="工具使用统计")


class CalculateEnergyRequest(BaseModel):
    """能量计算请求"""

    duration_minutes: float = Field(..., gt=0, description="编码时长(分钟)")
    consecutive_minutes: float | None = Field(default=None, ge=0, description="连续编码时长(分钟)")
    consecutive_days: int = Field(default=0, ge=0, description="连续签到天数")
    is_flow_state: bool = Field(default=False, description="是否处于心流状态")
    quality: QualityMetricsInput | None = Field(default=None, description="质量指标")


class EnergyBreakdownResponse(BaseModel):
    """能量计算分解响应"""

    base: float = Field(..., description="基础能量")
    time_bonus: float = Field(..., description="时间加成倍数")
    quality_bonus: float = Field(..., description="质量加成倍数")
    streak_bonus: float = Field(..., description="连续签到加成倍数")
    flow_bonus: float = Field(..., description="心流状态加成倍数")


class CalculateEnergyResponse(BaseModel):
    """能量计算响应"""

    vibe_energy: int = Field(..., description="计算得到的Vibe能量")
    experience: int = Field(..., description="经验值")
    code_essence: int = Field(..., description="代码精华")
    breakdown: EnergyBreakdownResponse = Field(..., description="能量分解")


class AwardEnergyRequest(BaseModel):
    """能量发放请求"""

    player_id: str = Field(..., description="玩家ID")
    duration_minutes: float = Field(..., gt=0, description="编码时长(分钟)")
    consecutive_minutes: float | None = Field(default=None, ge=0, description="连续编码时长(分钟)")
    consecutive_days: int = Field(default=0, ge=0, description="连续签到天数")
    is_flow_state: bool = Field(default=False, description="是否处于心流状态")
    quality: QualityMetricsInput | None = Field(default=None, description="质量指标")
    source: str = Field(default="claude_code", description="数据来源")


class AwardEnergyResponse(BaseModel):
    """能量发放响应"""

    player_id: str = Field(..., description="玩家ID")
    awarded_energy: int = Field(..., description="实际发放的能量")
    awarded_experience: int = Field(..., description="实际发放的经验")
    awarded_essence: int = Field(..., description="实际发放的代码精华")
    current_energy: int = Field(..., description="当前能量")
    max_energy: int = Field(..., description="能量上限")
    daily_earned: int = Field(..., description="今日已获得能量")
    daily_cap: int = Field(..., description="每日能量上限")
    capped: bool = Field(..., description="是否触发上限")
    breakdown: EnergyBreakdownResponse = Field(..., description="能量分解")
    message: str = Field(..., description="消息")


class EnergyHistoryItem(BaseModel):
    """能量历史项"""

    activity_id: str = Field(..., description="活动ID")
    earned_at: datetime = Field(..., description="获得时间")
    energy_earned: int = Field(..., description="获得能量")
    exp_earned: int = Field(..., description="获得经验")
    essence_earned: int = Field(..., description="获得代码精华")
    duration_seconds: int = Field(..., description="活动时长(秒)")
    source: str = Field(..., description="数据来源")
    is_flow_state: bool = Field(..., description="是否心流状态")


class EnergyHistoryResponse(BaseModel):
    """能量历史响应"""

    player_id: str = Field(..., description="玩家ID")
    total: int = Field(..., description="总记录数")
    daily_earned: int = Field(..., description="今日已获得能量")
    daily_cap: int = Field(..., description="每日能量上限")
    items: list[EnergyHistoryItem] = Field(..., description="历史记录")


class EnergyStatusResponse(BaseModel):
    """能量状态响应"""

    player_id: str = Field(..., description="玩家ID")
    current_energy: int = Field(..., description="当前能量")
    max_energy: int = Field(..., description="能量上限")
    daily_earned: int = Field(..., description="今日已获得能量")
    daily_cap: int = Field(..., description="每日能量上限")
    daily_remaining: int = Field(..., description="今日剩余可获得能量")


# ============== 辅助函数 ==============


def get_db_session():
    """获取数据库会话依赖"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


def _convert_to_core_quality(schema: QualityMetricsInput) -> QualityMetrics:
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


def _get_daily_earned_energy(db_session: Session, player_id: str) -> int:
    """获取玩家今日已获得的能量"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    result = (
        db_session.query(func.sum(CodingActivity.energy_earned))
        .filter(
            CodingActivity.player_id == player_id,
            CodingActivity.started_at >= today_start,
        )
        .scalar()
    )

    return result or 0


def _check_energy_cap(
    db_session: Session, player_id: str, energy_to_award: int
) -> tuple[int, bool]:
    """检查能量上限，返回实际可发放能量和是否触发上限

    Args:
        db_session: 数据库会话
        player_id: 玩家ID
        energy_to_award: 计划发放的能量

    Returns:
        (实际可发放能量, 是否触发上限)
    """
    daily_earned = _get_daily_earned_energy(db_session, player_id)
    remaining = max(0, DAILY_ENERGY_CAP - daily_earned)

    if energy_to_award <= remaining:
        return energy_to_award, False
    else:
        return remaining, True


# ============== API 端点 ==============


@router.post("/calculate", response_model=CalculateEnergyResponse)
async def calculate_energy(request: CalculateEnergyRequest) -> CalculateEnergyResponse:
    """计算能量值

    根据活动数据计算能量值，不进行实际发放。
    用于预览或客户端显示。
    """
    # 准备质量指标
    quality = QualityMetrics()
    if request.quality:
        quality = _convert_to_core_quality(request.quality)

    # 构建 Activity 对象
    consecutive_minutes = request.consecutive_minutes or request.duration_minutes
    activity = Activity(
        session_id="calculate-preview",
        started_at=datetime.utcnow(),
        duration_minutes=request.duration_minutes,
        consecutive_minutes=consecutive_minutes,
        consecutive_days=request.consecutive_days,
        quality=quality,
        is_in_flow_state=request.is_flow_state,
    )

    # 计算奖励
    reward = _energy_calculator.calculate(activity)

    return CalculateEnergyResponse(
        vibe_energy=reward.vibe_energy,
        experience=reward.experience,
        code_essence=reward.code_essence,
        breakdown=EnergyBreakdownResponse(
            base=reward.breakdown.base,
            time_bonus=reward.breakdown.time_bonus,
            quality_bonus=reward.breakdown.quality_bonus,
            streak_bonus=reward.breakdown.streak_bonus,
            flow_bonus=reward.breakdown.flow_bonus,
        ),
    )


@router.post("/award", response_model=AwardEnergyResponse)
async def award_energy(
    request: AwardEnergyRequest,
    db_session: Session = Depends(get_db_session),
) -> AwardEnergyResponse:
    """发放能量到玩家账户

    计算能量并发放到指定玩家账户，同时记录活动历史。
    会检查每日能量上限。
    """
    # 检查玩家是否存在
    player = db_session.query(Player).filter_by(player_id=request.player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {request.player_id}",
        )

    # 准备质量指标
    quality = QualityMetrics()
    if request.quality:
        quality = _convert_to_core_quality(request.quality)

    # 构建 Activity 对象
    consecutive_minutes = request.consecutive_minutes or request.duration_minutes
    started_at = datetime.utcnow() - timedelta(minutes=request.duration_minutes)
    ended_at = datetime.utcnow()

    activity = Activity(
        session_id=f"award-{datetime.utcnow().timestamp()}",
        started_at=started_at,
        ended_at=ended_at,
        duration_minutes=request.duration_minutes,
        consecutive_minutes=consecutive_minutes,
        consecutive_days=request.consecutive_days,
        quality=quality,
        is_in_flow_state=request.is_flow_state,
    )

    # 计算奖励
    reward = _energy_calculator.calculate(activity)

    # 检查每日能量上限
    actual_energy, capped = _check_energy_cap(db_session, request.player_id, reward.vibe_energy)

    # 按比例调整经验和代码精华
    if capped and reward.vibe_energy > 0:
        ratio = actual_energy / reward.vibe_energy
        actual_experience = int(reward.experience * ratio)
        actual_essence = int(reward.code_essence * ratio)
    else:
        actual_experience = reward.experience
        actual_essence = reward.code_essence

    # 更新玩家资源
    new_energy = min(player.vibe_energy + actual_energy, player.max_vibe_energy)
    player.vibe_energy = new_energy
    player.experience += actual_experience

    # 记录活动
    coding_activity = CodingActivity(
        player_id=request.player_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=int(request.duration_minutes * 60),
        source=request.source,
        energy_earned=actual_energy,
        exp_earned=actual_experience,
        essence_earned=actual_essence,
        is_flow_state=request.is_flow_state,
        flow_duration_seconds=(int(request.duration_minutes * 60) if request.is_flow_state else 0),
    )
    db_session.add(coding_activity)
    db_session.commit()

    # 获取今日已获得能量
    daily_earned = _get_daily_earned_energy(db_session, request.player_id)

    # 构建消息
    if capped:
        message = f"能量发放成功（已触发每日上限，实际发放 {actual_energy}/{reward.vibe_energy}）"
    else:
        message = "能量发放成功"

    return AwardEnergyResponse(
        player_id=request.player_id,
        awarded_energy=actual_energy,
        awarded_experience=actual_experience,
        awarded_essence=actual_essence,
        current_energy=player.vibe_energy,
        max_energy=player.max_vibe_energy,
        daily_earned=daily_earned,
        daily_cap=DAILY_ENERGY_CAP,
        capped=capped,
        breakdown=EnergyBreakdownResponse(
            base=reward.breakdown.base,
            time_bonus=reward.breakdown.time_bonus,
            quality_bonus=reward.breakdown.quality_bonus,
            streak_bonus=reward.breakdown.streak_bonus,
            flow_bonus=reward.breakdown.flow_bonus,
        ),
        message=message,
    )


@router.get("/history", response_model=EnergyHistoryResponse)
async def get_energy_history(
    player_id: str,
    limit: int = 20,
    offset: int = 0,
    db_session: Session = Depends(get_db_session),
) -> EnergyHistoryResponse:
    """获取能量获取历史

    查询指定玩家的能量获取历史记录。
    """
    # 检查玩家是否存在
    player = db_session.query(Player).filter_by(player_id=player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    # 查询总数
    total = db_session.query(CodingActivity).filter_by(player_id=player_id).count()

    # 查询活动列表
    activities = (
        db_session.query(CodingActivity)
        .filter_by(player_id=player_id)
        .order_by(CodingActivity.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 获取今日已获得能量
    daily_earned = _get_daily_earned_energy(db_session, player_id)

    items = [
        EnergyHistoryItem(
            activity_id=activity.activity_id,
            earned_at=activity.started_at,
            energy_earned=activity.energy_earned,
            exp_earned=activity.exp_earned,
            essence_earned=activity.essence_earned,
            duration_seconds=activity.duration_seconds,
            source=activity.source,
            is_flow_state=activity.is_flow_state,
        )
        for activity in activities
    ]

    return EnergyHistoryResponse(
        player_id=player_id,
        total=total,
        daily_earned=daily_earned,
        daily_cap=DAILY_ENERGY_CAP,
        items=items,
    )


@router.get("/status", response_model=EnergyStatusResponse)
async def get_energy_status(
    player_id: str,
    db_session: Session = Depends(get_db_session),
) -> EnergyStatusResponse:
    """获取能量状态

    查询指定玩家的当前能量状态，包括每日上限信息。
    """
    # 检查玩家是否存在
    player = db_session.query(Player).filter_by(player_id=player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    # 获取今日已获得能量
    daily_earned = _get_daily_earned_energy(db_session, player_id)
    daily_remaining = max(0, DAILY_ENERGY_CAP - daily_earned)

    return EnergyStatusResponse(
        player_id=player_id,
        current_energy=player.vibe_energy,
        max_energy=player.max_vibe_energy,
        daily_earned=daily_earned,
        daily_cap=DAILY_ENERGY_CAP,
        daily_remaining=daily_remaining,
    )
