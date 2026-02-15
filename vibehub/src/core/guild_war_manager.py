"""公会战管理器

提供公会战的创建、管理、结算等功能。
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from src.storage.models import (
    Guild,
    GuildMember,
    GuildRole,
    GuildWar,
    GuildWarParticipant,
    GuildWarStatus,
    GuildWarType,
    Player,
    generate_uuid,
)

# 公会战奖励配置
WAR_REWARD_CONFIG = {
    GuildWarType.TERRITORY.value: {
        "winner_multiplier": 1.5,
        "loser_multiplier": 0.5,
        "base_diamonds": 100,
        "base_gold": 1000,
    },
    GuildWarType.RESOURCE.value: {
        "winner_multiplier": 1.2,
        "loser_multiplier": 0.6,
        "base_diamonds": 50,
        "base_gold": 500,
    },
    GuildWarType.HONOR.value: {
        "winner_multiplier": 2.0,
        "loser_multiplier": 0.3,
        "base_diamonds": 150,
        "base_gold": 2000,
    },
}


class GuildWarError(Exception):
    """公会战操作错误"""

    def __init__(self, message: str, code: str = "WAR_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class GuildWarManager:
    """公会战管理器

    负责公会战的创建、管理、结算等功能。
    """

    def __init__(self, session: Session):
        """初始化公会战管理器

        Args:
            session: 数据库会话
        """
        self.session = session

    # ==================== 公会战创建和管理 ====================

    def create_war(
        self,
        creator_id: str,
        guild_a_id: str,
        guild_b_id: str,
        war_type: str = GuildWarType.HONOR.value,
        duration_hours: int = 24,
        war_name: str | None = None,
        target_score: int = 1000,
    ) -> dict[str, Any]:
        """创建公会战

        Args:
            creator_id: 创建者玩家ID（必须是公会A的会长或干部）
            guild_a_id: 公会A ID（发起方）
            guild_b_id: 公会B ID（被挑战方）
            war_type: 战斗类型
            duration_hours: 持续小时数
            war_name: 战斗名称
            target_score: 目标分数

        Returns:
            创建结果

        Raises:
            GuildWarError: 创建失败时抛出
        """
        # 验证战斗类型
        if war_type not in [
            GuildWarType.TERRITORY.value,
            GuildWarType.RESOURCE.value,
            GuildWarType.HONOR.value,
        ]:
            raise GuildWarError("Invalid war type", "INVALID_WAR_TYPE")

        # 验证公会存在
        guild_a = self.session.get(Guild, guild_a_id)
        guild_b = self.session.get(Guild, guild_b_id)

        if not guild_a:
            raise GuildWarError("Guild A not found", "GUILD_A_NOT_FOUND")
        if not guild_b:
            raise GuildWarError("Guild B not found", "GUILD_B_NOT_FOUND")

        if guild_a_id == guild_b_id:
            raise GuildWarError("Cannot fight against yourself", "SAME_GUILD")

        # 检查创建者权限（必须是公会A的会长或干部）
        creator_member = self.session.scalar(
            select(GuildMember).where(
                and_(
                    GuildMember.player_id == creator_id,
                    GuildMember.guild_id == guild_a_id,
                    GuildMember.is_active,
                )
            )
        )

        if not creator_member:
            raise GuildWarError("Creator is not a member of guild A", "NOT_MEMBER")

        if creator_member.role not in [GuildRole.LEADER.value, GuildRole.OFFICER.value]:
            raise GuildWarError("Only leader and officer can create wars", "NO_PERMISSION")

        # 检查公会等级要求（需要达到一定等级才能参加公会战）
        min_level = 5
        if guild_a.level < min_level or guild_b.level < min_level:
            raise GuildWarError(f"Both guilds must be level {min_level} or higher", "LEVEL_TOO_LOW")

        # 检查是否已有进行中的战斗
        existing_war = self.session.scalar(
            select(GuildWar).where(
                and_(
                    or_(
                        and_(
                            GuildWar.guild_a_id == guild_a_id,
                            GuildWar.guild_b_id == guild_b_id,
                        ),
                        and_(
                            GuildWar.guild_a_id == guild_b_id,
                            GuildWar.guild_b_id == guild_a_id,
                        ),
                    ),
                    GuildWar.status.in_([
                        GuildWarStatus.PREPARING.value,
                        GuildWarStatus.ACTIVE.value,
                    ]),
                )
            )
        )

        if existing_war:
            raise GuildWarError("War already exists between these guilds", "WAR_EXISTS")

        # 计算奖励池
        reward_config = WAR_REWARD_CONFIG[war_type]
        reward_pool = reward_config["base_diamonds"] * duration_hours

        # 生成战斗名称
        if not war_name:
            war_name = f"{guild_a.guild_name} vs {guild_b.guild_name}"

        # 创建公会战
        war_id = generate_uuid()
        now = datetime.utcnow()
        end_time = now + timedelta(hours=duration_hours)

        war = GuildWar(
            war_id=war_id,
            war_name=war_name,
            war_type=war_type,
            guild_a_id=guild_a_id,
            guild_b_id=guild_b_id,
            score_a=0,
            score_b=0,
            target_score=target_score,
            status=GuildWarStatus.PREPARING.value,
            winner_id=None,
            start_time=now,
            end_time=end_time,
            duration_hours=duration_hours,
            reward_pool=reward_pool,
        )

        self.session.add(war)

        return {
            "war_id": war_id,
            "war_name": war_name,
            "status": war.status,
            "start_time": war.start_time.isoformat(),
            "end_time": war.end_time.isoformat(),
            "message": "Guild war created successfully",
        }

    def start_war(self, war_id: str) -> dict[str, Any]:
        """开始公会战

        Args:
            war_id: 公会战ID

        Returns:
            开始结果

        Raises:
            GuildWarError: 开始失败时抛出
        """
        war = self.session.get(GuildWar, war_id)
        if not war:
            raise GuildWarError("War not found", "WAR_NOT_FOUND")

        if war.status != GuildWarStatus.PREPARING.value:
            raise GuildWarError(f"Cannot start war in status: {war.status}", "INVALID_STATUS")

        # 更新状态为进行中
        war.status = GuildWarStatus.ACTIVE.value

        return {
            "success": True,
            "war_id": war_id,
            "status": war.status,
            "message": "Guild war started",
        }

    def get_war_info(self, war_id: str) -> dict[str, Any]:
        """获取公会战信息

        Args:
            war_id: 公会战ID

        Returns:
            公会战详情

        Raises:
            GuildWarError: 获取失败时抛出
        """
        war = self.session.get(GuildWar, war_id)
        if not war:
            raise GuildWarError("War not found", "WAR_NOT_FOUND")

        # 获取对战公会信息
        guild_a = self.session.get(Guild, war.guild_a_id)
        guild_b = self.session.get(Guild, war.guild_b_id)

        # 获取参与者列表
        participants_a = self.session.scalars(
            select(GuildWarParticipant).where(
                and_(
                    GuildWarParticipant.war_id == war_id,
                    GuildWarParticipant.guild_id == war.guild_a_id,
                )
            )
        ).all()

        participants_b = self.session.scalars(
            select(GuildWarParticipant).where(
                and_(
                    GuildWarParticipant.war_id == war_id,
                    GuildWarParticipant.guild_id == war.guild_b_id,
                )
            )
        ).all()

        # 构建参与者信息
        def build_participant_list(participants):
            result = []
            for p in participants:
                player = self.session.get(Player, p.player_id)
                result.append({
                    "player_id": p.player_id,
                    "username": player.username if player else f"Player_{p.player_id[:8]}",
                    "score": p.score,
                    "battles_won": p.battles_won,
                    "damage_dealt": p.damage_dealt,
                    "personal_reward_claimed": p.personal_reward_claimed,
                })
            return sorted(result, key=lambda x: -x["score"])

        return {
            "war_id": war.war_id,
            "war_name": war.war_name,
            "war_type": war.war_type,
            "status": war.status,
            "start_time": war.start_time.isoformat() if war.start_time else None,
            "end_time": war.end_time.isoformat() if war.end_time else None,
            "duration_hours": war.duration_hours,
            "target_score": war.target_score,
            "reward_pool": war.reward_pool,
            "guild_a": {
                "guild_id": guild_a.guild_id if guild_a else war.guild_a_id,
                "guild_name": guild_a.guild_name if guild_a else "Unknown",
                "score": war.score_a,
                "participants": build_participant_list(participants_a),
            },
            "guild_b": {
                "guild_id": guild_b.guild_id if guild_b else war.guild_b_id,
                "guild_name": guild_b.guild_name if guild_b else "Unknown",
                "score": war.score_b,
                "participants": build_participant_list(participants_b),
            },
            "winner_id": war.winner_id,
        }

    def get_active_wars(self, guild_id: str | None = None) -> dict[str, Any]:
        """获取进行中的公会战列表

        Args:
            guild_id: 可选，筛选特定公会的战斗

        Returns:
            公会战列表
        """
        query = select(GuildWar).where(
            GuildWar.status.in_([
                GuildWarStatus.PREPARING.value,
                GuildWarStatus.ACTIVE.value,
            ])
        )

        if guild_id:
            query = query.where(
                or_(
                    GuildWar.guild_a_id == guild_id,
                    GuildWar.guild_b_id == guild_id,
                )
            )

        query = query.order_by(GuildWar.start_time.desc())

        wars = self.session.scalars(query).all()

        result = []
        for war in wars:
            guild_a = self.session.get(Guild, war.guild_a_id)
            guild_b = self.session.get(Guild, war.guild_b_id)

            result.append({
                "war_id": war.war_id,
                "war_name": war.war_name,
                "war_type": war.war_type,
                "status": war.status,
                "guild_a_name": guild_a.guild_name if guild_a else "Unknown",
                "guild_b_name": guild_b.guild_name if guild_b else "Unknown",
                "score_a": war.score_a,
                "score_b": war.score_b,
                "target_score": war.target_score,
                "start_time": war.start_time.isoformat() if war.start_time else None,
                "end_time": war.end_time.isoformat() if war.end_time else None,
            })

        return {
            "wars": result,
            "count": len(result),
        }

    def get_war_history(
        self,
        guild_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """获取公会战历史记录

        Args:
            guild_id: 可选，筛选特定公会的战斗
            page: 页码
            page_size: 每页数量

        Returns:
            公会战历史列表
        """
        query = select(GuildWar).where(
            GuildWar.status == GuildWarStatus.FINISHED.value
        )

        if guild_id:
            query = query.where(
                or_(
                    GuildWar.guild_a_id == guild_id,
                    GuildWar.guild_b_id == guild_id,
                )
            )

        # 获取总数
        count_query = select(func.count(GuildWar.war_id)).where(GuildWar.status == GuildWarStatus.FINISHED.value)
        if guild_id:
            count_query = count_query.where(
                or_(
                    GuildWar.guild_a_id == guild_id,
                    GuildWar.guild_b_id == guild_id,
                )
            )
        total_result = self.session.execute(count_query).scalar()
        total = total_result or 0

        # 分页
        query = query.order_by(GuildWar.end_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        wars = self.session.scalars(query).all()

        result = []
        for war in wars:
            guild_a = self.session.get(Guild, war.guild_a_id)
            guild_b = self.session.get(Guild, war.guild_b_id)
            winner = self.session.get(Guild, war.winner_id) if war.winner_id else None

            result.append({
                "war_id": war.war_id,
                "war_name": war.war_name,
                "war_type": war.war_type,
                "guild_a_name": guild_a.guild_name if guild_a else "Unknown",
                "guild_b_name": guild_b.guild_name if guild_b else "Unknown",
                "winner_name": winner.guild_name if winner else None,
                "score_a": war.score_a,
                "score_b": war.score_b,
                "end_time": war.end_time.isoformat() if war.end_time else None,
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "wars": result,
        }

    # ==================== 分数更新 ====================

    def update_score(
        self,
        war_id: str,
        player_id: str,
        score_delta: int,
        damage_dealt: int = 0,
        battle_won: bool = False,
    ) -> dict[str, Any]:
        """更新玩家在公会战中的分数

        Args:
            war_id: 公会战ID
            player_id: 玩家ID
            score_delta: 分数增量
            damage_dealt: 造成伤害
            battle_won: 是否获胜本场

        Returns:
            更新结果

        Raises:
            GuildWarError: 更新失败时抛出
        """
        if score_delta <= 0:
            raise GuildWarError("Invalid score delta", "INVALID_SCORE")

        war = self.session.get(GuildWar, war_id)
        if not war:
            raise GuildWarError("War not found", "WAR_NOT_FOUND")

        if war.status != GuildWarStatus.ACTIVE.value:
            raise GuildWarError(f"Cannot update score in status: {war.status}", "INVALID_STATUS")

        # 检查玩家是否在任一公会中
        member = self.session.scalar(
            select(GuildMember).where(
                and_(
                    GuildMember.player_id == player_id,
                    GuildMember.is_active,
                )
            )
        )

        if not member:
            raise GuildWarError("Player not in a guild", "NOT_IN_GUILD")

        if member.guild_id not in [war.guild_a_id, war.guild_b_id]:
            raise GuildWarError("Player's guild is not in this war", "NOT_PARTICIPANT")

        # 获取或创建参与记录
        participant = self.session.scalar(
            select(GuildWarParticipant).where(
                and_(
                    GuildWarParticipant.war_id == war_id,
                    GuildWarParticipant.player_id == player_id,
                )
            )
        )

        if not participant:
            # 创建参与记录
            participant = GuildWarParticipant(
                participation_id=generate_uuid(),
                war_id=war_id,
                player_id=player_id,
                guild_id=member.guild_id,
                score=0,
                battles_won=0,
                damage_dealt=0,
                personal_reward_claimed=False,
            )
            self.session.add(participant)
            self.session.flush()

        # 更新参与者数据
        participant.score += score_delta
        participant.damage_dealt += damage_dealt
        if battle_won:
            participant.battles_won += 1

        # 更新公会分数
        if member.guild_id == war.guild_a_id:
            war.score_a += score_delta
            guild_score = war.score_a
        else:
            war.score_b += score_delta
            guild_score = war.score_b

        # 检查是否提前结束（任一方达到目标分数）
        early_finish = False
        if guild_score >= war.target_score:
            early_finish = True
            return self._finish_war(war, early_finish=True)

        return {
            "success": True,
            "war_id": war_id,
            "player_id": player_id,
            "score_added": score_delta,
            "total_score": participant.score,
            "guild_score": guild_score,
            "early_finish": early_finish,
        }

    # ==================== 结算和奖励 ====================

    def end_war(self, war_id: str, force_winner_id: str | None = None) -> dict[str, Any]:
        """结束公会战（手动结束）

        Args:
            war_id: 公会战ID
            force_winner_id: 强制指定获胜公会ID（可选）

        Returns:
            结束结果

        Raises:
            GuildWarError: 结束失败时抛出
        """
        war = self.session.get(GuildWar, war_id)
        if not war:
            raise GuildWarError("War not found", "WAR_NOT_FOUND")

        if war.status == GuildWarStatus.FINISHED.value:
            raise GuildWarError("War already finished", "ALREADY_FINISHED")

        # 如果指定了获胜者
        if force_winner_id:
            if force_winner_id not in [war.guild_a_id, war.guild_b_id]:
                raise GuildWarError("Invalid winner guild", "INVALID_WINNER")
            war.winner_id = force_winner_id

        return self._finish_war(war, early_finish=False)

    def _finish_war(self, war: GuildWar, early_finish: bool = False) -> dict[str, Any]:
        """完成公会战结算

        Args:
            war: 公会战对象
            early_finish: 是否提前结束

        Returns:
            结算结果
        """
        # 确定获胜方
        if not war.winner_id:
            if war.score_a > war.score_b:
                war.winner_id = war.guild_a_id
            elif war.score_b > war.score_a:
                war.winner_id = war.guild_b_id
            # 平局则无获胜方

        # 更新状态
        war.status = GuildWarStatus.FINISHED.value

        # 分发奖励
        self._distribute_rewards(war)

        return {
            "success": True,
            "war_id": war.war_id,
            "winner_id": war.winner_id,
            "final_score": f"{war.score_a}:{war.score_b}",
            "early_finish": early_finish,
            "message": "Guild war finished",
        }

    def _distribute_rewards(self, war: GuildWar) -> None:
        """分发公会战奖励

        Args:
            war: 公会战对象
        """
        reward_config = WAR_REWARD_CONFIG.get(war.war_type, WAR_REWARD_CONFIG[GuildWarType.HONOR.value])

        # 获取双方参与者
        participants_a = self.session.scalars(
            select(GuildWarParticipant).where(
                and_(
                    GuildWarParticipant.war_id == war.war_id,
                    GuildWarParticipant.guild_id == war.guild_a_id,
                )
            )
        ).all()

        participants_b = self.session.scalars(
            select(GuildWarParticipant).where(
                and_(
                    GuildWarParticipant.war_id == war.war_id,
                    GuildWarParticipant.guild_id == war.guild_b_id,
                )
            )
        ).all()

        # 确定胜者和败者
        if war.winner_id == war.guild_a_id:
            winners_participants = participants_a
            losers_participants = participants_b
        elif war.winner_id == war.guild_b_id:
            winners_participants = participants_b
            losers_participants = participants_a
        else:
            # 平局，双方都是败者奖励
            winners_participants = []
            losers_participants = participants_a + participants_b

        # 计算个人奖励（基于贡献）
        def calculate_personal_rewards(participants, multiplier):
            rewards = {}
            if not participants:
                return rewards

            total_score = sum(p.score for p in participants)
            if total_score == 0:
                # 平均分配
                base_diamonds = reward_config["base_diamonds"]
                base_gold = reward_config["base_gold"]
                for p in participants:
                    rewards[p.player_id] = {
                        "diamonds": int(base_diamonds * multiplier / len(participants)),
                        "gold": int(base_gold * multiplier / len(participants)),
                    }
            else:
                # 按分数比例分配
                for p in participants:
                    share = p.score / total_score
                    rewards[p.player_id] = {
                        "diamonds": int(reward_config["base_diamonds"] * multiplier * share * len(participants)),
                        "gold": int(reward_config["base_gold"] * multiplier * share * len(participants)),
                    }
            return rewards

        winner_rewards = calculate_personal_rewards(
            winners_participants,
            reward_config["winner_multiplier"]
        )
        loser_rewards = calculate_personal_rewards(
            losers_participants,
            reward_config["loser_multiplier"]
        )

        # 应用奖励到玩家
        all_rewards = {**winner_rewards, **loser_rewards}
        for player_id, reward in all_rewards.items():
            player = self.session.get(Player, player_id)
            if player:
                player.gold += reward["gold"]
                player.diamonds += reward["diamonds"]

    def claim_war_reward(
        self,
        player_id: str,
        war_id: str,
    ) -> dict[str, Any]:
        """领取公会战个人奖励（预留接口）

        当前奖励在战争结束时自动发放，此接口用于未来的手动领取系统。

        Args:
            player_id: 玩家ID
            war_id: 公会战ID

        Returns:
            领取结果

        Raises:
            GuildWarError: 领取失败时抛出
        """
        war = self.session.get(GuildWar, war_id)
        if not war:
            raise GuildWarError("War not found", "WAR_NOT_FOUND")

        if war.status != GuildWarStatus.FINISHED.value:
            raise GuildWarError("War not finished yet", "WAR_NOT_FINISHED")

        participant = self.session.scalar(
            select(GuildWarParticipant).where(
                and_(
                    GuildWarParticipant.war_id == war_id,
                    GuildWarParticipant.player_id == player_id,
                )
            )
        )

        if not participant:
            raise GuildWarError("Player did not participate in this war", "NOT_PARTICIPATED")

        if participant.personal_reward_claimed:
            raise GuildWarError("Reward already claimed", "ALREADY_CLAIMED")

        # 标记为已领取
        participant.personal_reward_claimed = True

        # 计算奖励（基于个人表现）
        reward_config = WAR_REWARD_CONFIG.get(war.war_type, WAR_REWARD_CONFIG[GuildWarType.HONOR.value])

        is_winner = (war.winner_id is not None and
                    self.session.scalar(
                        select(GuildMember).where(
                            and_(
                                GuildMember.player_id == player_id,
                                GuildMember.guild_id == war.winner_id,
                                GuildMember.is_active,
                            )
                        )
                    ) is not None)

        multiplier = (
            reward_config["winner_multiplier"] if is_winner
            else reward_config["loser_multiplier"]
        )

        diamonds = int(reward_config["base_diamonds"] * multiplier * (1 + participant.score / 10000))
        gold = int(reward_config["base_gold"] * multiplier * (1 + participant.score / 10000))

        # 发放奖励
        player = self.session.get(Player, player_id)
        if player:
            player.diamonds += diamonds
            player.gold += gold

        return {
            "success": True,
            "diamonds": diamonds,
            "gold": gold,
            "message": "Reward claimed successfully",
        }

    # ==================== 自动结束检测 ====================

    def check_and_finish_expired_wars(self) -> list[dict[str, Any]]:
        """检查并结束已过期的公会战（定时任务调用）

        Returns:
            已结束的公会战列表
        """
        now = datetime.utcnow()

        # 查找已过期但未结束的公会战
        expired_wars = self.session.scalars(
            select(GuildWar).where(
                and_(
                    GuildWar.end_time < now,
                    GuildWar.status != GuildWarStatus.FINISHED.value,
                )
            )
        ).all()

        finished = []
        for war in expired_wars:
            result = self._finish_war(war, early_finish=False)
            finished.append({
                "war_id": war.war_id,
                "war_name": war.war_name,
                "result": result,
            })

        return finished

    # ==================== 战斗匹配 ====================

    def find_opponent(
        self,
        guild_id: str,
        war_type: str = GuildWarType.HONOR.value,
        level_diff: int = 3,
    ) -> list[dict[str, Any]]:
        """查找可对战公会

        Args:
            guild_id: 公会ID
            war_type: 战斗类型
            level_diff: 等级差异限制

        Returns:
            可对战公会列表
        """
        guild = self.session.get(Guild, guild_id)
        if not guild:
            raise GuildWarError("Guild not found", "GUILD_NOT_FOUND")

        # 等级筛选
        min_level = max(1, guild.level - level_diff)
        max_level = guild.level + level_diff

        # 查找符合条件的公会
        candidates = self.session.scalars(
            select(Guild).where(
                and_(
                    Guild.guild_id != guild_id,
                    Guild.level >= min_level,
                    Guild.level <= max_level,
                    Guild.disbanded_at.is_(None),
                )
            )
        ).all()

        # 排除已有进行中战斗的公会
        result = []
        for candidate in candidates:
            # 检查是否已有战斗
            existing_war = self.session.scalar(
                select(GuildWar).where(
                    and_(
                        or_(
                            and_(
                                GuildWar.guild_a_id == guild_id,
                                GuildWar.guild_b_id == candidate.guild_id,
                            ),
                            and_(
                                GuildWar.guild_a_id == candidate.guild_id,
                                GuildWar.guild_b_id == guild_id,
                            ),
                        ),
                        GuildWar.status.in_([
                            GuildWarStatus.PREPARING.value,
                            GuildWarStatus.ACTIVE.value,
                        ]),
                    )
                )
            )

            if not existing_war:
                # 获取活跃成员数
                active_members = self.session.scalar(
                    select(func.count(GuildMember.membership_id)).where(
                        and_(
                            GuildMember.guild_id == candidate.guild_id,
                            GuildMember.is_active,
                        )
                    )
                ) or candidate.member_count

                result.append({
                    "guild_id": candidate.guild_id,
                    "guild_name": candidate.guild_name,
                    "level": candidate.level,
                    "member_count": active_members,
                    "contribution_points": candidate.contribution_points,
                    "level_diff": abs(candidate.level - guild.level),
                })

        # 按等级和贡献度排序
        result.sort(key=lambda x: (x["level_diff"], -x["contribution_points"]))

        return result[:10]  # 返回前10个候选
