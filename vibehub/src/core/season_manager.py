"""赛季管理器

提供赛季创建、管理、结束和奖励发放功能。
"""

import json
from datetime import datetime, timedelta
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
    SeasonType,
)


class SeasonManager:
    """赛季管理器

    负责赛季的生命周期管理，包括创建、查询、结束和奖励发放。
    """

    def __init__(self, session: Session):
        """初始化赛季管理器

        Args:
            session: 数据库会话
        """
        self.session = session

    async def create_season(
        self,
        season_name: str,
        season_number: int,
        season_type: str,
        start_time: datetime,
        end_time: datetime,
        reward_tiers: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """创建新赛季

        Args:
            season_name: 赛季名称
            season_number: 赛季编号
            season_type: 赛季类型 (regular/special/championship)
            start_time: 开始时间
            end_time: 结束时间
            reward_tiers: 奖励层级配置

        Returns:
            创建的赛季信息
        """
        season = Season(
            season_id=str(uuid4()),
            season_name=season_name,
            season_number=season_number,
            season_type=season_type,
            start_time=start_time,
            end_time=end_time,
            reward_tiers=json.dumps(reward_tiers) if reward_tiers else None,
            is_active=False,
        )

        self.session.add(season)
        self.session.commit()
        self.session.refresh(season)

        return self._season_to_dict(season)

    async def get_current_season(self) -> dict[str, Any] | None:
        """获取当前激活的赛季

        Returns:
            当前赛季信息，如果没有则返回 None
        """
        now = datetime.utcnow()
        stmt = select(Season).where(
            Season.is_active == True,
            Season.start_time <= now,
            Season.end_time >= now,
        )
        result = self.session.execute(stmt).scalar_one_or_none()

        return self._season_to_dict(result) if result else None

    async def get_season(self, season_id: str) -> dict[str, Any] | None:
        """获取指定赛季信息

        Args:
            season_id: 赛季 ID

        Returns:
            赛季信息，不存在则返回 None
        """
        stmt = select(Season).where(Season.season_id == season_id)
        result = self.session.execute(stmt).scalar_one_or_none()

        return self._season_to_dict(result) if result else None

    async def get_season_list(
        self, include_inactive: bool = True, limit: int = 10
    ) -> list[dict[str, Any]]:
        """获取赛季列表

        Args:
            include_inactive: 是否包含非激活赛季
            limit: 返回数量限制

        Returns:
            赛季列表
        """
        stmt = select(Season).order_by(Season.season_number.desc()).limit(limit)
        result = self.session.execute(stmt).scalars().all()

        return [self._season_to_dict(s) for s in result]

    async def activate_season(self, season_id: str) -> dict[str, Any]:
        """激活赛季

        先关闭其他激活的赛季，再激活指定赛季。

        Args:
            season_id: 赛季 ID

        Returns:
            更新后的赛季信息
        """
        # 关闭其他激活的赛季
        self.session.query(Season).filter(Season.is_active == True).update(
            {"is_active": False}
        )

        # 激活指定赛季
        stmt = select(Season).where(Season.season_id == season_id)
        season = self.session.execute(stmt).scalar_one_or_none()

        if not season:
            raise ValueError(f"Season not found: {season_id}")

        season.is_active = True
        self.session.commit()
        self.session.refresh(season)

        return self._season_to_dict(season)

    async def end_season(self, season_id: str) -> dict[str, Any]:
        """结束赛季

        创建最终快照并关闭赛季。

        Args:
            season_id: 赛季 ID

        Returns:
            结赛季信息
        """
        stmt = select(Season).where(Season.season_id == season_id)
        season = self.session.execute(stmt).scalar_one_or_none()

        if not season:
            raise ValueError(f"Season not found: {season_id}")

        # 创建最终快照
        await self._create_final_snapshots(season_id)

        # 关闭赛季
        season.is_active = False
        self.session.commit()
        self.session.refresh(season)

        return self._season_to_dict(season)

    async def distribute_season_rewards(self, season_id: str) -> dict[str, Any]:
        """发放赛季奖励

        根据最终排名发放奖励。

        Args:
            season_id: 赛季 ID

        Returns:
            奖励发放结果
        """
        stmt = select(Season).where(Season.season_id == season_id)
        season = self.session.execute(stmt).scalar_one_or_none()

        if not season:
            raise ValueError(f"Season not found: {season_id}")

        reward_tiers = {}
        if season.reward_tiers:
            try:
                reward_tiers = json.loads(season.reward_tiers)
            except json.JSONDecodeError:
                pass

        # 获取该赛季的所有排行榜
        lb_stmt = select(Leaderboard).where(Leaderboard.season_id == season_id)
        leaderboards = self.session.execute(lb_stmt).scalars().all()

        distributed_rewards = []

        for leaderboard in leaderboards:
            if leaderboard.rankings_json:
                rankings = json.loads(leaderboard.rankings_json)

                for entry in rankings:
                    rank = entry.get("rank", 0)
                    entity_id = entry.get("entity_id")

                    # 确定奖励层级
                    reward = self._get_reward_for_rank(rank, reward_tiers)
                    if reward and entity_id:
                        # 发放奖励 (简化处理，实际需要调用奖励系统)
                        result = await self._grant_reward(
                            entity_id, leaderboard.leaderboard_type, reward
                        )
                        distributed_rewards.append(result)

        return {
            "season_id": season_id,
            "total_rewards": len(distributed_rewards),
            "distributed_rewards": distributed_rewards,
        }

    async def _create_final_snapshots(self, season_id: str) -> list[dict[str, Any]]:
        """创建赛季结束时的最终快照

        Args:
            season_id: 赛季 ID

        Returns:
            创建的快照列表
        """
        stmt = select(Leaderboard).where(Leaderboard.season_id == season_id)
        leaderboards = self.session.execute(stmt).scalars().all()

        snapshots = []
        now = datetime.utcnow()

        for leaderboard in leaderboards:
            snapshot = LeaderboardSnapshot(
                snapshot_id=str(uuid4()),
                leaderboard_id=leaderboard.leaderboard_id,
                season_id=season_id,
                snapshot_time=now,
                rankings_json=leaderboard.rankings_json,
            )

            self.session.add(snapshot)
            snapshots.append(
                {
                    "snapshot_id": snapshot.snapshot_id,
                    "leaderboard_type": leaderboard.leaderboard_type,
                }
            )

        self.session.commit()

        return snapshots

    def _get_reward_for_rank(
        self, rank: int, reward_tiers: dict[str, Any]
    ) -> dict[str, Any] | None:
        """根据排名获取奖励

        Args:
            rank: 排名
            reward_tiers: 奖励层级配置

        Returns:
            奖励配置
        """
        for tier_name, tier_config in reward_tiers.items():
            if "range" in tier_config:
                rank_range = tier_config["range"]
                if isinstance(rank_range, str):
                    # 解析 "1-10" 格式
                    if "-" in rank_range:
                        start, end = map(int, rank_range.split("-"))
                        if start <= rank <= end:
                            return tier_config.get("rewards", {})
                    else:
                        # 单个排名 "1"
                        if rank == int(rank_range):
                            return tier_config.get("rewards", {})
            elif "min_rank" in tier_config and "max_rank" in tier_config:
                if tier_config["min_rank"] <= rank <= tier_config["max_rank"]:
                    return tier_config.get("rewards", {})

        return None

    async def _grant_reward(
        self, entity_id: str, leaderboard_type: str, reward: dict[str, Any]
    ) -> dict[str, Any]:
        """发放奖励给实体

        Args:
            entity_id: 实体 ID (玩家 ID 或公会 ID)
            leaderboard_type: 排行榜类型
            reward: 奖励配置

        Returns:
            发放结果
        """
        # 简化处理，实际需要根据排行榜类型和奖励类型进行发放
        if leaderboard_type == LeaderboardType.INDIVIDUAL.value:
            # 发放给玩家
            stmt = select(Player).where(Player.player_id == entity_id)
            player = self.session.execute(stmt).scalar_one_or_none()
            if player:
                # 发放奖励
                if "gold" in reward:
                    player.gold += reward["gold"]
                if "exp" in reward:
                    player.experience += reward["exp"]
                if "diamonds" in reward:
                    player.diamonds += reward["diamonds"]
                self.session.commit()

        return {
            "entity_id": entity_id,
            "leaderboard_type": leaderboard_type,
            "reward": reward,
            "granted_at": datetime.utcnow().isoformat(),
        }

    async def calculate_season_rankings(self, season_id: str) -> dict[str, Any]:
        """计算赛季最终排名

        Args:
            season_id: 赛季 ID

        Returns:
            排名计算结果
        """
        # 获取赛季信息
        stmt = select(Season).where(Season.season_id == season_id)
        season = self.session.execute(stmt).scalar_one_or_none()

        if not season:
            raise ValueError(f"Season not found: {season_id}")

        results = {}

        # 计算各种类型的排行榜
        for lb_type in [
            LeaderboardType.INDIVIDUAL.value,
            LeaderboardType.GUILD.value,
            LeaderboardType.ACHIEVEMENT.value,
        ]:
            rankings = await self._calculate_rankings_by_type(season_id, lb_type)
            results[lb_type] = rankings

        return {
            "season_id": season_id,
            "rankings": results,
        }

    async def _calculate_rankings_by_type(
        self, season_id: str, leaderboard_type: str
    ) -> list[dict[str, Any]]:
        """计算特定类型的排名

        Args:
            season_id: 赛季 ID
            leaderboard_type: 排行榜类型

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
        # 获取所有有成就进度的玩家
        stmt = (
            select(AchievementProgress, Player)
            .join(Player, AchievementProgress.player_id == Player.player_id)
            .where(AchievementProgress.is_completed == True)
        )
        results = self.session.execute(stmt).all()

        # 按玩家聚合成就分数
        player_scores: dict[str, dict[str, Any]] = {}

        for progress, player in results:
            if player.player_id not in player_scores:
                player_scores[player.player_id] = {
                    "entity_id": player.player_id,
                    "entity_name": player.username,
                    "common": 0,
                    "rare": 0,
                    "epic": 0,
                    "legendary": 0,
                    "total": 0,
                }

            # 这里简化处理，实际需要从 AchievementDefinition 获取稀有度
            player_scores[player.player_id]["total"] += 1

        # 计算分数
        rankings = []
        for player_id, data in player_scores.items():
            score = (
                data["common"] * 1
                + data["rare"] * 5
                + data["epic"] * 20
                + data["legendary"] * 100
            )
            data["score"] = score
            rankings.append(data)

        # 按分数排序
        rankings.sort(key=lambda x: x["score"], reverse=True)

        # 添加排名
        for i, entry in enumerate(rankings):
            entry["rank"] = i + 1

        return rankings

    def _season_to_dict(self, season: Season | None) -> dict[str, Any] | None:
        """将赛季对象转换为字典

        Args:
            season: 赛季对象

        Returns:
            赛季字典
        """
        if not season:
            return None

        reward_tiers = None
        if season.reward_tiers:
            try:
                reward_tiers = json.loads(season.reward_tiers)
            except json.JSONDecodeError:
                pass

        return {
            "season_id": season.season_id,
            "season_name": season.season_name,
            "season_number": season.season_number,
            "season_type": season.season_type,
            "start_time": season.start_time.isoformat(),
            "end_time": season.end_time.isoformat(),
            "reward_tiers": reward_tiers,
            "is_active": season.is_active,
            "created_at": season.created_at.isoformat() if season.created_at else None,
        }

    async def get_season_status(self, season_id: str) -> dict[str, Any]:
        """获取赛季状态

        Args:
            season_id: 赛季 ID

        Returns:
            赛季状态信息
        """
        stmt = select(Season).where(Season.season_id == season_id)
        season = self.session.execute(stmt).scalar_one_or_none()

        if not season:
            raise ValueError(f"Season not found: {season_id}")

        now = datetime.utcnow()

        # 计算剩余时间
        if season.end_time > now:
            remaining = season.end_time - now
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            remaining_str = f"{days}天 {hours}小时 {minutes}分钟"
        else:
            remaining_str = "已结束"

        # 获取排行榜数量
        lb_count = (
            self.session.query(Leaderboard)
            .filter(Leaderboard.season_id == season_id)
            .count()
        )

        return {
            "season_id": season.season_id,
            "season_name": season.season_name,
            "season_number": season.season_number,
            "is_active": season.is_active,
            "status": self._get_season_status(season, now),
            "start_time": season.start_time.isoformat(),
            "end_time": season.end_time.isoformat(),
            "remaining_time": remaining_str,
            "leaderboard_count": lb_count,
        }

    def _get_season_status(self, season: Season, now: datetime) -> str:
        """获取赛季状态字符串

        Args:
            season: 赛季对象
            now: 当前时间

        Returns:
            状态字符串
        """
        # 先检查时间状态
        if now < season.start_time:
            return "upcoming"
        elif now > season.end_time:
            return "ended"
        # 时间在范围内，检查是否激活
        elif season.is_active:
            return "active"
        else:
            return "inactive"
