"""数据库管理模块

提供数据库连接、初始化和会话管理功能。
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import settings
from src.storage.models import Base


class Database:
    """数据库管理类

    负责数据库的初始化、连接管理和会话创建。
    """

    def __init__(self, db_path: str | None = None):
        """初始化数据库

        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        self.db_path = db_path or settings.DATABASE_PATH
        self._ensure_data_dir()

        # 创建数据库引擎
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
        )

        # 启用 SQLite 外键约束
        self._enable_foreign_keys()

        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

    def _ensure_data_dir(self) -> None:
        """确保数据目录存在"""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)

    def _enable_foreign_keys(self) -> None:
        """启用 SQLite 外键约束"""

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def create_tables(self) -> None:
        """创建所有数据库表"""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """删除所有数据库表（谨慎使用）"""
        Base.metadata.drop_all(bind=self.engine)

    def reset_database(self) -> None:
        """重置数据库（删除并重新创建所有表）"""
        self.drop_tables()
        self.create_tables()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（上下文管理器）

        使用方式:
            with db.get_session() as session:
                session.add(player)
                session.commit()

        Yields:
            Session: 数据库会话
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session_instance(self) -> Session:
        """获取数据库会话实例（需要手动管理）

        Returns:
            Session: 数据库会话
        """
        return self.SessionLocal()


# 全局数据库实例
_db_instance: Database | None = None


def get_db() -> Database:
    """获取全局数据库实例

    Returns:
        Database: 数据库实例
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.create_tables()
    return _db_instance


def init_db(db_path: str | None = None) -> Database:
    """初始化数据库

    Args:
        db_path: 数据库文件路径

    Returns:
        Database: 数据库实例
    """
    global _db_instance
    _db_instance = Database(db_path)
    _db_instance.create_tables()
    return _db_instance


def close_db() -> None:
    """关闭数据库连接"""
    global _db_instance
    if _db_instance is not None:
        _db_instance.engine.dispose()
        _db_instance = None
