from environs import Env
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Tgbot:
    token: str


@dataclass
class Database:
    db_name: str
    db_user: str
    db_password: str
    host: str
    port: int


@dataclass
class AdminIDS:
    lst_ids: list


@dataclass
class Config:
    tg_bot: Tgbot
    db: Database
    ids: AdminIDS


def load_config(path: None | str = None) -> Config:
    logger.debug('load config func')
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=Tgbot(token=env('TOKEN')),
        db=Database(
            db_name=env('DB_NAME'),
            db_user=env('DB_USER'),
            db_password=env('DB_PASSWORD'),
            host=env('DB_HOST'),
            port=env('DB_PORT')
        ),
        ids=AdminIDS(env('IDS'))
    )

