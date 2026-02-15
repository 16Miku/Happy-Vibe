"""PVP API 端点单元测试"""

from datetime import datetime, timedelta
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.storage.database import get_db
from src.storage.models import (
    PVPMatch,
    PVPMatchStatus,
    PVPMatchType,
    PVPRanking,
    Season,
    generate_uuid,
)
from tests.test_quest_manager import test_player as make_test_player


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    db = get_db()
    db.create_tables()
    session = db.get_session_instance()

    yield session

    session.close()


@pytest.fixture
def test_client(db_session):
    """创建测试客户端"""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_player(db_session):
    """创建测试玩家"""
    return make_test_player(db_session)


@pytest.fixture
def test_player_2(db_session):
    """创建第二个测试玩家"""
    from src.storage.models import Player
    unique_name = f"test_api_pvp_player_2_{uuid.uuid4().hex[:8]}"
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


class TestPVPMatchmakingAPI:
    """PVP 匹配 API 测试"""

    def test_join_matchmaking(self, test_client, test_player, test_season):
        """测试加入匹配"""
        response = test_client.post(
            "/api/pvp/matchmaking",
            json={
                "player_id": test_player.player_id,
                "match_type": PVPMatchType.ARENA.value,
                "rating_range": 200,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["player_id"] == test_player.player_id
        assert data["rating"] == 1000

    def test_join_matchmaking_player_not_found(self, test_client):
        """测试加入匹配 - 玩家不存在"""
        response = test_client.post(
            "/api/pvp/matchmaking",
            json={"player_id": "non_existent_id", "match_type": "arena"},
        )

        assert response.status_code == 404

    def test_cancel_matchmaking(self, test_client, test_player):
        """测试取消匹配"""
        # 先加入匹配
        test_client.post(
            "/api/pvp/matchmaking",
            json={"player_id": test_player.player_id},
        )

        # 取消匹配
        response = test_client.delete("/api/pvp/matchmaking?player_id=" + test_player.player_id)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_get_matchmaking_queue(self, test_client, test_player):
        """测试获取匹配队列"""
        response = test_client.get("/api/pvp/matchmaking/queue")

        assert response.status_code == 200
        data = response.json()
        assert "queue_size" in data
        assert "players" in data


class TestPVPMatchAPI:
    """PVP 对战 API 测试"""

    def test_get_match_info(self, test_client, test_player, test_player_2, test_season, db_session):
        """测试获取对战信息"""
        # 创建对战
        match = PVPMatch(
            match_id=generate_uuid(),
            match_type=PVPMatchType.ARENA.value,
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
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
        db_session.add(match)
        db_session.commit()

        response = test_client.get(f"/api/pvp/match/{match.match_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == match.match_id
        assert data["player_a_id"] == test_player.player_id
        assert data["player_b_id"] == test_player_2.player_id

    def test_get_match_info_not_found(self, test_client):
        """测试获取不存在的对战"""
        response = test_client.get("/api/pvp/match/non_existent_id")
        assert response.status_code == 404

    def test_start_match(self, test_client, test_player, test_player_2, test_season, db_session):
        """测试开始对战"""
        match = PVPMatch(
            match_id=generate_uuid(),
            match_type=PVPMatchType.ARENA.value,
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
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
        db_session.add(match)
        db_session.commit()

        response = test_client.post(f"/api/pvp/match/{match.match_id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == PVPMatchStatus.ACTIVE.value
        assert data["started_at"] is not None

    def test_submit_result(self, test_client, test_player, test_player_2, test_season, db_session):
        """测试提交对战结果"""
        match = PVPMatch(
            match_id=generate_uuid(),
            match_type=PVPMatchType.ARENA.value,
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            status=PVPMatchStatus.ACTIVE.value,
            score_a=0,
            score_b=0,
            duration_seconds=0,
            moves_a=0,
            moves_b=0,
            spectator_count=0,
            allow_spectate=True,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
        )
        db_session.add(match)
        db_session.commit()

        response = test_client.post(
            f"/api/pvp/match/{match.match_id}/result",
            json={
                "match_id": match.match_id,
                "winner_id": test_player.player_id,
                "score_a": 3,
                "score_b": 1,
                "moves_a": 10,
                "moves_b": 8,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == PVPMatchStatus.FINISHED.value
        assert data["winner_id"] == test_player.player_id
        assert "rating_changes" in data


class TestPVPSpectateAPI:
    """PVP 观战 API 测试"""

    def test_join_spectate(self, test_client, test_player, test_player_2, test_season, db_session):
        """测试加入观战"""
        # 创建观战者
        from src.storage.models import Player

        spectator_name = f"api_spectator_{uuid.uuid4().hex[:8]}"
        spectator = Player(
            username=spectator_name,
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
        )
        db_session.add(spectator)
        db_session.commit()

        # 创建对战
        match = PVPMatch(
            match_id=generate_uuid(),
            match_type=PVPMatchType.ARENA.value,
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            status=PVPMatchStatus.ACTIVE.value,
            score_a=1,
            score_b=1,
            duration_seconds=60,
            moves_a=5,
            moves_b=5,
            spectator_count=0,
            allow_spectate=True,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
        )
        db_session.add(match)
        db_session.commit()

        response = test_client.post(
            f"/api/pvp/match/{match.match_id}/spectate",
            params={"player_id": spectator.player_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "joined"
        assert data["spectator_id"] is not None

    def test_leave_spectate(self, test_client, test_player, test_player_2, db_session):
        """测试离开观战"""
        # 创建观战者
        from src.storage.models import Player, PVPSpectator

        spectator_name = f"api_spectator_{uuid.uuid4().hex[:8]}"
        spectator = Player(
            username=spectator_name,
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
        )
        db_session.add(spectator)
        db_session.commit()

        # 创建对战和观战记录
        match = PVPMatch(
            match_id=generate_uuid(),
            match_type=PVPMatchType.ARENA.value,
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            status=PVPMatchStatus.ACTIVE.value,
            score_a=1,
            score_b=1,
            spectator_count=1,
            allow_spectate=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(match)
        db_session.commit()

        spectator_rec = PVPSpectator(
            spectator_id=generate_uuid(),
            match_id=match.match_id,
            player_id=spectator.player_id,
            joined_at=datetime.utcnow(),
        )
        db_session.add(spectator_rec)
        db_session.commit()

        response = test_client.delete(
            f"/api/pvp/match/{match.match_id}/spectate",
            params={"spectator_id": spectator_rec.spectator_id},
        )

        assert response.status_code == 200

    def test_get_spectators(self, test_client, test_player, test_player_2, db_session):
        """测试获取观战列表"""
        match = PVPMatch(
            match_id=generate_uuid(),
            match_type=PVPMatchType.ARENA.value,
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            status=PVPMatchStatus.ACTIVE.value,
            score_a=1,
            score_b=1,
            spectator_count=0,
            allow_spectate=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(match)
        db_session.commit()

        response = test_client.get(f"/api/pvp/match/{match.match_id}/spectators")

        assert response.status_code == 200
        data = response.json()
        assert "match_id" in data
        assert "spectators" in data
        assert "count" in data


class TestPVPRankingAPI:
    """PVP 排名 API 测试"""

    def test_get_ranking_list(self, test_client, test_player, test_season, db_session):
        """测试获取排行榜"""
        # 创建排名记录
        ranking = PVPRanking(
            ranking_id=generate_uuid(),
            season_id=test_season.season_id,
            player_id=test_player.player_id,
            rating=1500,
            max_rating=1500,
            matches_played=10,
            matches_won=7,
            matches_lost=3,
            matches_drawn=0,
            current_streak=2,
            max_streak=5,
        )
        db_session.add(ranking)
        db_session.commit()

        response = test_client.get(f"/api/pvp/ranking?season_id={test_season.season_id}")

        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data
        assert len(data["rankings"]) >= 1

    def test_get_player_ranking(self, test_client, test_player, test_season, db_session):
        """测试获取玩家排名"""
        ranking = PVPRanking(
            ranking_id=generate_uuid(),
            season_id=test_season.season_id,
            player_id=test_player.player_id,
            rating=1500,
            max_rating=1600,
            matches_played=20,
            matches_won=15,
            matches_lost=4,
            matches_drawn=1,
            current_streak=3,
            max_streak=8,
        )
        db_session.add(ranking)
        db_session.commit()

        response = test_client.get(f"/api/pvp/ranking/{test_player.player_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["player_id"] == test_player.player_id
        assert data["rating"] == 1500
        assert data["matches_played"] == 20

    def test_get_player_ranking_not_found(self, test_client):
        """测试获取不存在的玩家排名"""
        response = test_client.get("/api/pvp/ranking/non_existent_id")
        assert response.status_code == 404


class TestPVPMatchHistoryAPI:
    """PVP 对战历史 API 测试"""

    def test_get_player_match_history(self, test_client, test_player, test_player_2, db_session):
        """测试获取玩家对战历史"""
        # 创建已结束的对战
        match = PVPMatch(
            match_id=generate_uuid(),
            match_type=PVPMatchType.ARENA.value,
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            status=PVPMatchStatus.FINISHED.value,
            score_a=3,
            score_b=1,
            winner_id=test_player.player_id,
            duration_seconds=300,
            moves_a=15,
            moves_b=12,
            spectator_count=0,
            allow_spectate=True,
            created_at=datetime.utcnow() - timedelta(minutes=10),
            started_at=datetime.utcnow() - timedelta(minutes=5),
            finished_at=datetime.utcnow(),
        )
        db_session.add(match)
        db_session.commit()

        response = test_client.get(f"/api/pvp/history/{test_player.player_id}")

        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert len(data["matches"]) >= 1


class TestPVPActiveMatchesAPI:
    """PVP 活跃对战 API 测试"""

    def test_get_active_matches(self, test_client, test_player, test_player_2, db_session):
        """测试获取活跃对战列表"""
        # 创建活跃对战
        match = PVPMatch(
            match_id=generate_uuid(),
            match_type=PVPMatchType.ARENA.value,
            player_a_id=test_player.player_id,
            player_b_id=test_player_2.player_id,
            status=PVPMatchStatus.ACTIVE.value,
            score_a=2,
            score_b=1,
            duration_seconds=120,
            moves_a=8,
            moves_b=6,
            spectator_count=3,
            allow_spectate=True,
            created_at=datetime.utcnow() - timedelta(minutes=5),
            started_at=datetime.utcnow() - timedelta(minutes=2),
        )
        db_session.add(match)
        db_session.commit()

        response = test_client.get("/api/pvp/matches/active")

        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert len(data["matches"]) >= 1
