"""签到 API 端点测试"""

from datetime import datetime, date, timedelta

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.storage.models import Player, CheckInRecord


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def check_in_player(test_db):
    """创建签到测试专用玩家"""
    with test_db.get_session() as session:
        player = Player(
            player_id="check-in-test-player",
            username="test_check_in_user",
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
            experience=0,
            consecutive_days=0,
            last_login_date=None
        )
        session.add(player)
    return "check-in-test-player"


class TestCheckInAPI:
    """签到 API 测试"""

    def test_check_in_first_time(self, client, check_in_player, test_db):
        """测试首次签到"""
        response = client.post("/api/check-in")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["consecutive_days"] == 1
        assert data["is_success"] is True
        assert data["reward"]["base_energy"] == 50
        assert data["reward"]["streak_bonus"] == 0
        assert data["reward"]["total_energy"] == 50

        # 验证数据库更新
        with test_db.get_session() as session:
            player = session.query(Player).filter_by(player_id=check_in_player).first()
            assert player.consecutive_days == 1
            assert player.vibe_energy == 150  # 100 + 50

    def test_check_in_consecutive(self, client, check_in_player, test_db):
        """测试连续签到"""
        # 设置昨天签到过
        yesterday = datetime.combine(
            date.today() - timedelta(days=1),
            datetime.min.time()
        )
        with test_db.get_session() as session:
            player = session.query(Player).filter_by(player_id=check_in_player).first()
            player.last_login_date = yesterday
            player.consecutive_days = 3

        response = client.post("/api/check-in")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["consecutive_days"] == 4
        assert data["previous_consecutive_days"] == 3
        assert data["reward"]["streak_bonus"] == 30  # (4-1) * 10

    def test_check_in_already_checked(self, client, check_in_player, test_db):
        """测试今日已签到"""
        # 设置今天已签到
        today = datetime.combine(date.today(), datetime.min.time())
        with test_db.get_session() as session:
            player = session.query(Player).filter_by(player_id=check_in_player).first()
            player.last_login_date = today
            player.consecutive_days = 5

        response = client.post("/api/check-in")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "already_checked"
        assert data["is_success"] is False
        assert data["consecutive_days"] == 5
        assert data["reward"]["total_energy"] == 0

    def test_check_in_streak_broken(self, client, check_in_player, test_db):
        """测试连续签到中断"""
        # 设置3天前签到过
        three_days_ago = datetime.combine(
            date.today() - timedelta(days=3),
            datetime.min.time()
        )
        with test_db.get_session() as session:
            player = session.query(Player).filter_by(player_id=check_in_player).first()
            player.last_login_date = three_days_ago
            player.consecutive_days = 10

        response = client.post("/api/check-in")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "streak_broken"
        assert data["consecutive_days"] == 1
        assert data["previous_consecutive_days"] == 10
        assert data["is_success"] is True

    def test_check_in_milestone_reward(self, client, check_in_player, test_db):
        """测试里程碑奖励"""
        # 设置昨天签到，连续6天
        yesterday = datetime.combine(
            date.today() - timedelta(days=1),
            datetime.min.time()
        )
        with test_db.get_session() as session:
            player = session.query(Player).filter_by(player_id=check_in_player).first()
            player.last_login_date = yesterday
            player.consecutive_days = 6

        response = client.post("/api/check-in")

        assert response.status_code == 200
        data = response.json()

        assert data["consecutive_days"] == 7
        assert data["reward"]["special_item"] == "function_flower_seed"
        assert "里程碑" in data["message"]

    def test_check_in_no_player(self, client, test_db):
        """测试无玩家时签到"""
        # 不创建玩家，直接签到
        response = client.post("/api/check-in")

        assert response.status_code == 404
        assert "玩家不存在" in response.json()["detail"]


