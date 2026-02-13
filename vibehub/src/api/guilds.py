"""公会系统 API

提供公会相关的 REST API 端点。
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.multiplayer.connection_manager import connection_manager
from src.multiplayer.models import GUILD_LEVEL_CONFIG, GuildRole

router = APIRouter(prefix="/api/guilds", tags=["guilds"])


# ==================== 请求/响应模型 ====================


class GuildCreate(BaseModel):
    """创建公会请求"""

    name: str = Field(..., min_length=2, max_length=50, description="公会名称")
    description: Optional[str] = Field(None, max_length=500, description="公会描述")
    icon: Optional[str] = Field(None, description="公会图标")
    founder_id: str = Field(..., description="创建者 ID")


class GuildUpdate(BaseModel):
    """更新公会信息"""

    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = None


class GuildJoinRequest(BaseModel):
    """加入公会请求"""

    player_id: str
    guild_id: str
    message: Optional[str] = Field(None, max_length=200)


class MemberRoleUpdate(BaseModel):
    """更新成员角色"""

    operator_id: str = Field(..., description="操作者 ID")
    target_id: str = Field(..., description="目标成员 ID")
    new_role: str = Field(..., description="新角色")


class ContributeRequest(BaseModel):
    """贡献请求"""

    player_id: str
    guild_id: str
    energy_amount: int = Field(..., ge=0, description="贡献的能量数量")


class GuildInfo(BaseModel):
    """公会信息"""

    guild_id: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    level: int
    experience: int
    exp_to_next_level: int
    member_count: int
    max_members: int
    total_energy_contributed: int
    features: list[str]
    created_at: str


class GuildMemberInfo(BaseModel):
    """公会成员信息"""

    player_id: str
    username: str
    level: int
    role: str
    contribution: int
    is_online: bool
    joined_at: str


# ==================== 内存存储 (临时) ====================

# 公会数据: guild_id -> guild_data
_guilds: dict[str, dict] = {}

# 公会成员: guild_id -> {player_id: member_data}
_guild_members: dict[str, dict[str, dict]] = {}

# 玩家所属公会: player_id -> guild_id
_player_guilds: dict[str, str] = {}

# 加入申请: request_id -> request_data
_join_requests: dict[str, dict] = {}

# 玩家信息缓存
_player_cache: dict[str, dict] = {}


def _get_guild_level_config(level: int) -> dict:
    """获取公会等级配置"""
    for lvl in sorted(GUILD_LEVEL_CONFIG.keys(), reverse=True):
        if level >= lvl:
            return GUILD_LEVEL_CONFIG[lvl]
    return GUILD_LEVEL_CONFIG[1]


def _calculate_exp_to_next_level(level: int, current_exp: int) -> int:
    """计算升级所需经验"""
    for lvl in sorted(GUILD_LEVEL_CONFIG.keys()):
        if lvl > level:
            return GUILD_LEVEL_CONFIG[lvl]["exp_required"] - current_exp
    return 0  # 已满级


def _get_unlocked_features(level: int) -> list[str]:
    """获取已解锁的功能"""
    features = []
    for lvl, config in GUILD_LEVEL_CONFIG.items():
        if level >= lvl:
            features.extend(config.get("features", []))
    return features


# ==================== API 端点 ====================


@router.post("/create")
async def create_guild(request: GuildCreate) -> dict:
    """创建公会

    Args:
        request: 创建请求

    Returns:
        创建结果
    """
    founder_id = request.founder_id

    # 检查玩家是否已在公会中
    if founder_id in _player_guilds:
        raise HTTPException(status_code=400, detail="Already in a guild")

    # 检查公会名是否已存在
    for guild in _guilds.values():
        if guild["name"] == request.name:
            raise HTTPException(status_code=400, detail="Guild name already exists")

    # 创建公会
    import uuid

    guild_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    _guilds[guild_id] = {
        "guild_id": guild_id,
        "name": request.name,
        "description": request.description,
        "icon": request.icon,
        "level": 1,
        "experience": 0,
        "max_members": 10,
        "total_energy_contributed": 0,
        "total_crops_harvested": 0,
        "territory_json": None,
        "warehouse_json": None,
        "skills_json": None,
        "created_at": now,
        "updated_at": now,
    }

    # 添加创建者为会长
    _guild_members[guild_id] = {
        founder_id: {
            "player_id": founder_id,
            "role": GuildRole.LEADER.value,
            "contribution": 0,
            "joined_at": now,
            "last_active_at": now,
        }
    }

    _player_guilds[founder_id] = guild_id

    return {
        "success": True,
        "guild_id": guild_id,
        "message": "Guild created successfully",
    }


@router.get("/list")
async def list_guilds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="搜索公会名"),
) -> dict:
    """获取公会列表

    Args:
        page: 页码
        page_size: 每页数量
        search: 搜索关键词

    Returns:
        公会列表
    """
    guilds = list(_guilds.values())

    # 搜索过滤
    if search:
        guilds = [g for g in guilds if search.lower() in g["name"].lower()]

    # 按等级和成员数排序
    guilds.sort(key=lambda x: (-x["level"], -len(_guild_members.get(x["guild_id"], {}))))

    # 分页
    total = len(guilds)
    start = (page - 1) * page_size
    end = start + page_size
    guilds = guilds[start:end]

    # 添加成员数
    result = []
    for guild in guilds:
        guild_id = guild["guild_id"]
        member_count = len(_guild_members.get(guild_id, {}))
        config = _get_guild_level_config(guild["level"])

        result.append(
            {
                **guild,
                "member_count": member_count,
                "max_members": config["max_members"],
                "features": _get_unlocked_features(guild["level"]),
            }
        )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "guilds": result,
    }


@router.get("/{guild_id}")
async def get_guild(guild_id: str) -> dict:
    """获取公会详情

    Args:
        guild_id: 公会 ID

    Returns:
        公会详情
    """
    if guild_id not in _guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    guild = _guilds[guild_id]
    members = _guild_members.get(guild_id, {})
    config = _get_guild_level_config(guild["level"])

    # 构建成员列表
    member_list = []
    for player_id, member_data in members.items():
        player_info = _player_cache.get(player_id, {})
        is_online = connection_manager.is_online(player_id)

        member_list.append(
            GuildMemberInfo(
                player_id=player_id,
                username=player_info.get("username", f"Player_{player_id[:8]}"),
                level=player_info.get("level", 1),
                role=member_data["role"],
                contribution=member_data["contribution"],
                is_online=is_online,
                joined_at=member_data["joined_at"],
            ).model_dump()
        )

    # 按角色和贡献排序
    role_order = {GuildRole.LEADER.value: 0, GuildRole.OFFICER.value: 1, GuildRole.MEMBER.value: 2}
    member_list.sort(key=lambda x: (role_order.get(x["role"], 99), -x["contribution"]))

    return {
        "guild": GuildInfo(
            guild_id=guild_id,
            name=guild["name"],
            description=guild["description"],
            icon=guild["icon"],
            level=guild["level"],
            experience=guild["experience"],
            exp_to_next_level=_calculate_exp_to_next_level(guild["level"], guild["experience"]),
            member_count=len(members),
            max_members=config["max_members"],
            total_energy_contributed=guild["total_energy_contributed"],
            features=_get_unlocked_features(guild["level"]),
            created_at=guild["created_at"],
        ).model_dump(),
        "members": member_list,
        "online_count": sum(1 for m in member_list if m["is_online"]),
    }


@router.put("/{guild_id}")
async def update_guild(guild_id: str, request: GuildUpdate, operator_id: str = Query(...)) -> dict:
    """更新公会信息

    Args:
        guild_id: 公会 ID
        request: 更新数据
        operator_id: 操作者 ID

    Returns:
        更新结果
    """
    if guild_id not in _guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    # 检查权限
    members = _guild_members.get(guild_id, {})
    if operator_id not in members:
        raise HTTPException(status_code=403, detail="Not a member")

    member_role = members[operator_id]["role"]
    if member_role not in [GuildRole.LEADER.value, GuildRole.OFFICER.value]:
        raise HTTPException(status_code=403, detail="No permission")

    # 更新信息
    guild = _guilds[guild_id]
    if request.name:
        # 检查名称是否重复
        for g in _guilds.values():
            if g["guild_id"] != guild_id and g["name"] == request.name:
                raise HTTPException(status_code=400, detail="Guild name already exists")
        guild["name"] = request.name

    if request.description is not None:
        guild["description"] = request.description

    if request.icon is not None:
        guild["icon"] = request.icon

    guild["updated_at"] = datetime.utcnow().isoformat()

    return {
        "success": True,
        "message": "Guild updated",
    }


@router.post("/join")
async def request_join_guild(request: GuildJoinRequest) -> dict:
    """申请加入公会

    Args:
        request: 加入请求

    Returns:
        申请结果
    """
    player_id = request.player_id
    guild_id = request.guild_id

    # 检查玩家是否已在公会中
    if player_id in _player_guilds:
        raise HTTPException(status_code=400, detail="Already in a guild")

    # 检查公会是否存在
    if guild_id not in _guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    # 检查公会是否已满
    guild = _guilds[guild_id]
    members = _guild_members.get(guild_id, {})
    config = _get_guild_level_config(guild["level"])

    if len(members) >= config["max_members"]:
        raise HTTPException(status_code=400, detail="Guild is full")

    # 创建申请
    import uuid

    request_id = str(uuid.uuid4())
    _join_requests[request_id] = {
        "request_id": request_id,
        "player_id": player_id,
        "guild_id": guild_id,
        "message": request.message,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }

    # 通知公会管理员
    for member_id, member_data in members.items():
        if member_data["role"] in [GuildRole.LEADER.value, GuildRole.OFFICER.value]:
            if connection_manager.is_online(member_id):
                player_info = _player_cache.get(player_id, {})
                await connection_manager.send_personal(
                    member_id,
                    {
                        "type": "guild_join_request",
                        "request_id": request_id,
                        "player_id": player_id,
                        "player_username": player_info.get("username", f"Player_{player_id[:8]}"),
                        "message": request.message,
                    },
                )

    return {
        "success": True,
        "request_id": request_id,
        "message": "Join request sent",
    }


@router.post("/join/{request_id}/respond")
async def respond_join_request(
    request_id: str,
    accept: bool = Query(...),
    operator_id: str = Query(...),
) -> dict:
    """处理加入申请

    Args:
        request_id: 申请 ID
        accept: 是否接受
        operator_id: 操作者 ID

    Returns:
        处理结果
    """
    if request_id not in _join_requests:
        raise HTTPException(status_code=404, detail="Request not found")

    req = _join_requests[request_id]
    if req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    guild_id = req["guild_id"]
    player_id = req["player_id"]

    # 检查权限
    members = _guild_members.get(guild_id, {})
    if operator_id not in members:
        raise HTTPException(status_code=403, detail="Not a member")

    member_role = members[operator_id]["role"]
    if member_role not in [GuildRole.LEADER.value, GuildRole.OFFICER.value]:
        raise HTTPException(status_code=403, detail="No permission")

    if accept:
        # 再次检查公会是否已满
        guild = _guilds[guild_id]
        config = _get_guild_level_config(guild["level"])

        if len(members) >= config["max_members"]:
            raise HTTPException(status_code=400, detail="Guild is full")

        # 添加成员
        now = datetime.utcnow().isoformat()
        _guild_members[guild_id][player_id] = {
            "player_id": player_id,
            "role": GuildRole.MEMBER.value,
            "contribution": 0,
            "joined_at": now,
            "last_active_at": now,
        }
        _player_guilds[player_id] = guild_id
        req["status"] = "accepted"

        # 通知申请者
        if connection_manager.is_online(player_id):
            await connection_manager.send_personal(
                player_id,
                {
                    "type": "guild_join_accepted",
                    "guild_id": guild_id,
                    "guild_name": guild["name"],
                },
            )

        # 广播给公会成员
        room_id = f"guild_{guild_id}"
        player_info = _player_cache.get(player_id, {})
        await connection_manager.broadcast_to_room(
            room_id,
            {
                "type": "guild_member_joined",
                "player_id": player_id,
                "player_username": player_info.get("username", f"Player_{player_id[:8]}"),
            },
        )

        return {
            "success": True,
            "message": "Member added to guild",
        }
    else:
        req["status"] = "rejected"

        # 通知申请者
        if connection_manager.is_online(player_id):
            await connection_manager.send_personal(
                player_id,
                {
                    "type": "guild_join_rejected",
                    "guild_id": guild_id,
                },
            )

        return {
            "success": True,
            "message": "Request rejected",
        }


@router.delete("/{guild_id}/members/{player_id}")
async def remove_member(
    guild_id: str,
    player_id: str,
    operator_id: str = Query(...),
) -> dict:
    """移除公会成员 / 退出公会

    Args:
        guild_id: 公会 ID
        player_id: 目标成员 ID
        operator_id: 操作者 ID

    Returns:
        操作结果
    """
    if guild_id not in _guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    members = _guild_members.get(guild_id, {})
    if player_id not in members:
        raise HTTPException(status_code=404, detail="Member not found")

    target_role = members[player_id]["role"]

    # 自己退出
    if operator_id == player_id:
        if target_role == GuildRole.LEADER.value:
            raise HTTPException(status_code=400, detail="Leader cannot leave, transfer leadership first")

        del _guild_members[guild_id][player_id]
        del _player_guilds[player_id]

        return {
            "success": True,
            "message": "Left guild",
        }

    # 踢人
    if operator_id not in members:
        raise HTTPException(status_code=403, detail="Not a member")

    operator_role = members[operator_id]["role"]

    # 权限检查
    if operator_role == GuildRole.MEMBER.value:
        raise HTTPException(status_code=403, detail="No permission")

    if operator_role == GuildRole.OFFICER.value and target_role != GuildRole.MEMBER.value:
        raise HTTPException(status_code=403, detail="Cannot kick officer or leader")

    del _guild_members[guild_id][player_id]
    del _player_guilds[player_id]

    # 通知被踢者
    if connection_manager.is_online(player_id):
        await connection_manager.send_personal(
            player_id,
            {
                "type": "guild_kicked",
                "guild_id": guild_id,
            },
        )

    return {
        "success": True,
        "message": "Member removed",
    }


@router.post("/{guild_id}/role")
async def update_member_role(guild_id: str, request: MemberRoleUpdate) -> dict:
    """更新成员角色

    Args:
        guild_id: 公会 ID
        request: 角色更新请求

    Returns:
        更新结果
    """
    if guild_id not in _guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    members = _guild_members.get(guild_id, {})

    if request.operator_id not in members:
        raise HTTPException(status_code=403, detail="Not a member")

    if request.target_id not in members:
        raise HTTPException(status_code=404, detail="Target member not found")

    operator_role = members[request.operator_id]["role"]
    target_role = members[request.target_id]["role"]

    # 只有会长可以更改角色
    if operator_role != GuildRole.LEADER.value:
        raise HTTPException(status_code=403, detail="Only leader can change roles")

    # 验证新角色
    try:
        new_role = GuildRole(request.new_role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    # 转让会长
    if new_role == GuildRole.LEADER:
        members[request.operator_id]["role"] = GuildRole.OFFICER.value
        members[request.target_id]["role"] = GuildRole.LEADER.value

        return {
            "success": True,
            "message": "Leadership transferred",
        }

    members[request.target_id]["role"] = new_role.value

    return {
        "success": True,
        "message": "Role updated",
    }


@router.post("/{guild_id}/contribute")
async def contribute_to_guild(guild_id: str, request: ContributeRequest) -> dict:
    """向公会贡献能量

    Args:
        guild_id: 公会 ID
        request: 贡献请求

    Returns:
        贡献结果
    """
    if guild_id not in _guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    members = _guild_members.get(guild_id, {})
    if request.player_id not in members:
        raise HTTPException(status_code=403, detail="Not a member")

    guild = _guilds[guild_id]
    member = members[request.player_id]

    # 计算公会经验 (1 经验 / 100 能量)
    exp_gained = request.energy_amount // 100

    # 更新数据
    guild["total_energy_contributed"] += request.energy_amount
    guild["experience"] += exp_gained
    member["contribution"] += request.energy_amount
    member["last_active_at"] = datetime.utcnow().isoformat()

    # 检查升级
    level_up = False
    old_level = guild["level"]

    for lvl in sorted(GUILD_LEVEL_CONFIG.keys()):
        if lvl > old_level and guild["experience"] >= GUILD_LEVEL_CONFIG[lvl]["exp_required"]:
            guild["level"] = lvl
            guild["max_members"] = GUILD_LEVEL_CONFIG[lvl]["max_members"]
            level_up = True

    # 广播升级消息
    if level_up:
        room_id = f"guild_{guild_id}"
        await connection_manager.broadcast_to_room(
            room_id,
            {
                "type": "guild_level_up",
                "guild_id": guild_id,
                "new_level": guild["level"],
                "new_features": _get_unlocked_features(guild["level"]),
            },
        )

    return {
        "success": True,
        "energy_contributed": request.energy_amount,
        "exp_gained": exp_gained,
        "total_contribution": member["contribution"],
        "guild_level": guild["level"],
        "level_up": level_up,
    }


@router.get("/{guild_id}/requests")
async def get_join_requests(
    guild_id: str,
    operator_id: str = Query(...),
) -> dict:
    """获取公会加入申请列表

    Args:
        guild_id: 公会 ID
        operator_id: 操作者 ID

    Returns:
        申请列表
    """
    if guild_id not in _guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    members = _guild_members.get(guild_id, {})
    if operator_id not in members:
        raise HTTPException(status_code=403, detail="Not a member")

    member_role = members[operator_id]["role"]
    if member_role not in [GuildRole.LEADER.value, GuildRole.OFFICER.value]:
        raise HTTPException(status_code=403, detail="No permission")

    # 获取待处理的申请
    requests = []
    for req in _join_requests.values():
        if req["guild_id"] == guild_id and req["status"] == "pending":
            player_info = _player_cache.get(req["player_id"], {})
            requests.append(
                {
                    **req,
                    "player_username": player_info.get("username", f"Player_{req['player_id'][:8]}"),
                    "player_level": player_info.get("level", 1),
                }
            )

    return {
        "guild_id": guild_id,
        "requests": requests,
        "count": len(requests),
    }


@router.get("/player/{player_id}")
async def get_player_guild(player_id: str) -> dict:
    """获取玩家所属公会

    Args:
        player_id: 玩家 ID

    Returns:
        公会信息
    """
    if player_id not in _player_guilds:
        return {
            "has_guild": False,
            "guild": None,
        }

    guild_id = _player_guilds[player_id]
    guild = _guilds.get(guild_id)

    if not guild:
        return {
            "has_guild": False,
            "guild": None,
        }

    members = _guild_members.get(guild_id, {})
    member = members.get(player_id, {})
    config = _get_guild_level_config(guild["level"])

    return {
        "has_guild": True,
        "guild": {
            "guild_id": guild_id,
            "name": guild["name"],
            "level": guild["level"],
            "member_count": len(members),
            "max_members": config["max_members"],
        },
        "membership": {
            "role": member.get("role", GuildRole.MEMBER.value),
            "contribution": member.get("contribution", 0),
            "joined_at": member.get("joined_at"),
        },
    }


# ==================== 内部函数 ====================


def update_player_cache(player_id: str, info: dict) -> None:
    """更新玩家信息缓存"""
    _player_cache[player_id] = {**_player_cache.get(player_id, {}), **info}


def get_guild_id(player_id: str) -> Optional[str]:
    """获取玩家所属公会 ID"""
    return _player_guilds.get(player_id)


def get_guild_members(guild_id: str) -> list[str]:
    """获取公会成员 ID 列表"""
    return list(_guild_members.get(guild_id, {}).keys())
