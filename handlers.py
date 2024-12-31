import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
import database.requests as rq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from fsm.fsm import (WaitScheduleFSM, WaitEditScheduleButton, WaitAddRowIntoSchedule, WaitAddSampleSchedule,
                     WaitAddToDoList, WaitAddOneAction)
from keyboards.keyboards import create_inline_keyboard, create_reply_keyboard
from services.services import check_dash_in_time


router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def process_command_start(message: Message):
        await rq.set_user(message.from_user.id, f'{message.from_user.first_name} {message.from_user.last_name}')
        await message.answer(text='Здравствуйте!\n'
                                  'Помогу составить расписание.\n'
                                  'О том как работать с функциями бота - нажмите команду /help')


@router.message(Command(commands='help'))
async def process_remind_command(message: Message, bot: Bot):
    await message.answer(text='Веберите с чем хотите работать:\n\n'
                              '<b>Расписание</b> - это работа с расписанием - пишите время и дело, '
                              'которое хотите спланировать на это время.\n\n'
                              '<b>Шаблоны</b> существуют, чтобы не прописывать одно и тоже расписание каждый день, '
                              'если оно одинаковое или похоже.\n\n'
                              '<b>Список дел</b> - это дела которые не привязаны к определенному времени,'
                              'также можно туда вписать список покупок и тд.\n\n',
                         reply_markup=create_reply_keyboard(2, False, 'Расписание', 'Шаблоны',
                                                            'Список дел'))

    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@router.message(F.text == 'На главную')
async def process_to_head_reply_button_press(message: Message, state: FSMContext):
    if state:
        await state.clear()
    await message.answer(text='Вы перешли на главную страницу!\n\n'
                                 'Для справки - нажмите на команду /help',
                            reply_markup=create_reply_keyboard(2, False, 'Расписание', 'Шаблоны',
                                                               'Список дел'))


# Блок работы с раписанием
# обработка reply кнопки "Распиание"
@router.message(F.text == 'Расписание')
async def process_schedule_reply_button_press(message: Message):
    await message.answer(text='Выберите действие с расписанием.\n\n'
                              'Для справки - нажмите на команду /help',
                         reply_markup=create_reply_keyboard(2, True,
                                                            'Новое расписание', 'Редактировать расписание',
                                                            'Показать расписание', 'Добавить в расписание',
                                                            'Загрузить шаблон в расписание'))


@router.message(F.text == 'Новое расписание')
async def process_new_schedule_press(message: Message, state: FSMContext):
    await message.answer(text='Отправьте расписание списком и я выведу его в сообщении кнопками.\n'
                              'При нажатии на кнопку с назначенным делом на день - оно '
                              'будет удаляться, сигнализируя о выполнение!\n\n'
                              'Отправьте свое расписание, например: \n'
                              '7:30 Подъем\n'
                              '8:00 Завтрак\n'
                              '10:30 Выйти из дома\n'
                              '11:00 Сесть в машину\n'
                              '...')
    await state.set_state(WaitScheduleFSM.wait_schedule)


