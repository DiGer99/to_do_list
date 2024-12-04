from aiogram.filters import BaseFilter
from aiogram.types import Message


class ScheduleFilter(BaseFilter):
    async def __call__(self, message: Message):
        message_split = message.text.split('-')
        if ':' in message_split[0].strip():
            return message_split[0].replace(':', '').isdigit()
        elif '-' in message_split[0].strip():
            return message_split[0].replace('-', '').isdigit()
