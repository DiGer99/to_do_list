from database.models import async_session
from database.models import User
from sqlalchemy import select, update


# добваление пользователя в расписание при нажатии на команду start
async def set_user(tg_id, full_name):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id, full_name=full_name))
            await session.commit()


# обновление расписания
async def update_schedule(tg_id, schedule):
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(schedule=schedule))
        await session.commit()


# обновление шаблонов для расписания
async def update_sample_schedule(tg_id, schedule):
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(sample_schedule=schedule))
        await session.commit()


# получение шаблона расписания из БД
async def get_full_sample_schedule(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user.sample_schedule


# получение расписание из БД
async def get_schedule(tg_id):
    async with async_session() as session:
        schedule = await session.scalar(select(User).where(User.tg_id == tg_id))
        return schedule.schedule


# обновление to_do_list
async def update_to_do_list(tg_id, to_do_list):
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(to_do_list=to_do_list))
        await session.commit()


# получение to_do_list из БД
async def get_to_do_list(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user.to_do_list