# Вывод кнопки "Расписание" для вывода инлайн-клавиатуры с расписанием
@router.message(F.text.split(' ', 1)[0].replace(':', '').isdigit(), StateFilter(WaitScheduleFSM.wait_schedule))
async def process_wait_schedule(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await rq.update_schedule(message.from_user.id, message.text)
    await message.answer(text='Для получения расписание нажмите кнопку "Расписание"',
                         reply_markup=create_inline_keyboard(1, schedule='Расписание'))
    await state.clear()


# Колбэк на кнопку "Расписание" и вывод расписания инлайн клавиатурой
@router.callback_query(F.data == 'schedule')
async def process_callback_schedule(callback: CallbackQuery):
    schedule = await rq.get_schedule(callback.from_user.id)
    rows = schedule.split('\n')
    buttons = {f'schedule_{i.split(' ', 1)[0]}': f'{i.split(' ', 1)[0]} - {i.split(' ', 1)[1]}' for i in rows}
    await callback.message.edit_text(text='Ваше расписание: ',
                                  reply_markup=create_inline_keyboard(width=1,
                                                                      **buttons))
    await callback.answer()


@router.message(F.text == 'Показать расписание')
async def process_get_schedule_reply_keyboard(message: Message):
    schedule = await rq.get_schedule(message.from_user.id)
    rows = schedule.split('\n')
    buttons = {f'schedule_{i.split(' ', 1)[0]}': f'{i.split(' ', 1)[0]} - {i.split(' ', 1)[1]}' for i in rows}
    await message.answer(text='Ваше расписание: ',
                                     reply_markup=create_inline_keyboard(width=1,
                                                                         **buttons))


@router.message(F.text == 'Добавить в расписание')
async def process_wait_row_to_add_into_schedule(message: Message, state: FSMContext):
    await message.answer(text='Введите время и описание в формате "13:30 Обед"')
    await state.set_state(WaitAddRowIntoSchedule.wait_row)


# Проверка на то, что первые символы - время, и фильтр состояния -- добавление новой строки расписания --
# Сортировка по времени -- полученние кнопок расписания
@router.message(F.text.split(' ', 1)[0].replace(':', '').isdigit(), StateFilter(WaitAddRowIntoSchedule.wait_row))
async def process_add_row_into_schedule(message: Message, state: FSMContext):
    schedule: str = await rq.get_schedule(message.from_user.id)
    schedule += '\n' + message.text
    rows: list = schedule.split('\n')
    if await check_dash_in_time(rows=rows): # проверка что "-" находится в интервале времени или нет 
        dashes = [] # если да, то создаем новый список, добавляем туда время с тире, сортируем по времени без тире и потом отдельно
        # добавляем время с тире в rows
        for i in rows:
            if "-" in i:
                dashes.append(rows.pop(rows.index(i))) # вынимаем в пустой список время с тире
        rows.sort(key=lambda x: int(x.split(' ', 1)[0].replace(':', ''))) # сортируем время без тире
        for i in dashes:
            for j in rows:
                if i.split("-", 1)[0] < j.split(" ", 1)[0]:
                    rows.insert(rows.index(j), i) # вставляем время с тире перед временем без тире
    else:
        rows.sort(key=lambda x: int(x.split(' ', 1)[0].replace(':', '')))
    await rq.update_schedule(message.from_user.id, '\n'.join(rows))
    buttons = {f'schedule_{i.split(' ', 1)[0]}': f'{i.split(' ', 1)[0]} - {i.split(' ', 1)[1]}' for i in rows}
    await state.clear()
    await message.answer(text='Ваше расписание:', reply_markup=create_inline_keyboard(1, **buttons))


# Удаление нажатой инлайн кнопки в расписании и обновление расписания в БД
@router.callback_query(F.data.startswith('schedule_'))
async def process_callback_press_schedule_button(callback: CallbackQuery):
    schedule = await rq.get_schedule(callback.from_user.id)
    rows = schedule.split('\n')
    indx = None
    for row in rows:
        if callback.data.removeprefix('schedule_') == row.split(' ', 1)[0]:
            indx = rows.index(row)
            break
    rows.pop(indx)
    new_schedule = '\n'.join(rows)
    await rq.update_schedule(callback.from_user.id, new_schedule)
    buttons = {f'schedule_{i.split(' ')[0]}': f'{i.split(' ', 1)[0]} - {i.split(' ', 1)[1]}' for i in rows}
    await callback.message.edit_text(text='Ваше расписание: ',
                                     reply_markup=create_inline_keyboard(width=1,
                                                                         **buttons))


# Загрузка шаблона в расписание по реплай кнопки из разделов "Расписание" и "Шаблоны"
@router.message(F.text == 'Загрузить шаблон в расписание')
async def process_load_sample_to_schedule(message: Message):
    sample = await rq.get_full_sample_schedule(message.from_user.id)
    await rq.update_schedule(message.from_user.id, sample)
    await message.answer(text='Шаблон загружен в расписание!')


# Редактирование расписания
@router.message(F.text == 'Редактировать расписание')
async def process_edit_schedule(message: Message):
    schedule = await rq.get_schedule(message.from_user.id)
    rows = schedule.split('\n')
    buttons = {f'edit_schedule_{i.split(' ', 1)[0]}': f'🔄 {i.split(' ', 1)[0]} - {i.split(' ', 1)[1]}' for i in rows}
    buttons.update({'schedule_cancel': '❌ Отмена'})
    await message.answer(text='Нажмите на кнопку вашего расписание, которую хотите изменить...',
                         reply_markup=create_inline_keyboard(width=1, **buttons))


# Нажатие на кнопку "Отмена" при редактировании расписания
@router.callback_query(F.data == 'schedule_cancel')
async def cancel_process_edit_schedule(callback: CallbackQuery):
    schedule = await rq.get_schedule(callback.from_user.id)
    rows = schedule.split('\n')
    buttons = {f'schedule_{i.split(' ', 1)[0]}': f'{i.split(' ', 1)[0]} - {i.split(' ', 1)[1]}' for i in rows}
    await callback.message.edit_text(text='Ваше расписание: ',
                                     reply_markup=create_inline_keyboard(width=1,
                                                                         **buttons))
    await callback.answer()


# Колбэк на редактирование расписания
# Заменяем оптсание запланированного дела на Null
@router.callback_query(F.data.startswith('edit_schedule_'))
async def process_edit_button_wait_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите текст, на который хотите заменить...')
    schedule = await rq.get_schedule(callback.from_user.id)
    rows = schedule.split('\n')
    pressed_button = callback.data.removeprefix('edit_schedule_')
    for row in rows:
        if pressed_button == row.split(' ', 1)[0]:
            rows[rows.index(row)] = f'{row.split(' ', 1)[0]} Null'
            break

    await rq.update_schedule(callback.from_user.id, '\n'.join(rows))
    await state.set_state(WaitEditScheduleButton.wait_button)
    await callback.answer()


# Ищем Null в описании и заменяем на новый текст
@router.message(StateFilter(WaitEditScheduleButton.wait_button))
async def edit_text_button(message: Message, state: FSMContext):
    schedule = await rq.get_schedule(message.from_user.id)
    rows = schedule.split('\n')
    for row in rows:
        if row.endswith('Null'):
            rows[rows.index(row)] = f'{row.split(' ', 1)[0]} {message.text}'
            break

    new_schedule = '\n'.join(rows)
    await rq.update_schedule(message.from_user.id, new_schedule)
    buttons = {f'schedule_{i.split(' ')[0]}': f'{i.split(' ', 1)[0]} - {i.split(' ', 1)[1]}' for i in rows}
    await message.answer(text='Ваше расписание: ',
                                     reply_markup=create_inline_keyboard(width=1,
                                                                         **buttons))
    await state.clear()


# Блок работы с шаблонами !!!!!!
# Реакция на кнопку "Шаблоны" -- генерация клавиатуры для работы с ними
@router.message(F.text == 'Шаблоны')
async def process_reply_button_samples_press(message: Message):
    await message.answer(text='Выберите действие с шаблонами.\n\n'
                              'Для справки - нажмите на команду /help',
                         reply_markup=create_reply_keyboard(2, True,
                                                            'Добавить шаблон', 'Показать шаблон',
                                                            'Загрузить шаблон в расписание'))


# Обработки кнопки "Добавить шаблон"
@router.message(F.text == 'Добавить шаблон')
async def process_add_sample_schedule(message: Message, state: FSMContext):
    await message.answer(text='Отправьте шаблон в формате, указанном ниже и я сохраню его:\n'
                              '7:30 Подъем\n'
                              '8:00 Завтрак\n'
                              '10:30 Выйти из дома\n'
                              '11:00 Сесть в машину\n'
                              '...')
    await state.set_state(WaitAddSampleSchedule.wait_sample)


# Загрузили новый шаблон в БД
@router.message(F.text.split(' ', 1)[0].replace(':', '').isdigit(), StateFilter(WaitAddSampleSchedule.wait_sample))
async def process_update_sample_schedule(message: Message, state: FSMContext):
    await rq.update_sample_schedule(message.from_user.id, message.text)
    await message.answer(text='Шаблон добавлен')
    await state.clear()


# Не верно введенный шаблон
@router.message(StateFilter(WaitScheduleFSM.wait_schedule))
async def process_wrong_schedule_from_user(message: Message):
    await message.answer(text='Не верно введенные данные!')


# Выводим шаблон из БД текстом в сообщении
@router.message(F.text == 'Показать шаблон')
async def process_previous_full_schedule(message: Message):
    schedule = await rq.get_full_sample_schedule(message.from_user.id)
    await message.answer(text=schedule)


# Блок работы со списками дел !!!!!!!
@router.message(F.text == 'Список дел')
async def process_to_do_list_press(message: Message):
    await message.answer(text='Работа со списками дел или покупок...\n\n'
                              'Для справки - нажмите на команду /help',
                         reply_markup=create_reply_keyboard(2, True, 'Создать список дел',
                                                            'Показать список дел', 'Добавить дело'))

# обработка реплай кнопки "Добавить дело"
@router.message(F.text == 'Добавить дело')
async def process_add_action_reply_button_press(message: Message, state: FSMContext):
    await message.answer(text='Напишите какое дело хотите добавить в список...')
    await state.set_state(WaitAddOneAction.wait_one_action)


# добавляем отдельное дело в список дел
@router.message(StateFilter(WaitAddOneAction.wait_one_action))
async def process_add_into_to_do_list(message: Message, state: FSMContext):
    to_do_list = await rq.get_to_do_list(message.from_user.id)
    rows = to_do_list.split('\n')
    messages_rows = message.text.split('\n')
    rows += messages_rows
    await rq.update_to_do_list(message.from_user.id, '\n'.join(rows))
    await state.clear()
    await message.answer(text='Дело добавлено!')


# Добавление списка дел в БД
@router.message(F.text == 'Создать список дел')
async def process_press_create_to_do_list_reply_button(message: Message, state: FSMContext):
    await message.answer(text='Напишите список в формате:\n\n'
                              'Купить молоко\n'
                              'Полить цветы\n'
                              'Зарядить телефон\n'
                              '...')
    await state.set_state(WaitAddToDoList.wait_to_do_list)


# Ожидания списка покупок, фильтрация по "\n"
@router.message(StateFilter(WaitAddToDoList.wait_to_do_list))
async def process_add_to_do_list(message: Message, state: FSMContext):
    await rq.update_to_do_list(message.from_user.id, message.text)
    await message.answer(text='Список добавлен!\n'
                              'Для просмотра нажмите на кнопку "Показать список"')
    await state.clear()


@router.message(StateFilter(WaitAddToDoList.wait_to_do_list))
async def process_wrong_to_do_list_from_user(message: Message):
    await message.answer(text='Неверный формат, в конце строки должен быть перенос на следующую строку!\n'
                              'Попробуйте ввести заново')


# Вывод списка из БД
@router.message(F.text == 'Показать список дел')
async def process_get_to_do_list(message: Message):
    to_do_list = await rq.get_to_do_list(message.from_user.id)
    rows = to_do_list.split('\n')
    buttons = {f'to_do_list_{rows.index(i)}': i for i in rows}
    await message.answer(text='Ваш список:',
                         reply_markup=create_inline_keyboard(1, **buttons))


# Удаляем инлайн кнопку при нажатиии при выполнении какого то дела
@router.callback_query(F.data.startswith('to_do_list_'))
async def process_press_to_do_list_button(callback: CallbackQuery):
    to_do_list = await rq.get_to_do_list(callback.from_user.id)
    rows = to_do_list.split('\n')
    for row in rows:
        if str(rows.index(row)) == callback.data.removeprefix('to_do_list_'):
            rows.pop(rows.index(row))
            break
    buttons = {f'to_do_list_{rows.index(i)}': i for i in rows}
    await callback.message.edit_text(text='Ваш список:',
                                     reply_markup=create_inline_keyboard(1, **buttons))
    await rq.update_to_do_list(callback.from_user.id, '\n'.join(rows))


@router.message()
async def process_any_message(message: Message):
    await message.answer(text='Для справки нажмите на команду /help')