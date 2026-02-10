"""应用配置"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用信息
    APP_NAME: str = "Happy Vibe Hub"
    VERSION: str = "0.1.0"

    # 服务配置
    HOST: str = "127.0.0.1"
    PORT: int = 8765
    DEBUG: bool = True

    # 数据存储
    DATA_DIR: str = "./data"
    DATABASE_PATH: str = "./data/vibehub.db"

    # Vibe 能量配置
    BASE_ENERGY_RATE: int = 10  # 每分钟基础能量
    MAX_ENERGY_MULTIPLIER: float = 2.0  # 最大时间加成
    MAX_QUALITY_MULTIPLIER: float = 1.5  # 最大质量加成
    FLOW_STATE_MULTIPLIER: float = 1.5  # 心流状态加成

    # 心流检测配置
    FLOW_MIN_DURATION: int = 45  # 最小编码时长(分钟)
    FLOW_MAX_GAP: int = 300  # 最大交互间隔(秒)
    FLOW_MIN_SUCCESS_RATE: float = 0.8  # 最低成功率

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
