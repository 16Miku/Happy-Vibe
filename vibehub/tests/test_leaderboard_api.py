"""排行榜和赛季 API 单元测试"""

import pytest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from src.main import app
from src.storage.models import Base, Player, Season, SeasonType
from src.storage.database import Database


@pytest.fixture
def in_memory_db():
    """创建内存数据库"""
    engine = Database(":memory:")
    engine.create_tables()
    return engine


@pytest.fixture
def client(in_memory_db):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def test_season(in_memory_db):
    """创建测试赛季"""
    now = datetime.utcnow()
    with in_memory_db.get_session() as session:
        season = Season(
            season_id="test-season-1",
            season_name="Test Season 1",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=30),
            reward_tiers='{"1": {"rewards": {"gold": 1000}}}',
            is_active=True,
        )
        session.add(season)
        session.commit()
    return "test-season-1"


@pytest.fixture
def test_players(in_memory_db):
    """创建测试玩家"""
    with in_memory_db.get_session() as session:
        players = []
        for i in range(5):
            player = Player(
                username=f"player{i}",
                level=10 + i,
                experience=1000 * (i + 1),
                gold=500 * (i + 1),
            )
            session.add(player)
            session.flush()
            players.append(player)
        session.commit()
    return players


class TestSeasonAPI:
    """赛季 API 测试"""

    def test_get_season_types(self, client: TestClient):
        """测试获取赛季类型"""
        response = client.get("/api/season/types/available")

        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) == 3

    def test_get_current_season(self, client: TestClient, test_season: str):
        """测试获取当前赛季"""
        response = client.get("/api/season/current")

        assert response.status_code == 200
        data = response.json()
        assert data["season_id"] == test_season
        assert data["is_active"] is True

    def test_get_season_list(self, client: TestClient, test_season: str):
        """测试获取赛季列表"""
        response = client.get("/api/season/list?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "seasons" in data
        assert len(data["seasons"]) >= 1

    def test_get_season_by_id(self, client: TestClient, test_season: str):
        """测试通过ID获取赛季"""
        response = client.get(f"/api/season/{test_season}")

        assert response.status_code == 200
        data = response.json()
        assert data["season_id"] == test_season
        assert data["season_name"] == "Test Season 1"

    def test_get_season_status(self, client: TestClient, test_season: str):
        """测试获取赛季状态"""
        response = client.get(f"/api/season/{test_season}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["season_id"] == test_season
        assert data["status"] == "active"
        assert "remaining_time" in data

    def test_create_season(self, client: TestClient):
        """测试创建赛季"""
        now = datetime.utcnow()
        request_data = {
            "season_name": "New Season",
            "season_number": 2,
            "season_type": "regular",
            "start_time": (now + timedelta(days=30)).isoformat(),
            "end_time": (now + timedelta(days=60)).isoformat(),
            "reward_tiers": {
                "1": {"range": "1", "rewards": {"gold": 1000}},
                "2-3": {"range": "2-3", "rewards": {"gold": 500}},
            },
        }

        response = client.post("/api/season", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["season_name"] == "New Season"
        assert data["season_number"] == 2
        assert data["is_active"] is False

    def test_create_season_invalid_dates(self, client: TestClient):
        """测试创建赛季时日期无效"""
        now = datetime.utcnow()
        request_data = {
            "season_name": "Invalid Season",
            "season_number": 3,
            "season_type": "regular",
            "start_time": (now + timedelta(days=60)).isoformat(),
            "end_time": (now + timedelta(days=30)).isoformat(),  # 结束时间早于开始时间
        }

        response = client.post("/api/season", json=request_data)

        assert response.status_code == 400

    def test_activate_season(self, client: TestClient, in_memory_db):
        """测试激活赛季"""
        # 先创建一个新赛季
        now = datetime.utcnow()
        with in_memory_db.get_session() as session:
            season = Season(
                season_id="test-season-2",
                season_name="Test Season 2",
                season_number=2,
                season_type=SeasonType.REGULAR.value,
                start_time=now - timedelta(days=1),
                end_time=now + timedelta(days=30),
                is_active=False,
            )
            session.add(season)
            session.commit()

        response = client.post(f"/api/season/test-season-2/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_get_nonexistent_season(self, client: TestClient):
        """测试获取不存在的赛季"""
        response = client.get("/api/season/nonexistent-id")

        assert response.status_code == 404


class TestLeaderboardAPI:
    """排行榜 API 测试"""

    def test_get_leaderboard_types(self, client: TestClient):
        """测试获取排行榜类型"""
        response = client.get("/api/leaderboard/types")

        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) == 3

    def test_get_leaderboard(
        self, client: TestClient, test_season: str, test_players: list
    ):
        """测试获取排行榜"""
        response = client.get(
            f"/api/leaderboard/individual?season_id={test_season}&limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert "leaderboard_id" in data
        assert data["season_id"] == test_season
        assert data["leaderboard_type"] == "individual"

    def test_update_leaderboard(
        self, client: TestClient, test_season: str, test_players: list
    ):
        """测试更新排行榜"""
        response = client.post(
            f"/api/leaderboard/individual/update?season_id={test_season}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["season_id"] == test_season
        assert data["total"] == len(test_players)

    def test_get_player_rank(
        self, client: TestClient, test_season: str, test_players: list
    ):
        """测试获取玩家排名"""
        # 先更新排行榜
        client.post(f"/api/leaderboard/individual/update?season_id={test_season}")

        # 获取玩家排名
        response = client.get(
            f"/api/leaderboard/individual/rank/{test_players[0].player_id}?season_id={test_season}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["player_id"] == test_players[0].player_id
        assert "rank" in data
        assert data["total"] == len(test_players)

    def test_get_top_players(
        self, client: TestClient, test_season: str, test_players: list
    ):
        """测试获取前N名玩家"""
        # 先更新排行榜
        client.post(f"/api/leaderboard/individual/update?season_id={test_season}")

        response = client.get(
            f"/api/leaderboard/individual/top?season_id={test_season}&limit=3"
        )

        assert response.status_code == 200
        data = response.json()
        assert "players" in data
        assert len(data["players"]) == 3

    def test_create_snapshot(
        self, client: TestClient, test_season: str, test_players: list
    ):
        """测试创建快照"""
        # 先更新排行榜
        client.post(f"/api/leaderboard/individual/update?season_id={test_season}")

        response = client.post(
            f"/api/leaderboard/individual/snapshot?season_id={test_season}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "snapshot_id" in data

    def test_get_snapshots(
        self, client: TestClient, test_season: str, test_players: list
    ):
        """测试获取快照列表"""
        # 先更新排行榜并创建快照
        client.post(f"/api/leaderboard/individual/update?season_id={test_season}")
        client.post(f"/api/leaderboard/individual/snapshot?season_id={test_season}")

        response = client.get(
            f"/api/leaderboard/individual/snapshots?season_id={test_season}&limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert "snapshots" in data
        assert len(data["snapshots"]) >= 1

    def test_invalid_leaderboard_type(self, client: TestClient, test_season: str):
        """测试无效的排行榜类型"""
        response = client.get(
            f"/api/leaderboard/invalid_type?season_id={test_season}&limit=10"
        )

        assert response.status_code == 400

    def test_get_leaderboard_around_player(
        self, client: TestClient, test_season: str, test_players: list
    ):
        """测试获取玩家周围的排行榜"""
        # 先更新排行榜
        client.post(f"/api/leaderboard/individual/update?season_id={test_season}")

        response = client.get(
            f"/api/leaderboard/around/{test_players[0].player_id}?season_id={test_season}&range_size=2"
        )

        assert response.status_code == 200
        data = response.json()
        assert "player_id" in data
        assert "entries" in data

    def test_guild_leaderboard(
        self, client: TestClient, test_season: str, in_memory_db
    ):
        """测试公会排行榜"""
        # 创建测试公会
        from src.storage.models import Guild

        with in_memory_db.get_session() as session:
            guild = Guild(
                guild_id="test-guild-1",
                guild_name="Test Guild",
                leader_id="leader-1",
                level=5,
                member_count=10,
                contribution_points=500,
            )
            session.add(guild)
            session.commit()

        response = client.get(
            f"/api/leaderboard/guild?season_id={test_season}&limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["leaderboard_type"] == "guild"

    def test_achievement_leaderboard(
        self, client: TestClient, test_season: str, test_players: list
    ):
        """测试成就排行榜"""
        response = client.get(
            f"/api/leaderboard/achievement?season_id={test_season}&limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["leaderboard_type"] == "achievement"
