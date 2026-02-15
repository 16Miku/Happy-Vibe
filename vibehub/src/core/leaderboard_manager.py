"""排行榜管理器

提供排行榜计算、更新、查询和快照功能。
"""

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage.models import (
    AchievementProgress,
    Guild,
    Leaderboard,
    LeaderboardSnapshot,
    LeaderboardType,
    Player,
    Season,
)


class LeaderboardManager:
    """排行榜管理器

    负责排行榜数据的计算、更新和查询。
    """

    def __init__(self, session: Session):
        """初始化排行榜管理器

        Args:
            session: 数据库会话
        """
        self.session = session

    async def get_leaderboard(
        self,
        leaderboard_type: str,
        season_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """获取排行榜数据

        Args:
            leaderboard_type: 排行榜类型 (individual/guild/achievement)
            season_id: 赛季 ID，默认为当前赛季
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            排行榜数据
        """
        # 获取赛季
        if season_id is None:
            season = await self._get_current_season()
            if not season:
                return {"error": "No active season found"}
            season_id = season.season_id
        else:
            stmt = select(Season).where(Season.season_id == season_id)
            season = self.session.execute(stmt).scalar_one_or_none()
            if not season:
                return {"error": "Season not found"}

        # 获取或创建排行榜
        stmt = select(Leaderboard).where(
            Leaderboard.season_id == season_id,
            Leaderboard.leaderboard_type == leaderboard_type,
        )
        leaderboard = self.session.execute(stmt).scalar_one_or_none()

        if not leaderboard:
            # 创建新排行榜
            leaderboard = Leaderboard(
                leaderboard_id=str(uuid4()),
                season_id=season_id,
                leaderboard_type=leaderboard_type,
                rankings_json=None,
                update_frequency="hourly",
            )
            self.session.add(leaderboard)
            self.session.commit()
            self.session.refresh(leaderboard)

        # 解析排行数据
        rankings = []
        if leaderboard.rankings_json:
            rankings = json.loads(leaderboard.rankings_json)

        # 应用分页
        total = len(rankings)
        rankings = rankings[offset : offset + limit]

        return {
            "leaderboard_id": leaderboard.leaderboard_id,
            "season_id": season_id,
            "leaderboard_type": leaderboard_type,
            "total": total,
            "offset": offset,
            "limit": limit,
            "last_updated": leaderboard.last_updated.isoformat(),
            "rankings": rankings,
        }

    async def update_leaderboard(
        self,
        leaderboard_type: str,
        season_id: str,
    ) -> dict[str, Any]:
        """更新排行榜数据

        Args:
            leaderboard_type: 排行榜类型
            season_id: 赛季 ID

        Returns:
            更新后的排行榜数据
        """
        # 验证赛季存在
        stmt = select(Season).where(Season.season_id == season_id)
        season = self.session.execute(stmt).scalar_one_or_none()
        if not season:
            raise ValueError(f"Season not found: {season_id}")

        # 获取或创建排行榜
        stmt = select(Leaderboard).where(
            Leaderboard.season_id == season_id,
            Leaderboard.leaderboard_type == leaderboard_type,
        )
        leaderboard = self.session.execute(stmt).scalar_one_or_none()

        if not leaderboard:
            leaderboard = Leaderboard(
                leaderboard_id=str(uuid4()),
                season_id=season_id,
                leaderboard_type=leaderboard_type,
                rankings_json=None,
                update_frequency="hourly",
            )
            self.session.add(leaderboard)

        # 计算排名
        rankings = await self._calculate_rankings(leaderboard_type, season_id)

        # 保存排行数据
        leaderboard.rankings_json = json.dumps(rankings)
        leaderboard.last_updated = datetime.utcnow()
        self.session.commit()
        self.session.refresh(leaderboard)

        return {
            "leaderboard_id": leaderboard.leaderboard_id,
            "season_id": season_id,
            "leaderboard_type": leaderboard_type,
            "total": len(rankings),
            "last_updated": leaderboard.last_updated.isoformat(),
        }

    async def get_player_rank(
        self,
        player_id: str,
        leaderboard_type: str,
        season_id: str | None = None,
    ) -> dict[str, Any]:
        """获取玩家排名

        Args:
            player_id: 玩家 ID
            leaderboard_type: 排行榜类型
            season_id: 赛季 ID，默认为当前赛季

        Returns:
            玩家排名信息
        """
        # 获取赛季
        if season_id is None:
            season = await self._get_current_season()
            if not season:
                return {"error": "No active season found"}
            season_id = season.season_id

        # 获取排行榜
        stmt = select(Leaderboard).where(
            Leaderboard.season_id == season_id,
            Leaderboard.leaderboard_type == leaderboard_type,
        )
        leaderboard = self.session.execute(stmt).scalar_one_or_none()

        if not leaderboard or not leaderboard.rankings_json:
            # 排行榜不存在，计算玩家分数和排名
            return await self._calculate_player_rank(
                player_id, leaderboard_type, season_id
            )

        # 查找玩家排名
        rankings = json.loads(leaderboard.rankings_json)

        for entry in rankings:
            if entry.get("entity_id") == player_id:
                return {
                    "player_id": player_id,
                    "rank": entry.get("rank", 0),
                    "score": entry.get("score", 0),
                    "entity_name": entry.get("entity_name", ""),
                    "on_leaderboard": True,
                    "total": len(rankings),
                }

        # 玩家不在排行榜上，计算其分数和排名
        return await self._calculate_player_rank(player_id, leaderboard_type, season_id)

    async def create_snapshot(
        self,
        leaderboard_type: str,
        season_id: str,
    ) -> dict[str, Any]:
        """创建排行榜快照

        Args:
            leaderboard_type: 排行榜类型
            season_id: 赛季 ID

        Returns:
            快照信息
        """
        # 获取排行榜
        stmt = select(Leaderboard).where(
            Leaderboard.season_id == season_id,
            Leaderboard.leaderboard_type == leaderboard_type,
        )
        leaderboard = self.session.execute(stmt).scalar_one_or_none()

        if not leaderboard:
            raise ValueError(f"Leaderboard not found for type: {leaderboard_type}")

        # 创建快照
        snapshot = LeaderboardSnapshot(
            snapshot_id=str(uuid4()),
            leaderboard_id=leaderboard.leaderboard_id,
            season_id=season_id,
            snapshot_time=datetime.utcnow(),
            rankings_json=leaderboard.rankings_json,
        )

        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)

        return {
            "snapshot_id": snapshot.snapshot_id,
            "leaderboard_id": leaderboard.leaderboard_id,
            "season_id": season_id,
            "snapshot_time": snapshot.snapshot_time.isoformat(),
        }

    async def get_snapshots(
        self,
        season_id: str,
        leaderboard_type: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """获取排行榜快照列表

        Args:
            season_id: 赛季 ID
            leaderboard_type: 排行榜类型（可选）
            limit: 返回数量限制

        Returns:
            快照列表
        """
        query = (
            select(LeaderboardSnapshot, Leaderboard)
            .join(Leaderboard, LeaderboardSnapshot.leaderboard_id == Leaderboard.leaderboard_id)
            .where(LeaderboardSnapshot.season_id == season_id)
        )

        if leaderboard_type:
            query = query.filter(Leaderboard.leaderboard_type == leaderboard_type)

        query = query.order_by(LeaderboardSnapshot.snapshot_time.desc()).limit(limit)

        results = self.session.execute(query).all()

        snapshots = []
        for snapshot, leaderboard in results:
            entry = {
                "snapshot_id": snapshot.snapshot_id,
                "leaderboard_type": leaderboard.leaderboard_type,
                "snapshot_time": snapshot.snapshot_time.isoformat(),
            }
            if snapshot.rankings_json:
                entry["entry_count"] = len(json.loads(snapshot.rankings_json))
            snapshots.append(entry)

        return snapshots

    async def _calculate_rankings(
        self,
        leaderboard_type: str,
        season_id: str,
    ) -> list[dict[str, Any]]:
        """计算排名数据

        Args:
            leaderboard_type: 排行榜类型
            season_id: 赛季 ID

        Returns:
            排名列表
        """
        if leaderboard_type == LeaderboardType.INDIVIDUAL.value:
            return await self._calculate_individual_rankings(season_id)
        elif leaderboard_type == LeaderboardType.GUILD.value:
            return await self._calculate_guild_rankings(season_id)
        elif leaderboard_type == LeaderboardType.ACHIEVEMENT.value:
            return await self._calculate_achievement_rankings(season_id)
        return []

    async def _calculate_individual_rankings(
        self, season_id: str
    ) -> list[dict[str, Any]]:
        """计算个人排名

        评分公式: score = level * 100 + exp / 10 + gold / 1000

        Args:
            season_id: 赛季 ID

        Returns:
            排名列表
        """
        stmt = select(Player).order_by(Player.level.desc(), Player.experience.desc())
        players = self.session.execute(stmt).scalars().all()

        rankings = []
        for player in players:
            score = player.level * 100 + player.experience / 10 + player.gold / 1000
            rankings.append(
                {
                    "rank": 0,  # 后续设置
                    "entity_id": player.player_id,
                    "entity_name": player.username,
                    "level": player.level,
                    "experience": player.experience,
                    "gold": player.gold,
                    "score": round(score, 2),
                }
            )

        # 按分数排序
        rankings.sort(key=lambda x: x["score"], reverse=True)

        # 添加排名
        for i, entry in enumerate(rankings):
            entry["rank"] = i + 1

        return rankings

    async def _calculate_guild_rankings(self, season_id: str) -> list[dict[str, Any]]:
        """计算公会排名

        评分公式: score = level * 500 + member_count * 50 + contribution_points

        Args:
            season_id: 赛季 ID

        Returns:
            排名列表
        """
        stmt = select(Guild).where(Guild.disbanded_at.is_(None))
        guilds = self.session.execute(stmt).scalars().all()

        rankings = []
        for guild in guilds:
            score = (
                guild.level * 500
                + guild.member_count * 50
                + guild.contribution_points
            )
            rankings.append(
                {
                    "rank": 0,
                    "entity_id": guild.guild_id,
                    "entity_name": guild.guild_name,
                    "level": guild.level,
                    "member_count": guild.member_count,
                    "contribution_points": guild.contribution_points,
                    "score": score,
                }
            )

        # 按分数排序
        rankings.sort(key=lambda x: x["score"], reverse=True)

        # 添加排名
        for i, entry in enumerate(rankings):
            entry["rank"] = i + 1

        return rankings

    async def _calculate_achievement_rankings(
        self, season_id: str
    ) -> list[dict[str, Any]]:
        """计算成就排名

        评分公式: score = common * 1 + rare * 5 + epic * 20 + legendary * 100

        Args:
            season_id: 赛季 ID

        Returns:
            排名列表
        """
        # 获取所有玩家
        stmt = select(Player)
        players = self.session.execute(stmt).scalars().all()

        rankings = []

        for player in players:
            # 获取玩家已完成的成就数量
            achievement_stmt = select(AchievementProgress).where(
                AchievementProgress.player_id == player.player_id,
                AchievementProgress.is_completed == True,
            )
            achievements = self.session.execute(achievement_stmt).scalars().all()

            # 简化处理：按完成数量计算分数
            # 实际应该根据成就稀有度加权
            score = len(achievements)

            rankings.append(
                {
                    "rank": 0,
                    "entity_id": player.player_id,
                    "entity_name": player.username,
                    "achievement_count": score,
                    "score": score,
                }
            )

        # 按分数排序
        rankings.sort(key=lambda x: x["score"], reverse=True)

        # 添加排名
        for i, entry in enumerate(rankings):
            entry["rank"] = i + 1

        return rankings

    async def _calculate_player_rank(
        self,
        player_id: str,
        leaderboard_type: str,
        season_id: str,
    ) -> dict[str, Any]:
        """计算玩家的分数和排名

        Args:
            player_id: 玩家 ID
            leaderboard_type: 排行榜类型
            season_id: 赛季 ID

        Returns:
            玩家排名信息
        """
        if leaderboard_type == LeaderboardType.INDIVIDUAL.value:
            return await self._calculate_individual_player_rank(player_id, season_id)
        elif leaderboard_type == LeaderboardType.ACHIEVEMENT.value:
            return await self._calculate_achievement_player_rank(player_id, season_id)
        else:
            return {
                "player_id": player_id,
                "error": f"Unsupported leaderboard type for player rank: {leaderboard_type}",
            }

    async def _calculate_individual_player_rank(
        self, player_id: str, season_id: str
    ) -> dict[str, Any]:
        """计算玩家在个人排行榜中的排名

        Args:
            player_id: 玩家 ID
            season_id: 赛季 ID

        Returns:
            玩家排名信息
        """
        # 获取玩家
        stmt = select(Player).where(Player.player_id == player_id)
        player = self.session.execute(stmt).scalar_one_or_none()

        if not player:
            return {"player_id": player_id, "error": "Player not found"}

        # 计算玩家分数
        player_score = player.level * 100 + player.experience / 10 + player.gold / 1000

        # 计算排名（有多少玩家分数更高）
        rank_stmt = select(Player).where(
            Player.level * 100 + Player.experience / 10 + Player.gold / 1000 > player_score
        )
        higher_count = self.session.execute(rank_stmt).count()
        rank = higher_count + 1

        # 获取总玩家数
        total_stmt = select(Player)
        total = self.session.execute(total_stmt).count()

        return {
            "player_id": player_id,
            "entity_name": player.username,
            "rank": rank,
            "total": total,
            "score": round(player_score, 2),
            "level": player.level,
            "experience": player.experience,
            "gold": player.gold,
            "on_leaderboard": rank <= 100,  # 假设前100名上榜
            "percentile": round((1 - rank / total) * 100, 1) if total > 0 else 0,
        }

    async def _calculate_achievement_player_rank(
        self, player_id: str, season_id: str
    ) -> dict[str, Any]:
        """计算玩家在成就排行榜中的排名

        Args:
            player_id: 玩家 ID
            season_id: 赛季 ID

        Returns:
            玩家排名信息
        """
        # 获取玩家
        stmt = select(Player).where(Player.player_id == player_id)
        player = self.session.execute(stmt).scalar_one_or_none()

        if not player:
            return {"player_id": player_id, "error": "Player not found"}

        # 获取玩家已完成的成就数量
        achievement_stmt = select(AchievementProgress).where(
            AchievementProgress.player_id == player_id,
            AchievementProgress.is_completed == True,
        )
        achievements = self.session.execute(achievement_stmt).scalars().all()
        player_score = len(achievements)

        # 计算所有玩家的成就数量
        all_players = self.session.execute(select(Player)).scalars().all()

        scores = []
        for p in all_players:
            stmt = select(AchievementProgress).where(
                AchievementProgress.player_id == p.player_id,
                AchievementProgress.is_completed == True,
            )
            count = self.session.execute(stmt).count()
            scores.append(count)

        # 计算排名
        higher_count = sum(1 for s in scores if s > player_score)
        rank = higher_count + 1

        return {
            "player_id": player_id,
            "entity_name": player.username,
            "rank": rank,
            "total": len(scores),
            "score": player_score,
            "achievement_count": player_score,
            "on_leaderboard": rank <= 100,
            "percentile": round((1 - rank / len(scores)) * 100, 1) if scores else 0,
        }

    async def _get_current_season(self) -> Season | None:
        """获取当前激活的赛季

        Returns:
            当前赛季，不存在则返回 None
        """
        now = datetime.utcnow()
        stmt = select(Season).where(
            Season.is_active == True,
            Season.start_time <= now,
            Season.end_time >= now,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    async def generate_leaderboard(
        self,
        season_id: str,
        leaderboard_type: str,
    ) -> Leaderboard:
        """生成指定赛季和类型的排行榜

        Args:
            season_id: 赛季 ID
            leaderboard_type: 排行榜类型

        Returns:
            创建的排行榜对象
        """
        # 检查是否已存在
        stmt = select(Leaderboard).where(
            Leaderboard.season_id == season_id,
            Leaderboard.leaderboard_type == leaderboard_type,
        )
        existing = self.session.execute(stmt).scalar_one_or_none()

        if existing:
            return existing

        # 创建新排行榜
        leaderboard = Leaderboard(
            leaderboard_id=str(uuid4()),
            season_id=season_id,
            leaderboard_type=leaderboard_type,
            rankings_json=None,
            update_frequency="hourly",
        )

        self.session.add(leaderboard)
        self.session.commit()
        self.session.refresh(leaderboard)

        return leaderboard

    async def get_top_players(
        self,
        leaderboard_type: str,
        season_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """获取排行榜前 N 名玩家

        Args:
            leaderboard_type: 排行榜类型
            season_id: 赛季 ID，默认为当前赛季
            limit: 返回数量

        Returns:
            前 N 名玩家列表
        """
        result = await self.get_leaderboard(leaderboard_type, season_id, limit)

        if "error" in result:
            return []

        return result.get("rankings", [])
