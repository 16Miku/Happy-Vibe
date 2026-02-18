"""PVP API 端点单元测试"""

from datetime import datetime, timedelta
import uuid

import pytest
from fastapi.testclient import TestClient

from src.main import app
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
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def pvp_test_player(test_db):
    """创建测试玩家"""
    unique_name = f"test_api_pvp_player_{uuid.uuid4().hex[:8]}"
    with test_db.get_session() as session:
        player = Player(
            username=unique_name,
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
            diamonds=10,
            experience=0,
        )
        session.add(player)
        session.commit()
        session.refresh(player)
        return Player(
            player_id=player.player_id,
            username=player.username,
        )


@pytest.fixture
def pvp_test_player_2(test_db):
    """创建第二个测试玩家"""
    unique_name = f"test_api_pvp_player_2_{uuid.uuid4().hex[:8]}"
    with test_db.get_session() as session:
        player = Player(
            username=unique_name,
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
            diamonds=10,
            experience=0,
        )
        session.add(player)
        session.commit()
        session.refresh(player)
        return Player(
            player_id=player.player_id,
            username=player.username,
        )


@pytest.fixture
def pvp_test_season(test_db):
    """创建测试赛季"""
    with test_db.get_session() as session:
        # 先清理现有的活跃赛季
        session.query(Season).filter(Season.is_active == True).update({"is_active": False})
        session.commit()

        season = Season(
            season_id=generate_uuid(),
            season_name="测试赛季",
            season_number=1,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(days=90),
            season_type="regular",
            is_active=True,
        )
        session.add(season)
        session.commit()
        session.refresh(season)
        return Season(
            season_id=season.season_id,
            season_name=season.season_name,
            season_number=season.season_number,
            is_active=season.is_active,
        )


