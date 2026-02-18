"""PVP 管理器

实现 PVP 竞技场系统的核心逻辑，包括：
- ELO 积分算法
- 匹配系统
- 对战管理
- 观战功能
- 排行榜查询
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage.models import (
    PVPMatch,
    PVPMatchStatus,
    PVPMatchType,
    PVPRanking,
    PVPSpectator,
    Season,
    generate_uuid,
)


@dataclass
class MatchInfo:
    """对战信息数据类"""

    match_id: str
    match_type: str
    player_a_id: str
    player_b_id: str
    player_a_rating: int
    player_b_rating: int
    status: str
    created_at: str
    started_at: str | None
    finished_at: str | None
    score_a: int = 0
    score_b: int = 0
    winner_id: str | None = None
    spectator_count: int = 0
    allow_spectate: bool = True


@dataclass
class MatchmakingQueueItem:
    """匹配队列项"""

    player_id: str
    rating: int
    queued_at: datetime
    match_type: str = PVPMatchType.ARENA.value
    rating_range: int = 200


@dataclass
class RankingInfo:
    """排名信息数据类"""

    player_id: str
    rating: int
    max_rating: int
    matches_played: int
    matches_won: int
    matches_lost: int
    matches_drawn: int
    current_streak: int
    max_streak: int
    win_rate: float
    rank: int = 0


class ELOCalculator:
    """ELO 积分计算器

    实现标准的 ELO 积分算法，用于计算对战后的积分变化。
    """

    # ELO 算法参数
    BASE_K = 32  # 基础 K 因子
    K_FACTOR_NEWBIE = 40  # 新手 K 因子（对战场数 < 30）
    K_FACTOR_PRO = 24  # 高手 K 因子（积分 > 2400）

    @staticmethod
    def calculate_expected_score(rating_a: int, rating_b: int) -> tuple[float, float]:
        """计算预期胜率

        Args:
            rating_a: 玩家A的积分
            rating_b: 玩家B的积分

        Returns:
            (玩家A的预期胜率, 玩家B的预期胜率)
        """
        expected_a = 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))
        expected_b = 1.0 / (1.0 + 10.0 ** ((rating_a - rating_b) / 400.0))
        return expected_a, expected_b

    @classmethod
    def get_k_factor(cls, rating: int, matches_played: int) -> int:
        """获取 K 因子

        Args:
            rating: 当前积分
            matches_played: 对战场数

        Returns:
            K 因子值
        """
        if matches_played < 30:
            return cls.K_FACTOR_NEWBIE
        if rating >= 2400:
            return cls.K_FACTOR_PRO
        return cls.BASE_K

    @classmethod
    def calculate_new_rating(
        cls,
        rating: int,
        expected_score: float,
        actual_score: float,
        matches_played: int,
    ) -> int:
        """计算新积分

        Args:
            rating: 当前积分
            expected_score: 预期胜率
            actual_score: 实际得分 (1=胜, 0.5=平, 0=负)
            matches_played: 对战场数

        Returns:
            新积分
        """
        k = cls.get_k_factor(rating, matches_played)
        new_rating = rating + k * (actual_score - expected_score)
        return max(0, int(new_rating))  # 确保积分非负


class PVPManager:
    """PVP 管理器

    负责 PVP 竞技场的核心逻辑，包括匹配、对战、积分计算等。
    """

    def __init__(self, db: Session):
        self.db = db
        self.matchmaking_queue: list[MatchmakingQueueItem] = []
        self.elo_calculator = ELOCalculator()

    def _get_active_season(self) -> Season | None:
        """获取当前活跃赛季

        Returns:
            当前活跃的赛季，如果没有则返回 None
        """
        return self.db.execute(
            select(Season).where(Season.is_active == True)  # noqa: E712
        ).scalar_one_or_none()

    def _get_or_create_ranking(
        self, player_id: str, season_id: str
    ) -> PVPRanking:
        """获取或创建玩家排名记录

        Args:
            player_id: 玩家ID
            season_id: 赛季ID

        Returns:
            PVP排名记录
        """
        ranking = self.db.execute(
            select(PVPRanking).where(
                PVPRanking.player_id == player_id,
                PVPRanking.season_id == season_id,
            )
        ).scalar_one_or_none()

        if not ranking:
            ranking = PVPRanking(
                ranking_id=generate_uuid(),
                season_id=season_id,
                player_id=player_id,
                rating=1000,
                max_rating=1000,
                matches_played=0,
                matches_won=0,
                matches_lost=0,
                matches_drawn=0,
                current_streak=0,
                max_streak=0,
            )
            self.db.add(ranking)
            self.db.commit()
            self.db.refresh(ranking)

        return ranking

    def _get_player_rating(self, player_id: str, season_id: str | None = None) -> int:
        """获取玩家积分

        Args:
            player_id: 玩家ID
            season_id: 赛季ID，默认为当前活跃赛季

        Returns:
            玩家积分，默认为1000
        """
        if season_id is None:
            season = self._get_active_season()
            if season is None:
                return 1000
            season_id = season.season_id

        ranking = self.db.execute(
            select(PVPRanking).where(
                PVPRanking.player_id == player_id,
                PVPRanking.season_id == season_id,
            )
        ).scalar_one_or_none()

        return ranking.rating if ranking else 1000

    def add_to_matchmaking(
        self,
        player_id: str,
        match_type: str = PVPMatchType.ARENA.value,
        rating_range: int = 200,
    ) -> dict:
        """加入匹配队列

        Args:
            player_id: 玩家ID
            match_type: 对战类型
            rating_range: 积分范围

        Returns:
            匹配结果或队列状态
        """
        # 获取当前活跃赛季
        season = self._get_active_season()
        if season is None:
            raise ValueError("当前没有活跃赛季")

        # 检查是否已在队列中
        for item in self.matchmaking_queue:
            if item.player_id == player_id:
                return {
                    "status": "already_queued",
                    "player_id": player_id,
                    "queue_position": self.matchmaking_queue.index(item) + 1,
                }

        # 获取玩家积分
        player_rating = self._get_player_rating(player_id, season.season_id)

        # 尝试寻找匹配
        matched = self._find_match_in_queue(
            player_id, player_rating, match_type, rating_range, season.season_id
        )

        if matched:
            from dataclasses import asdict
            return {
                "status": "matched",
                "match": asdict(matched),
            }

        # 加入队列
        queue_item = MatchmakingQueueItem(
            player_id=player_id,
            rating=player_rating,
            queued_at=datetime.utcnow(),
            match_type=match_type,
            rating_range=rating_range,
        )
        self.matchmaking_queue.append(queue_item)

        return {
            "status": "queued",
            "player_id": player_id,
            "rating": player_rating,
            "queue_position": len(self.matchmaking_queue),
            "estimated_wait_time": len(self.matchmaking_queue) * 5,  # 预估秒数
        }

    def _find_match_in_queue(
        self,
        player_id: str,
        player_rating: int,
        match_type: str,
        rating_range: int,
        season_id: str,
    ) -> MatchInfo | None:
        """在队列中寻找匹配对手

        Args:
            player_id: 玩家ID
            player_rating: 玩家积分
            match_type: 对战类型
            rating_range: 积分范围
            season_id: 赛季ID

        Returns:
            匹配的对战信息，未找到返回 None
        """
        for i, item in enumerate(self.matchmaking_queue):
            # 跳过自己
            if item.player_id == player_id:
                continue

            # 检查类型是否匹配
            if item.match_type != match_type:
                continue

            # 检查积分范围
            if abs(item.rating - player_rating) > rating_range:
                continue

            # 找到匹配，创建对战
            opponent_rating = item.rating
            match = self._create_match(
                player_id,
                item.player_id,
                player_rating,
                opponent_rating,
                match_type,
                season_id,
            )

            # 从队列中移除对手
            self.matchmaking_queue.pop(i)

            return match

        return None

    def _create_match(
        self,
        player_a_id: str,
        player_b_id: str,
        rating_a: int,
        rating_b: int,
        match_type: str,
        season_id: str,
    ) -> MatchInfo:
        """创建对战

        Args:
            player_a_id: 玩家A ID
            player_b_id: 玩家B ID
            rating_a: 玩家A积分
            rating_b: 玩家B积分
            match_type: 对战类型
            season_id: 赛季ID

        Returns:
            创建的对战信息
        """
        match = PVPMatch(
            match_id=generate_uuid(),
            match_type=match_type,
            player_a_id=player_a_id,
            player_b_id=player_b_id,
            status=PVPMatchStatus.WAITING.value,
            score_a=0,
            score_b=0,
            duration_seconds=0,
            moves_a=0,
            moves_b=0,
            spectator_count=0,
            allow_spectate=True,
            created_at=datetime.utcnow(),
        )

        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)

        return MatchInfo(
            match_id=match.match_id,
            match_type=match.match_type,
            player_a_id=match.player_a_id,
            player_b_id=match.player_b_id,
            player_a_rating=rating_a,
            player_b_rating=rating_b,
            status=match.status,
            created_at=match.created_at.isoformat(),
            started_at=match.started_at.isoformat() if match.started_at else None,
            finished_at=match.finished_at.isoformat() if match.finished_at else None,
            score_a=match.score_a,
            score_b=match.score_b,
            winner_id=match.winner_id,
            spectator_count=match.spectator_count,
            allow_spectate=match.allow_spectate,
        )

    def cancel_matchmaking(self, player_id: str) -> dict:
        """取消匹配

        Args:
            player_id: 玩家ID

        Returns:
            取消结果
        """
        for i, item in enumerate(self.matchmaking_queue):
            if item.player_id == player_id:
                self.matchmaking_queue.pop(i)
                return {
                    "status": "cancelled",
                    "player_id": player_id,
                }

        return {
            "status": "not_queued",
            "player_id": player_id,
        }

    def get_match_info(self, match_id: str) -> dict:
        """获取对战信息

        Args:
            match_id: 对战ID

        Returns:
            对战信息详情

        Raises:
            ValueError: 对战不存在
        """
        match = self.db.execute(
            select(PVPMatch).where(PVPMatch.match_id == match_id)
        ).scalar_one_or_none()

        if not match:
            raise ValueError(f"对战不存在: {match_id}")

        # 获取双方玩家积分
        season = self._get_active_season()
        rating_a = (
            self._get_player_rating(match.player_a_id, season.season_id)
            if season
            else 1000
        )
        rating_b = (
            self._get_player_rating(match.player_b_id, season.season_id)
            if season
            else 1000
        )

        return {
            "match_id": match.match_id,
            "match_type": match.match_type,
            "player_a_id": match.player_a_id,
            "player_b_id": match.player_b_id,
            "player_a_rating": rating_a,
            "player_b_rating": rating_b,
            "status": match.status,
            "score_a": match.score_a,
            "score_b": match.score_b,
            "winner_id": match.winner_id,
            "duration_seconds": match.duration_seconds,
            "moves_a": match.moves_a,
            "moves_b": match.moves_b,
            "spectator_count": match.spectator_count,
            "allow_spectate": match.allow_spectate,
            "created_at": match.created_at.isoformat(),
            "started_at": match.started_at.isoformat() if match.started_at else None,
            "finished_at": match.finished_at.isoformat() if match.finished_at else None,
        }

    def start_match(self, match_id: str) -> dict:
        """开始对战

        Args:
            match_id: 对战ID

        Returns:
            更新后的对战信息

        Raises:
            ValueError: 对战不存在或状态不正确
        """
        match = self.db.execute(
            select(PVPMatch).where(PVPMatch.match_id == match_id)
        ).scalar_one_or_none()

        if not match:
            raise ValueError(f"对战不存在: {match_id}")

        if match.status != PVPMatchStatus.WAITING.value:
            raise ValueError(f"对战状态不正确: {match.status}")

        match.status = PVPMatchStatus.ACTIVE.value
        match.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(match)

        return {
            "match_id": match.match_id,
            "status": match.status,
            "started_at": match.started_at.isoformat(),
        }

    def submit_result(
        self,
        match_id: str,
        winner_id: str | None,
        score_a: int,
        score_b: int,
        moves_a: int = 0,
        moves_b: int = 0,
    ) -> dict:
        """提交对战结果

        Args:
            match_id: 对战ID
            winner_id: 获胜玩家ID (None表示平局)
            score_a: 玩家A得分
            score_b: 玩家B得分
            moves_a: 玩家A行动次数
            moves_b: 玩家B行动次数

        Returns:
            更新后的对战信息和积分变化

        Raises:
            ValueError: 对战不存在或状态不正确
        """
        match = self.db.execute(
            select(PVPMatch).where(PVPMatch.match_id == match_id)
        ).scalar_one_or_none()

        if not match:
            raise ValueError(f"对战不存在: {match_id}")

        if match.status != PVPMatchStatus.ACTIVE.value:
            raise ValueError(f"对战状态不正确: {match.status}")

        # 获取当前赛季
        season = self._get_active_season()
        if season is None:
            raise ValueError("当前没有活跃赛季")

        # 验证获胜者
        if winner_id is not None and winner_id not in (
            match.player_a_id,
            match.player_b_id,
        ):
            raise ValueError(f"获胜者ID不在对战中: {winner_id}")

        # 获取双方排名记录
        ranking_a = self._get_or_create_ranking(match.player_a_id, season.season_id)
        ranking_b = self._get_or_create_ranking(match.player_b_id, season.season_id)

        # 更新对战数据
        match.score_a = score_a
        match.score_b = score_b
        match.moves_a = moves_a
        match.moves_b = moves_b
        match.winner_id = winner_id
        match.status = PVPMatchStatus.FINISHED.value
        match.finished_at = datetime.utcnow()

        if match.started_at:
            match.duration_seconds = int(
                (match.finished_at - match.started_at).total_seconds()
            )

        # 计算 ELO 积分变化
        rating_changes = self._update_ratings(
            match, ranking_a, ranking_b, winner_id, season.season_id
        )

        self.db.commit()
        self.db.refresh(match)

        return {
            "match_id": match.match_id,
            "status": match.status,
            "winner_id": match.winner_id,
            "score_a": match.score_a,
            "score_b": match.score_b,
            "duration_seconds": match.duration_seconds,
            "rating_changes": rating_changes,
        }

    def _update_ratings(
        self,
        match: PVPMatch,
        ranking_a: PVPRanking,
        ranking_b: PVPRanking,
        winner_id: str | None,
        season_id: str,
    ) -> dict:
        """更新双方积分

        Args:
            match: 对战记录
            ranking_a: 玩家A排名记录
            ranking_b: 玩家B排名记录
            winner_id: 获胜者ID
            season_id: 赛季ID

        Returns:
            积分变化信息
        """
        # 获取当前积分
        rating_a = ranking_a.rating
        rating_b = ranking_b.rating

        # 计算预期胜率
        expected_a, expected_b = self.elo_calculator.calculate_expected_score(
            rating_a, rating_b
        )

        # 确定实际得分
        if winner_id == match.player_a_id:
            actual_a, actual_b = 1.0, 0.0
        elif winner_id == match.player_b_id:
            actual_a, actual_b = 0.0, 1.0
        else:  # 平局
            actual_a, actual_b = 0.5, 0.5

        # 计算新积分
        new_rating_a = self.elo_calculator.calculate_new_rating(
            rating_a, expected_a, actual_a, ranking_a.matches_played
        )
        new_rating_b = self.elo_calculator.calculate_new_rating(
            rating_b, expected_b, actual_b, ranking_b.matches_played
        )

        # 更新排名记录
        ranking_a.rating = new_rating_a
        ranking_a.max_rating = max(ranking_a.max_rating, new_rating_a)
        ranking_a.matches_played += 1

        ranking_b.rating = new_rating_b
        ranking_b.max_rating = max(ranking_b.max_rating, new_rating_b)
        ranking_b.matches_played += 1

        # 更新胜负统计
        if winner_id == match.player_a_id:
            ranking_a.matches_won += 1
            ranking_b.matches_lost += 1
            # 更新连胜
            ranking_a.current_streak = ranking_a.current_streak + 1 if ranking_a.current_streak > 0 else 1
            ranking_a.max_streak = max(ranking_a.max_streak, ranking_a.current_streak)
            ranking_b.current_streak = ranking_b.current_streak - 1 if ranking_b.current_streak < 0 else -1
        elif winner_id == match.player_b_id:
            ranking_b.matches_won += 1
            ranking_a.matches_lost += 1
            # 更新连胜
            ranking_b.current_streak = ranking_b.current_streak + 1 if ranking_b.current_streak > 0 else 1
            ranking_b.max_streak = max(ranking_b.max_streak, ranking_b.current_streak)
            ranking_a.current_streak = ranking_a.current_streak - 1 if ranking_a.current_streak < 0 else -1
        else:  # 平局
            ranking_a.matches_drawn += 1
            ranking_b.matches_drawn += 1
            ranking_a.current_streak = 0
            ranking_b.current_streak = 0

        return {
            "player_a": {
                "player_id": match.player_a_id,
                "old_rating": rating_a,
                "new_rating": new_rating_a,
                "change": new_rating_a - rating_a,
            },
            "player_b": {
                "player_id": match.player_b_id,
                "old_rating": rating_b,
                "new_rating": new_rating_b,
                "change": new_rating_b - rating_b,
            },
        }

    def get_player_ranking(self, player_id: str, season_id: str | None = None) -> dict:
        """获取玩家排名信息

        Args:
            player_id: 玩家ID
            season_id: 赛季ID，默认为当前活跃赛季

        Returns:
            玩家排名信息

        Raises:
            ValueError: 玩家排名不存在
        """
        if season_id is None:
            season = self._get_active_season()
            if season is None:
                raise ValueError("当前没有活跃赛季")
            season_id = season.season_id

        ranking = self.db.execute(
            select(PVPRanking).where(
                PVPRanking.player_id == player_id,
                PVPRanking.season_id == season_id,
            )
        ).scalar_one_or_none()

        if not ranking:
            raise ValueError(f"玩家排名不存在: {player_id}")

        # 计算排名
        rank = self._calculate_rank(ranking.rating, season_id)

        win_rate = (
            ranking.matches_won / ranking.matches_played * 100
            if ranking.matches_played > 0
            else 0
        )

        return {
            "player_id": player_id,
            "season_id": season_id,
            "rating": ranking.rating,
            "max_rating": ranking.max_rating,
            "rank": rank,
            "matches_played": ranking.matches_played,
            "matches_won": ranking.matches_won,
            "matches_lost": ranking.matches_lost,
            "matches_drawn": ranking.matches_drawn,
            "current_streak": ranking.current_streak,
            "max_streak": ranking.max_streak,
            "win_rate": round(win_rate, 2),
        }

    def _calculate_rank(self, rating: int, season_id: str) -> int:
        """计算排名

        Args:
            rating: 玩家积分
            season_id: 赛季ID

        Returns:
            排名
        """
        # 统计积分高于该玩家的人数
        from sqlalchemy import func
        count = self.db.execute(
            select(func.count()).select_from(PVPRanking).where(
                PVPRanking.season_id == season_id,
                PVPRanking.rating > rating,
            )
        ).scalar() or 0
        return count + 1

    def get_ranking_list(
        self,
        season_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """获取积分排行榜

        Args:
            season_id: 赛季ID，默认为当前活跃赛季
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            排行榜列表
        """
        if season_id is None:
            season = self._get_active_season()
            if season is None:
                return []
            season_id = season.season_id

        # 查询排行榜
        rankings = (
            self.db.execute(
                select(PVPRanking)
                .where(PVPRanking.season_id == season_id)
                .order_by(PVPRanking.rating.desc())
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )

        result = []
        for i, ranking in enumerate(rankings):
            win_rate = (
                ranking.matches_won / ranking.matches_played * 100
                if ranking.matches_played > 0
                else 0
            )
            result.append({
                "rank": offset + i + 1,
                "player_id": ranking.player_id,
                "season_id": season_id,
                "rating": ranking.rating,
                "max_rating": ranking.max_rating,
                "matches_played": ranking.matches_played,
                "matches_won": ranking.matches_won,
                "matches_lost": ranking.matches_lost,
                "matches_drawn": ranking.matches_drawn,
                "current_streak": ranking.current_streak,
                "max_streak": ranking.max_streak,
                "win_rate": round(win_rate, 2),
            })

        return result

    def join_spectate(self, match_id: str, player_id: str) -> dict:
        """加入观战

        Args:
            match_id: 对战ID
            player_id: 观战玩家ID

        Returns:
            观战结果

        Raises:
            ValueError: 对战不存在或不允许观战
        """
        match = self.db.execute(
            select(PVPMatch).where(PVPMatch.match_id == match_id)
        ).scalar_one_or_none()

        if not match:
            raise ValueError(f"对战不存在: {match_id}")

        if not match.allow_spectate:
            raise ValueError("该对战不允许观战")

        if match.status not in (
            PVPMatchStatus.WAITING.value,
            PVPMatchStatus.ACTIVE.value,
        ):
            raise ValueError(f"对战状态不允许观战: {match.status}")

        # 检查是否已在观战
        existing = self.db.execute(
            select(PVPSpectator).where(
                PVPSpectator.match_id == match_id,
                PVPSpectator.player_id == player_id,
                PVPSpectator.left_at.is_(None),
            )
        ).scalar_one_or_none()

        if existing:
            return {
                "status": "already_spectating",
                "match_id": match_id,
                "spectator_id": existing.spectator_id,
            }

        # 创建观战记录
        spectator = PVPSpectator(
            spectator_id=generate_uuid(),
            match_id=match_id,
            player_id=player_id,
            joined_at=datetime.utcnow(),
        )
        self.db.add(spectator)

        # 更新观战人数
        match.spectator_count += 1

        self.db.commit()
        self.db.refresh(spectator)

        return {
            "status": "joined",
            "match_id": match_id,
            "spectator_id": spectator.spectator_id,
            "spectator_count": match.spectator_count,
        }

    def leave_spectate(self, spectator_id: str) -> dict:
        """离开观战

        Args:
            spectator_id: 观战记录ID

        Returns:
            离开结果
        """
        spectator = self.db.execute(
            select(PVPSpectator).where(PVPSpectator.spectator_id == spectator_id)
        ).scalar_one_or_none()

        if spectator and spectator.left_at is None:
            spectator.left_at = datetime.utcnow()

            # 更新对战观战人数
            match = self.db.execute(
                select(PVPMatch).where(PVPMatch.match_id == spectator.match_id)
            ).scalar_one_or_none()

            if match and match.spectator_count > 0:
                match.spectator_count -= 1

            self.db.commit()

        return {
            "status": "left",
            "spectator_id": spectator_id,
        }

    def get_spectators(self, match_id: str) -> list[dict]:
        """获取观战列表

        Args:
            match_id: 对战ID

        Returns:
            观战玩家列表
        """
        spectators = self.db.execute(
            select(PVPSpectator).where(
                PVPSpectator.match_id == match_id,
                PVPSpectator.left_at.is_(None),
            )
        ).scalars().all()

        return [
            {
                "spectator_id": s.spectator_id,
                "player_id": s.player_id,
                "joined_at": s.joined_at.isoformat(),
            }
            for s in spectators
        ]

    def get_active_matches(self, limit: int = 50) -> list[dict]:
        """获取活跃对战列表

        Args:
            limit: 返回数量限制

        Returns:
            活跃对战列表
        """
        matches = (
            self.db.execute(
                select(PVPMatch)
                .where(
                    PVPMatch.status.in_(
                        [PVPMatchStatus.WAITING.value, PVPMatchStatus.ACTIVE.value]
                    )
                )
                .order_by(PVPMatch.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        season = self._get_active_season()

        result = []
        for match in matches:
            rating_a = (
                self._get_player_rating(match.player_a_id, season.season_id)
                if season
                else 1000
            )
            rating_b = (
                self._get_player_rating(match.player_b_id, season.season_id)
                if season
                else 1000
            )

            result.append({
                "match_id": match.match_id,
                "match_type": match.match_type,
                "player_a_id": match.player_a_id,
                "player_b_id": match.player_b_id,
                "player_a_rating": rating_a,
                "player_b_rating": rating_b,
                "status": match.status,
                "score_a": match.score_a,
                "score_b": match.score_b,
                "spectator_count": match.spectator_count,
                "allow_spectate": match.allow_spectate,
                "created_at": match.created_at.isoformat(),
                "started_at": match.started_at.isoformat() if match.started_at else None,
            })

        return result

    def get_player_match_history(
        self, player_id: str, limit: int = 20
    ) -> list[dict]:
        """获取玩家对战历史

        Args:
            player_id: 玩家ID
            limit: 返回数量限制

        Returns:
            对战历史列表
        """
        matches = (
            self.db.execute(
                select(PVPMatch)
                .where(
                    PVPMatch.status == PVPMatchStatus.FINISHED.value,
                )
                .where(
                    (PVPMatch.player_a_id == player_id) | (PVPMatch.player_b_id == player_id)
                )
                .order_by(PVPMatch.finished_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        result = []
        for match in matches:
            is_player_a = match.player_a_id == player_id
            opponent_id = match.player_b_id if is_player_a else match.player_a_id
            player_score = match.score_a if is_player_a else match.score_b
            opponent_score = match.score_b if is_player_a else match.score_a

            result.append({
                "match_id": match.match_id,
                "match_type": match.match_type,
                "opponent_id": opponent_id,
                "player_score": player_score,
                "opponent_score": opponent_score,
                "is_winner": match.winner_id == player_id,
                "is_draw": match.winner_id is None,
                "finished_at": match.finished_at.isoformat() if match.finished_at else None,
            })

        return result
