from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)
API_ID: int
API_HASH: str


SLEEP_TIME: list[int] = [3600, 7200]
START_DELAY: list[int] = [5, 25]


AUTO_TASK: bool = True
AUTO_MINING: bool = True
AUTO_BUY_MINE: bool = True
AUTO_UPGRADEL: bool = True
CLAIM_DAILY_REWARDS: bool = True
UPGRADE_MINE: bool = True
UPGRADE_MINERS: bool = True
UPGRADE_INVENTORY: bool = True
UPGRADE_CART: bool = True
MAX_CART_LEVEL: int
EXPEDITIONSL: bool = True
CUSTOM_EXPEDITION_COST: list[int]
NIGHT_MODE: bool = True


JOIN_TG_CHANNELS: bool = False
USE_REF: bool = True
REF_ID: str = '77513450415'


settings = Settings()
