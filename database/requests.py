from database.models import async_session
from database.models import User
from sqlalchemy import select, update


def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return inner


# добваление пользователя в расписание при нажатии на команду start
@connection
async def set_user(session, tg_id, full_name):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))

    if not user:
        session.add(User(tg_id=tg_id, full_name=full_name))
        await session.commit()


# обновление расписания
@connection
async def update_schedule(session, tg_id, schedule):
    await session.execute(update(User).where(User.tg_id == tg_id).values(schedule=schedule))
    await session.commit()


# обновление шаблонов для расписания
@connection
async def update_sample_schedule(session, tg_id, schedule):
    await session.execute(update(User).where(User.tg_id == tg_id).values(sample_schedule=schedule))
    await session.commit()

@connection
# получение шаблона расписания из БД
async def get_full_sample_schedule(session, tg_id):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    return user.sample_schedule


# получение расписание из БД
@connection
async def get_schedule(session, tg_id):
    schedule = await session.scalar(select(User).where(User.tg_id == tg_id))
    return schedule.schedule


# обновление to_do_list
@connection
async def update_to_do_list(session, tg_id, to_do_list):
    await session.execute(update(User).where(User.tg_id == tg_id).values(to_do_list=to_do_list))
    await session.commit()


# получение to_do_list из БД
@connection
async def get_to_do_list(session, tg_id):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    return user.to_do_list
