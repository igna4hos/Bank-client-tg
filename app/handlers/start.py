from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from app.api_client import backend

router = Router()

DEPARTMENTS = [
    "Manager",
    "Business Analyst",
    "System Analyst",
    "UI/UX",
    "Web Developer",
    "Mobile Developer",
    "DevOps",
    "QA",
]

_DEPT_MAP = {str(i + 1): d for i, d in enumerate(DEPARTMENTS)}
_DEPT_LIST = "\n".join(f"{i + 1}. {d}" for i, d in enumerate(DEPARTMENTS))


class Reg(StatesGroup):
    choosing = State()
    custom = State()


def _dept_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"),
             KeyboardButton(text="3"), KeyboardButton(text="4")],
            [KeyboardButton(text="5"), KeyboardButton(text="6"),
             KeyboardButton(text="7"), KeyboardButton(text="8")],
            [KeyboardButton(text="Другой")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _get_nick(message: Message) -> str:
    return message.from_user.username or str(message.from_user.id)


def _get_first_name(message: Message) -> str:
    return message.from_user.first_name


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    nick = _get_nick(message)
    name = _get_first_name(message)
    user = await backend.get_user(nick)

    if user:
        await message.answer(f"С возвращением, {name}! 👋")
        return

    await message.answer(
        f"Привет, {name}! 👋\n\nДобро пожаловать! Выбери свой департамент "
        f"(введи цифру) или нажми «Другой»:\n\n{_DEPT_LIST}",
        reply_markup=_dept_keyboard(),
    )
    await state.set_state(Reg.choosing)


@router.message(Reg.choosing)
async def choose_dept(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "Другой":
        await message.answer(
            "Введи название своего департамента:",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(Reg.custom)
        return

    department = _DEPT_MAP.get(text, text)
    await _register(message, state, department)


@router.message(Reg.custom)
async def enter_custom_dept(message: Message, state: FSMContext):
    await _register(message, state, message.text.strip())


async def _register(message: Message, state: FSMContext, department: str) -> None:
    nick = _get_nick(message)
    await backend.create_user(nick, message.chat.id, department)
    await state.clear()
    await message.answer(
        f"Готово! Ты зарегистрирован как @{nick}\n"
        f"Департамент: *{department}*\n"
        f"Роль: manager",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