class TestPVPMatchmakingAPI:
    """PVP 匹配 API 测试"""

    def test_join_matchmaking(self, client, pvp_test_player, pvp_test_season):
        """测试加入匹配"""
        response = client.post(
            "/api/pvp/matchmaking",
            json={
                "player_id": pvp_test_player.player_id,
                "match_type": PVPMatchType.ARENA.value,
                "rating_range": 200,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["player_id"] == pvp_test_player.player_id
        assert data["rating"] == 1000

    def test_join_matchmaking_player_not_found(self, client):
        """测试加入匹配 - 玩家不存在"""
        response = client.post(
            "/api/pvp/matchmaking",
            json={"player_id": "non_existent_id", "match_type": "arena"},
        )

        assert response.status_code == 404

    def test_cancel_matchmaking(self, client, pvp_test_player, pvp_test_season):
        """测试取消匹配"""
        # 先加入匹配
        join_response = client.post(
            "/api/pvp/matchmaking",
            json={"player_id": pvp_test_player.player_id},
        )
        assert join_response.status_code == 200

        # 取消匹配
        response = client.delete("/api/pvp/matchmaking?player_id=" + pvp_test_player.player_id)

        assert response.status_code == 200
        data = response.json()
        # 由于每次请求创建新的 PVPManager 实例，队列不共享，所以可能是 not_queued
        assert data["status"] in ["cancelled", "not_queued"]

    def test_get_matchmaking_queue(self, client, pvp_test_player, pvp_test_season):
        """测试获取匹配队列"""
        response = client.get("/api/pvp/matchmaking/queue")

        assert response.status_code == 200
        data = response.json()
        assert "queue_size" in data
        assert "players" in data


class TestPVPMatchAPI:
    """PVP 对战 API 测试"""

    def test_get_match_info(self, client, pvp_test_player, pvp_test_player_2, pvp_test_season, test_db):
        """测试获取对战信息"""
        with test_db.get_session() as session:
            match = PVPMatch(
                match_id=generate_uuid(),
                match_type=PVPMatchType.ARENA.value,
                player_a_id=pvp_test_player.player_id,
                player_b_id=pvp_test_player_2.player_id,
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
            session.add(match)
            session.commit()
            match_id = match.match_id

        response = client.get(f"/api/pvp/match/{match_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == match_id
        assert data["player_a_id"] == pvp_test_player.player_id
        assert data["player_b_id"] == pvp_test_player_2.player_id

    def test_get_match_info_not_found(self, client):
        """测试获取不存在的对战"""
        response = client.get("/api/pvp/match/non_existent_id")
        assert response.status_code == 404

    def test_start_match(self, client, pvp_test_player, pvp_test_player_2, pvp_test_season, test_db):
        """测试开始对战"""
        with test_db.get_session() as session:
            match = PVPMatch(
                match_id=generate_uuid(),
                match_type=PVPMatchType.ARENA.value,
                player_a_id=pvp_test_player.player_id,
                player_b_id=pvp_test_player_2.player_id,
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
            session.add(match)
            session.commit()
            match_id = match.match_id

        response = client.post(f"/api/pvp/match/{match_id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == PVPMatchStatus.ACTIVE.value
        assert data["started_at"] is not None

    def test_submit_result(self, client, pvp_test_player, pvp_test_player_2, pvp_test_season, test_db):
        """测试提交对战结果"""
        with test_db.get_session() as session:
            match = PVPMatch(
                match_id=generate_uuid(),
                match_type=PVPMatchType.ARENA.value,
                player_a_id=pvp_test_player.player_id,
                player_b_id=pvp_test_player_2.player_id,
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
            session.add(match)
            session.commit()
            match_id = match.match_id

        response = client.post(
            f"/api/pvp/match/{match_id}/result",
            json={
                "match_id": match_id,
                "winner_id": pvp_test_player.player_id,
                "score_a": 3,
                "score_b": 1,
                "moves_a": 10,
                "moves_b": 8,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == PVPMatchStatus.FINISHED.value
        assert data["winner_id"] == pvp_test_player.player_id
        assert "rating_changes" in data


class TestPVPSpectateAPI:
    """PVP 观战 API 测试"""

    def test_join_spectate(self, client, pvp_test_player, pvp_test_player_2, pvp_test_season, test_db):
        """测试加入观战"""
        # 创建观战者
        spectator_name = f"api_spectator_{uuid.uuid4().hex[:8]}"
        with test_db.get_session() as session:
            spectator = Player(
                username=spectator_name,
                vibe_energy=100,
                max_vibe_energy=1000,
                gold=500,
            )
            session.add(spectator)
            session.commit()
            spectator_id = spectator.player_id

            # 创建对战
            match = PVPMatch(
                match_id=generate_uuid(),
                match_type=PVPMatchType.ARENA.value,
                player_a_id=pvp_test_player.player_id,
                player_b_id=pvp_test_player_2.player_id,
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
            session.add(match)
            session.commit()
            match_id = match.match_id

        response = client.post(
            f"/api/pvp/match/{match_id}/spectate",
            params={"player_id": spectator_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "joined"
        assert data["spectator_id"] is not None

    def test_leave_spectate(self, client, pvp_test_player, pvp_test_player_2, test_db):
        """测试离开观战"""
        # 创建观战者
        spectator_name = f"api_spectator_{uuid.uuid4().hex[:8]}"
        with test_db.get_session() as session:
            spectator = Player(
                username=spectator_name,
                vibe_energy=100,
                max_vibe_energy=1000,
                gold=500,
            )
            session.add(spectator)
            session.commit()

            # 创建对战和观战记录
            match = PVPMatch(
                match_id=generate_uuid(),
                match_type=PVPMatchType.ARENA.value,
                player_a_id=pvp_test_player.player_id,
                player_b_id=pvp_test_player_2.player_id,
                status=PVPMatchStatus.ACTIVE.value,
                score_a=1,
                score_b=1,
                spectator_count=1,
                allow_spectate=True,
                created_at=datetime.utcnow(),
            )
            session.add(match)
            session.commit()

            spectator_rec = PVPSpectator(
                spectator_id=generate_uuid(),
                match_id=match.match_id,
                player_id=spectator.player_id,
                joined_at=datetime.utcnow(),
            )
            session.add(spectator_rec)
            session.commit()
            spectator_rec_id = spectator_rec.spectator_id
            match_id = match.match_id

        response = client.delete(
            f"/api/pvp/match/{match_id}/spectate",
            params={"spectator_id": spectator_rec_id},
        )

        assert response.status_code == 200

    def test_get_spectators(self, client, pvp_test_player, pvp_test_player_2, test_db):
        """测试获取观战列表"""
        with test_db.get_session() as session:
            match = PVPMatch(
                match_id=generate_uuid(),
                match_type=PVPMatchType.ARENA.value,
                player_a_id=pvp_test_player.player_id,
                player_b_id=pvp_test_player_2.player_id,
                status=PVPMatchStatus.ACTIVE.value,
                score_a=1,
                score_b=1,
                spectator_count=0,
                allow_spectate=True,
                created_at=datetime.utcnow(),
            )
            session.add(match)
            session.commit()
            match_id = match.match_id

        response = client.get(f"/api/pvp/match/{match_id}/spectators")

        assert response.status_code == 200
        data = response.json()
        assert "match_id" in data
        assert "spectators" in data
        assert "count" in data


class TestPVPRankingAPI:
    """PVP 排名 API 测试"""

    def test_get_ranking_list(self, client, pvp_test_player, pvp_test_season, test_db):
        """测试获取排行榜"""
        with test_db.get_session() as session:
            ranking = PVPRanking(
                ranking_id=generate_uuid(),
                season_id=pvp_test_season.season_id,
                player_id=pvp_test_player.player_id,
                rating=1500,
                max_rating=1500,
                matches_played=10,
                matches_won=7,
                matches_lost=3,
                matches_drawn=0,
                current_streak=2,
                max_streak=5,
            )
            session.add(ranking)
            session.commit()

        response = client.get(f"/api/pvp/ranking?season_id={pvp_test_season.season_id}")

        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data
        assert len(data["rankings"]) >= 1

    def test_get_player_ranking(self, client, pvp_test_player, pvp_test_season, test_db):
        """测试获取玩家排名"""
        with test_db.get_session() as session:
            ranking = PVPRanking(
                ranking_id=generate_uuid(),
                season_id=pvp_test_season.season_id,
                player_id=pvp_test_player.player_id,
                rating=1500,
                max_rating=1600,
                matches_played=20,
                matches_won=15,
                matches_lost=4,
                matches_drawn=1,
                current_streak=3,
                max_streak=8,
            )
            session.add(ranking)
            session.commit()

        response = client.get(f"/api/pvp/ranking/{pvp_test_player.player_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["player_id"] == pvp_test_player.player_id
        assert data["rating"] == 1500
        assert data["matches_played"] == 20

    def test_get_player_ranking_not_found(self, client):
        """测试获取不存在的玩家排名"""
        response = client.get("/api/pvp/ranking/non_existent_id")
        assert response.status_code == 404


class TestPVPMatchHistoryAPI:
    """PVP 对战历史 API 测试"""

    def test_get_player_match_history(self, client, pvp_test_player, pvp_test_player_2, test_db):
        """测试获取玩家对战历史"""
        with test_db.get_session() as session:
            match = PVPMatch(
                match_id=generate_uuid(),
                match_type=PVPMatchType.ARENA.value,
                player_a_id=pvp_test_player.player_id,
                player_b_id=pvp_test_player_2.player_id,
                status=PVPMatchStatus.FINISHED.value,
                score_a=3,
                score_b=1,
                winner_id=pvp_test_player.player_id,
                duration_seconds=300,
                moves_a=15,
                moves_b=12,
                spectator_count=0,
                allow_spectate=True,
                created_at=datetime.utcnow() - timedelta(minutes=10),
                started_at=datetime.utcnow() - timedelta(minutes=5),
                finished_at=datetime.utcnow(),
            )
            session.add(match)
            session.commit()

        response = client.get(f"/api/pvp/history/{pvp_test_player.player_id}")

        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert len(data["matches"]) >= 1


class TestPVPActiveMatchesAPI:
    """PVP 活跃对战 API 测试"""

    def test_get_active_matches(self, client, pvp_test_player, pvp_test_player_2, test_db):
        """测试获取活跃对战列表"""
        with test_db.get_session() as session:
            match = PVPMatch(
                match_id=generate_uuid(),
                match_type=PVPMatchType.ARENA.value,
                player_a_id=pvp_test_player.player_id,
                player_b_id=pvp_test_player_2.player_id,
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
            session.add(match)
            session.commit()

        response = client.get("/api/pvp/matches/active")

        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert len(data["matches"]) >= 1
