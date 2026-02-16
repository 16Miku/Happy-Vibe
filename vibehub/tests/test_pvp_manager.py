"""PVP 管理器单元测试"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from src.core.pvp_manager import ELOCalculator, PVPManager
from src.storage.database import get_db
from src.storage.models import (
    Player,
    PVPMatch,
    PVPMatchStatus,
    PVPMatchType,
    PVPRanking,
    PVPSpectator,
    Season,
    generate_uuid,
)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    db = get_db()
    db.create_tables()
    session = db.get_session_instance()

    yield session

    session.close()


@pytest.fixture
def test_player(db_session):
    """创建测试玩家"""
    unique_name = f"test_pvp_player_{uuid.uuid4().hex[:8]}"
    player = Player(
        username=unique_name,
        vibe_energy=100,
        max_vibe_energy=1000,
        gold=500,
        diamonds=10,
        experience=0,
    )
    db_session.add(player)
    db_session.commit()
    db_session.refresh(player)
    return player


@pytest.fixture
def test_player_2(db_session):
    """创建第二个测试玩家"""
    unique_name = f"test_pvp_player_2_{uuid.uuid4().hex[:8]}"
    from src.storage.models import Player
    player = Player(
        username=unique_name,
        vibe_energy=100,
        max_vibe_energy=1000,
        gold=500,
        diamonds=10,
        experience=0,
    )
    db_session.add(player)
    db_session.commit()
    db_session.refresh(player)
    return player


@pytest.fixture
def test_season(db_session):
    """创建测试赛季"""
    # 先清理现有的活跃赛季
    db_session.query(Season).filter(Season.is_active == True).update({"is_active": False})
    db_session.commit()

    season = Season(
        season_id=generate_uuid(),
        season_name="测试赛季",
        season_number=1,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(days=90),
        season_type="regular",
        is_active=True,
    )
    db_session.add(season)
    db_session.commit()
    db_session.refresh(season)
    return season


@pytest.fixture
def pvp_manager(db_session):
    """创建 PVP 管理器"""
    return PVPManager(db_session)


class TestELOCalculator:
    """ELO 积分计算器测试"""

    def test_calculate_expected_score_equal_rating(self):
        """测试相同积分的预期胜率"""
        expected_a, expected_b = ELOCalculator.calculate_expected_score(1000, 1000)
        assert abs(expected_a - 0.5) < 0.01
        assert abs(expected_b - 0.5) < 0.01

    def test_calculate_expected_score_different_rating(self):
        """测试不同积分的预期胜率"""
        expected_a, expected_b = ELOCalculator.calculate_expected_score(1200, 1000)
        assert expected_a > 0.5
        assert expected_b < 0.5
        assert abs(expected_a + expected_b - 1.0) < 0.01

    def test_get_k_factor_newbie(self):
        """测试新手 K 因子"""
        k = ELOCalculator.get_k_factor(rating=1000, matches_played=10)
        assert k == ELOCalculator.K_FACTOR_NEWBIE

    def test_get_k_factor_normal(self):
        """测试普通玩家 K 因子"""
        k = ELOCalculator.get_k_factor(rating=1500, matches_played=50)
        assert k == ELOCalculator.BASE_K

    def test_get_k_factor_pro(self):
        """测试高手 K 因子"""
        k = ELOCalculator.get_k_factor(rating=2500, matches_played=100)
        assert k == ELOCalculator.K_FACTOR_PRO

    def test_calculate_new_rating_win(self):
        """测试获胜后新积分计算"""
        new_rating = ELOCalculator.calculate_new_rating(
            rating=1000,
            expected_score=0.5,
            actual_score=1.0,
            matches_played=50,
        )
        assert new_rating > 1000

    def test_calculate_new_rating_loss(self):
        """测试失败后新积分计算"""
        new_rating = ELOCalculator.calculate_new_rating(
            rating=1000,
            expected_score=0.5,
            actual_score=0.0,
            matches_played=50,
        )
        assert new_rating < 1000

    def test_calculate_new_rating_draw(self):
        """测试平局后新积分计算"""
        new_rating = ELOCalculator.calculate_new_rating(
            rating=1000,
            expected_score=0.5,
            actual_score=0.5,
            matches_played=50,
        )
        assert new_rating == 1000

    def test_calculate_new_rating_no_negative(self):
        """测试积分不会变成负数"""
        new_rating = ELOCalculator.calculate_new_rating(
            rating=10,
            expected_score=0.9,
            actual_score=0.0,
            matches_played=50,
        )
        assert new_rating >= 0


class TestPVPManager:
    """PVP 管理器测试"""

    def test_get_active_season(self, pvp_manager, test_season):
        """测试获取活跃赛季"""
        season = pvp_manager._get_active_season()
        assert season is not None
        assert season.season_id == test_season.season_id

    def test_get_or_create_ranking_new(self, pvp_manager, test_player, test_season):
        """测试创建新排名记录"""
        ranking = pvp_manager._get_or_create_ranking(
            test_player.player_id, test_season.season_id
        )

        assert ranking.player_id == test_player.player_id
        assert ranking.season_id == test_season.season_id
        assert ranking.rating == 1000
        assert ranking.matches_played == 0

    def test_get_or_create_ranking_existing(
        self, pvp_manager, test_player, test_season
    ):
        """测试获取现有排名记录"""
        ranking1 = pvp_manager._get_or_create_ranking(
            test_player.player_id, test_season.season_id
        )
        ranking1.rating = 1200
        pvp_manager.db.commit()

        ranking2 = pvp_manager._get_or_create_ranking(
            test_player.player_id, test_season.season_id
        )

        assert ranking2.ranking_id == ranking1.ranking_id
        assert ranking2.rating == 1200

    def test_get_player_rating_default(self, pvp_manager, test_player, test_season):
        """测试获取默认积分"""
        rating = pvp_manager._get_player_rating(
            test_player.player_id, test_season.season_id
        )
        assert rating == 1000

    def test_add_to_matchmaking(self, pvp_manager, test_player, test_season):
        """测试加入匹配队列"""
        result = pvp_manager.add_to_matchmaking(
            player_id=test_player.player_id,
            match_type=PVPMatchType.ARENA.value,
            rating_range=200,
        )

        assert result["status"] == "queued"
        assert result["player_id"] == test_player.player_id
        assert result["rating"] == 1000
        assert len(pvp_manager.matchmaking_queue) == 1

    def test_add_to_matchmaking_auto_match(
        self, pvp_manager, test_player, test_player_2, test_season
    ):
        """测试自动匹配"""
        # 第一个玩家加入队列
        pvp_manager.add_to_matchmaking(
            player_id=test_player.player_id,
            match_type=PVPMatchType.ARENA.value,
            rating_range=200,
        )

        # 第二个玩家加入，应该自动匹配
        result = pvp_manager.add_to_matchmaking(
            player_id=test_player_2.player_id,
            match_type=PVPMatchType.ARENA.value,
            rating_range=200,
        )

        assert result["status"] == "matched"
        assert result["match"] is not None
        assert result["match"]["player_a_id"] == test_player.player_id
        assert result["match"]["player_b_id"] == test_player_2.player_id

        # 队列应该为空
        assert len(pvp_manager.matchmaking_queue) == 0

    def test_add_to_matchmaking_already_queued(
        self, pvp_manager, test_player, test_season
    ):
        """测试重复加入队列"""
        pvp_manager.add_to_matchmaking(player_id=test_player.player_id)
        result = pvp_manager.add_to_matchmaking(player_id=test_player.player_id)

        assert result["status"] == "already_queued"

    def test_cancel_matchmaking(self, pvp_manager, test_player, test_season):
        """测试取消匹配"""
        pvp_manager.add_to_matchmaking(player_id=test_player.player_id)
        result = pvp_manager.cancel_matchmaking(test_player.player_id)

        assert result["status"] == "cancelled"
        assert len(pvp_manager.matchmaking_queue) == 0

    def test_cancel_matchmaking_not_queued(self, pvp_manager, test_player):
        """测试取消未在队列中的匹配"""
        result = pvp_manager.cancel_matchmaking(test_player.player_id)
        assert result["status"] == "not_queued"

    def test_create_match(self, pvp_manager, test_player, test_player_2, test_season):
        """测试创建对战"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1100,
            match_type=PVPMatchType.DUEL.value,
            season_id=test_season.season_id,
        )

        assert match.match_id is not None
        assert match.player_a_id == test_player.player_id
        assert match.player_b_id == test_player_2.player_id
        assert match.status == PVPMatchStatus.WAITING.value

    def test_get_match_info(self, pvp_manager, test_player, test_player_2, test_season):
        """测试获取对战信息"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1100,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        info = pvp_manager.get_match_info(match.match_id)

        assert info["match_id"] == match.match_id
        assert info["player_a_id"] == test_player.player_id
        assert info["player_b_id"] == test_player_2.player_id
        assert info["player_a_rating"] == 1000
        assert info["player_b_rating"] == 1100

    def test_get_match_info_not_found(self, pvp_manager):
        """测试获取不存在的对战"""
        with pytest.raises(ValueError, match="对战不存在"):
            pvp_manager.get_match_info("non_existent_id")

    def test_start_match(self, pvp_manager, test_player, test_player_2, test_season):
        """测试开始对战"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1100,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        result = pvp_manager.start_match(match.match_id)

        assert result["status"] == PVPMatchStatus.ACTIVE.value
        assert result["started_at"] is not None

    def test_submit_result_player_a_wins(
        self, pvp_manager, test_player, test_player_2, test_season, db_session
    ):
        """测试提交对战结果 - 玩家A获胜"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1000,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        pvp_manager.start_match(match.match_id)

        result = pvp_manager.submit_result(
            match_id=match.match_id,
            winner_id=test_player.player_id,
            score_a=3,
            score_b=1,
        )

        assert result["status"] == PVPMatchStatus.FINISHED.value
        assert result["winner_id"] == test_player.player_id
        assert result["score_a"] == 3
        assert result["score_b"] == 1

        # 验证积分变化
        rating_changes = result["rating_changes"]
        assert rating_changes["player_a"]["change"] > 0  # 胜者积分增加
        assert rating_changes["player_b"]["change"] < 0  # 败者积分减少

    def test_submit_result_draw(
        self, pvp_manager, test_player, test_player_2, test_season
    ):
        """测试提交对战结果 - 平局"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1000,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        pvp_manager.start_match(match.match_id)

        result = pvp_manager.submit_result(
            match_id=match.match_id,
            winner_id=None,
            score_a=2,
            score_b=2,
        )

        assert result["winner_id"] is None

        # 验证积分变化（平局双方积分变化接近）
        rating_changes = result["rating_changes"]
        assert abs(rating_changes["player_a"]["change"]) < 5
        assert abs(rating_changes["player_b"]["change"]) < 5

    def test_submit_result_updates_rankings(
        self, pvp_manager, test_player, test_player_2, test_season, db_session
    ):
        """测试提交结果更新排名记录"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1000,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        pvp_manager.start_match(match.match_id)
        pvp_manager.submit_result(
            match_id=match.match_id,
            winner_id=test_player.player_id,
            score_a=3,
            score_b=0,
        )

        # 验证排名记录已更新
        from src.storage.models import PVPRanking

        ranking_a = db_session.query(PVPRanking).filter(
            PVPRanking.player_id == test_player.player_id,
            PVPRanking.season_id == test_season.season_id,
        ).first()

        ranking_b = db_session.query(PVPRanking).filter(
            PVPRanking.player_id == test_player_2.player_id,
            PVPRanking.season_id == test_season.season_id,
        ).first()

        assert ranking_a is not None
        assert ranking_b is not None
        assert ranking_a.matches_played == 1
        assert ranking_a.matches_won == 1
        assert ranking_a.matches_lost == 0
        assert ranking_b.matches_played == 1
        assert ranking_b.matches_won == 0
        assert ranking_b.matches_lost == 1
        assert ranking_a.current_streak == 1
        assert ranking_b.current_streak == -1

    def test_get_player_ranking(self, pvp_manager, test_player, test_season):
        """测试获取玩家排名"""
        ranking = pvp_manager._get_or_create_ranking(
            test_player.player_id, test_season.season_id
        )
        ranking.rating = 1500
        pvp_manager.db.commit()

        result = pvp_manager.get_player_ranking(
            test_player.player_id, test_season.season_id
        )

        assert result["player_id"] == test_player.player_id
        assert result["rating"] == 1500
        assert result["rank"] == 1

    def test_get_ranking_list(self, pvp_manager, test_player, test_player_2, test_season):
        """测试获取排行榜"""
        # 设置不同积分
        ranking_a = pvp_manager._get_or_create_ranking(
            test_player.player_id, test_season.season_id
        )
        ranking_a.rating = 1500

        ranking_b = pvp_manager._get_or_create_ranking(
            test_player_2.player_id, test_season.season_id
        )
        ranking_b.rating = 1200

        pvp_manager.db.commit()

        rankings = pvp_manager.get_ranking_list(season_id=test_season.season_id)

        assert len(rankings) == 2
        assert rankings[0]["player_id"] == test_player.player_id
        assert rankings[0]["rating"] == 1500
        assert rankings[0]["rank"] == 1
        assert rankings[1]["player_id"] == test_player_2.player_id
        assert rankings[1]["rating"] == 1200
        assert rankings[1]["rank"] == 2

    def test_join_spectate(self, pvp_manager, test_player, test_player_2, test_season):
        """测试加入观战"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1000,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        # 创建第三个玩家用于观战
        from src.storage.models import Player

        spectator_name = f"spectator_{uuid.uuid4().hex[:8]}"
        spectator = Player(
            username=spectator_name,
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
        )
        pvp_manager.db.add(spectator)
        pvp_manager.db.commit()

        result = pvp_manager.join_spectate(match.match_id, spectator.player_id)

        assert result["status"] == "joined"
        assert result["spectator_id"] is not None
        assert result["spectator_count"] == 1

    def test_join_spectate_not_allowed(self, pvp_manager, test_player, test_player_2, test_season):
        """测试加入不允许观战的对战"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1000,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        # 修改为不允许观战
        db_match = pvp_manager.db.execute(
            PVPMatch.__table__.select().where(PVPMatch.match_id == match.match_id)
        ).first()
        pvp_manager.db.execute(
            PVPMatch.__table__.update()
            .where(PVPMatch.match_id == match.match_id)
            .values(allow_spectate=False)
        )
        pvp_manager.db.commit()

        from src.storage.models import Player

        spectator_name = f"spectator_{uuid.uuid4().hex[:8]}"
        spectator = Player(
            username=spectator_name,
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
        )
        pvp_manager.db.add(spectator)
        pvp_manager.db.commit()

        with pytest.raises(ValueError, match="不允许观战"):
            pvp_manager.join_spectate(match.match_id, spectator.player_id)

    def test_leave_spectate(self, pvp_manager, test_player, test_player_2, test_season):
        """测试离开观战"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1000,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        from src.storage.models import Player

        spectator_name = f"spectator_{uuid.uuid4().hex[:8]}"
        spectator = Player(
            username=spectator_name,
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
        )
        pvp_manager.db.add(spectator)
        pvp_manager.db.commit()

        join_result = pvp_manager.join_spectate(match.match_id, spectator.player_id)
        spectator_id = join_result["spectator_id"]

        result = pvp_manager.leave_spectate(spectator_id)

        assert result["status"] == "left"

    def test_get_spectators(self, pvp_manager, test_player, test_player_2, test_season):
        """测试获取观战列表"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1000,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        from src.storage.models import Player

        # 添加两个观战者
        for i in range(2):
            spectator_name = f"spectator_{uuid.uuid4().hex[:8]}"
            spectator = Player(
                username=spectator_name,
                vibe_energy=100,
                max_vibe_energy=1000,
                gold=500,
            )
            pvp_manager.db.add(spectator)
            pvp_manager.db.commit()
            pvp_manager.join_spectate(match.match_id, spectator.player_id)

        spectators = pvp_manager.get_spectators(match.match_id)

        assert len(spectators) == 2

    def test_get_active_matches(self, pvp_manager, test_player, test_player_2, test_season):
        """测试获取活跃对战"""
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1100,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        matches = pvp_manager.get_active_matches()

        assert len(matches) >= 1
        match_ids = [m["match_id"] for m in matches]
        assert match.match_id in match_ids

    def test_get_player_match_history(
        self, pvp_manager, test_player, test_player_2, test_season
    ):
        """测试获取玩家对战历史"""
        # 创建一场已结束的对战
        match = pvp_manager._create_match(
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            rating_a=1000,
            rating_b=1100,
            match_type=PVPMatchType.ARENA.value,
            season_id=test_season.season_id,
        )

        # 标记为已结束
        pvp_manager.db.execute(
            PVPMatch.__table__.update()
            .where(PVPMatch.match_id == match.match_id)
            .values(
                status=PVPMatchStatus.FINISHED.value,
                finished_at=datetime.utcnow(),
            )
        )
        pvp_manager.db.commit()

        history = pvp_manager.get_player_match_history(test_player.player_id)

        assert len(history) >= 1
        assert history[0]["match_id"] == match.match_id
        assert history[0]["opponent_id"] == test_player_2.player_id
