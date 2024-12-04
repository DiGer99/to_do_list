from aiogram.fsm.state import State, StatesGroup


class WaitScheduleFSM(StatesGroup):
    wait_schedule = State()


class WaitEditScheduleButton(StatesGroup):
    wait_button = State()


class WaitAddRowIntoSchedule(StatesGroup):
    wait_row = State()


class WaitAddSampleSchedule(StatesGroup):
    wait_sample = State()


class WaitAddToDoList(StatesGroup):
    wait_to_do_list = State()


class WaitAddOneAction(StatesGroup):
    wait_one_action = State()