class TestCheckInStatusAPI:
    """签到状态 API 测试"""

    def test_get_status_not_checked(self, client, check_in_player, test_db):
        """测试获取状态 - 未签到"""
        response = client.get("/api/check-in/status")

        assert response.status_code == 200
        data = response.json()

        assert data["is_checked_today"] is False
        assert data["expected_streak_after_check_in"] == 1
        assert data["expected_reward"] is not None

    def test_get_status_already_checked(self, client, check_in_player, test_db):
        """测试获取状态 - 已签到"""
        today = datetime.combine(date.today(), datetime.min.time())
        with test_db.get_session() as session:
            player = session.query(Player).filter_by(player_id=check_in_player).first()
            player.last_login_date = today
            player.consecutive_days = 5

        response = client.get("/api/check-in/status")

        assert response.status_code == 200
        data = response.json()

        assert data["is_checked_today"] is True
        assert data["current_consecutive_days"] == 5
        assert data["expected_reward"] is None

    def test_get_status_will_break_streak(self, client, check_in_player, test_db):
        """测试获取状态 - 将中断连续"""
        three_days_ago = datetime.combine(
            date.today() - timedelta(days=3),
            datetime.min.time()
        )
        with test_db.get_session() as session:
            player = session.query(Player).filter_by(player_id=check_in_player).first()
            player.last_login_date = three_days_ago
            player.consecutive_days = 8

        response = client.get("/api/check-in/status")

        assert response.status_code == 200
        data = response.json()

        assert data["is_checked_today"] is False
        assert data["will_break_streak"] is True
        assert data["expected_streak_after_check_in"] == 1

    def test_get_status_next_milestone(self, client, check_in_player, test_db):
        """测试获取状态 - 下一个里程碑"""
        yesterday = datetime.combine(
            date.today() - timedelta(days=1),
            datetime.min.time()
        )
        with test_db.get_session() as session:
            player = session.query(Player).filter_by(player_id=check_in_player).first()
            player.last_login_date = yesterday
            player.consecutive_days = 5

        response = client.get("/api/check-in/status")

        assert response.status_code == 200
        data = response.json()

        # 签到后是第6天，下一个里程碑是7天
        assert data["next_milestone"] is not None
        assert data["next_milestone"]["days"] == 7
        assert data["next_milestone"]["days_remaining"] == 1


class TestCheckInHistoryAPI:
    """签到历史 API 测试"""

    def test_get_history_empty(self, client, check_in_player, test_db):
        """测试获取空历史"""
        response = client.get("/api/check-in/history")

        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 0
        assert data["records"] == []

    def test_get_history_with_records(self, client, check_in_player, test_db):
        """测试获取有记录的历史"""
        # 创建签到记录
        with test_db.get_session() as session:
            for i in range(5):
                record = CheckInRecord(
                    player_id=check_in_player,
                    check_in_date=datetime.combine(
                        date.today() - timedelta(days=i),
                        datetime.min.time()
                    ),
                    consecutive_days=5 - i,
                    energy_reward=50 + (4 - i) * 10,
                    gold_reward=10,
                    exp_reward=20
                )
                session.add(record)

        response = client.get("/api/check-in/history")

        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 5
        assert len(data["records"]) == 5
        # 验证按日期降序排列
        assert data["records"][0]["consecutive_days"] == 5

    def test_get_history_pagination(self, client, check_in_player, test_db):
        """测试历史分页"""
        # 创建10条记录
        with test_db.get_session() as session:
            for i in range(10):
                record = CheckInRecord(
                    player_id=check_in_player,
                    check_in_date=datetime.combine(
                        date.today() - timedelta(days=i),
                        datetime.min.time()
                    ),
                    consecutive_days=i + 1,
                    energy_reward=50,
                    gold_reward=10,
                    exp_reward=20
                )
                session.add(record)

        # 获取前5条
        response = client.get("/api/check-in/history?limit=5&offset=0")
        data = response.json()

        assert data["total_count"] == 10
        assert len(data["records"]) == 5

        # 获取后5条
        response = client.get("/api/check-in/history?limit=5&offset=5")
        data = response.json()

        assert data["total_count"] == 10
        assert len(data["records"]) == 5

    def test_get_history_with_special_item(self, client, check_in_player, test_db):
        """测试获取包含特殊物品的历史"""
        with test_db.get_session() as session:
            record = CheckInRecord(
                player_id=check_in_player,
                check_in_date=datetime.combine(date.today(), datetime.min.time()),
                consecutive_days=7,
                energy_reward=110,
                gold_reward=110,
                exp_reward=20,
                special_item="function_flower_seed"
            )
            session.add(record)

        response = client.get("/api/check-in/history")

        assert response.status_code == 200
        data = response.json()

        assert data["records"][0]["special_item"] == "function_flower_seed"
