from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import BigInteger, String

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    full_name: Mapped[str] = mapped_column(String(30))
    schedule: Mapped[str] = mapped_column(String(355), default='')
    sample_schedule: Mapped[str] = mapped_column(String(355), default='')
    to_do_list: Mapped[str] = mapped_column(String(355), default='')

async def db_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)