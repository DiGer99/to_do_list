from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def create_inline_keyboard(width: int, *args, **kwargs):
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    if kwargs:
        for callback, text in kwargs.items():
            buttons.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=callback
                )
            )
    kb_builder.row(width=width, *buttons)
    return kb_builder.as_markup()


def create_reply_keyboard(width, to_head=False, *args):
    kb_builder = ReplyKeyboardBuilder()
    buttons = []
    if args:
        for text in args:
            buttons.append(KeyboardButton(text=text))
    kb_builder.row(width=width, *buttons)
    if to_head:
        kb_builder.row(KeyboardButton(text='На главную'), width=1)
    return kb_builder.as_markup(resize_keyboard=True)