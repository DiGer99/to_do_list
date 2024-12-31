from config import load_config, Config
from aiogram import Dispatcher, Bot, F
from database.models import db_main
import asyncio
from handlers import router
import logging
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties


logger = logging.getLogger(__name__)


async def main():
    await db_main()
    config: Config = load_config()
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)-8s %(filename)s'
                                                    '%(lineno)d %(name)s %(message)s')

    bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')