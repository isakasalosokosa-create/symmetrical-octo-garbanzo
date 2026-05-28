import asyncio
import logging
import uuid

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "7753201135:AAGsL9XqVxgf7V2N6y_m6NhVNAVjT3j3pPo"

ADMIN_IDS = [8147892171, 8508525339]  # Список администраторов

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ---------------- STATES ----------------

class OrderState(StatesGroup):
    waiting_id = State()


# Хранилище временных данных заявки (user_id -> данные)
pending_orders = {}


# ---------------- KEYBOARDS ----------------

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сопровождения ✅", callback_data="service_1"),
            InlineKeyboardButton(text="Веши 📦", callback_data="service_2")
        ],
        [
            InlineKeyboardButton(text="Буст балика 🔥", callback_data="service_3"),
            InlineKeyboardButton(text="Кламси 🌟", callback_data="service_4")
        ]
    ])


def managers_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Написать @Edla1n", url="https://t.me/Edla1n")
        ],
        [
            InlineKeyboardButton(text="Написать @Qwerty9998", url="https://t.me/Dream_while_you_ca0")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_menu")
        ]
    ])


def admin_kb(order_id):
    """Клавиатура для админа с привязкой к ID заявки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Принял в друзья", callback_data=f"admin_accept_{order_id}"),
            InlineKeyboardButton(text="Отказаться", callback_data=f"admin_decline_{order_id}")
        ]
    ])


# ---------------- START ----------------

@dp.message(CommandStart())
async def start(message: Message):
    photo = FSInputFile("start.jpg")

    caption = (
        f"👋 Здравствуй, {message.from_user.username}\n\n"
        "▸ Ты в боте AQRESSOR\n\n"
        "✦ Тут ты сможешь купить:\n\n"
        "▸ Сопровождение ✅\n"
        "▸ Веши 📦\n"
        "▸ Буст балика 🔥"
    )

    await message.answer_photo(
        photo=photo,
        caption=caption,
        reply_markup=main_menu()
    )


# ---------------- SERVICE SELECT ----------------

@dp.callback_query(F.data.startswith("service_"))
async def service(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderState.waiting_id)
    await state.update_data(service=call.data)

    await call.message.answer("🆔 Напиши свой айди чтобы мы могли пригласить вас в друзья")
    await call.answer()


# ---------------- ID CHECK ----------------

@dp.message(OrderState.waiting_id)
async def get_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Айди должен содержать только цифры\n\nПопробуй еще раз")
        return

    data = await state.get_data()
    service = data.get("service")
    user_id = message.from_user.id

    await state.clear()

    # USER MESSAGE
    await message.answer(
        "Отлично скоро мы добавим вас в друзья\n\n"
        "После того как добавим бот кинет сообщение для продолжения\n\n"
        "Также ты можешь обратиться к менеджерам:",
        reply_markup=managers_kb()
    )

    # Сохраняем временные данные заявки
    order_id = str(uuid.uuid4())[:8]
    pending_orders[order_id] = {
        "user_id": user_id,
        "username": message.from_user.username,
        "pubg_id": message.text,
        "service": service
    }

    # Рассылаем уведомления всем администраторам
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"Игрок кинул заявку на приглашение\n\n"
            f"Юзер: @{message.from_user.username}\n"
            f"Айди тг: {user_id}\n"
            f"Айди пабг: {message.text}\n"
            f"Услуга: {service}",
            reply_markup=admin_kb(order_id)
        )


# ---------------- ADMIN ACTIONS ----------------

@dp.callback_query(F.data.startswith("admin_accept_"))
async def admin_accept(call: CallbackQuery):
    order_id = call.data.split("_")[-1]
    order = pending_orders.get(order_id)

    if not order:
        await call.answer("Заявка уже обработана или не найдена", show_alert=True)
        return

    await call.message.edit_text(
        f"Отлично вы приняли в друзья открываю доступ игроку @{order['username']}"
    )

    # Отправляем сообщение игроку
    await bot.send_message(
        order["user_id"],
        "Админ принял заявку",
        reply_markup=managers_kb()
    )

    # Удаляем заявку из pending
    del pending_orders[order_id]

    await call.answer()


@dp.callback_query(F.data.startswith("admin_decline_"))
async def admin_decline(call: CallbackQuery):
    order_id = call.data.split("_")[-1]
    order = pending_orders.pop(order_id, None)

    await call.message.edit_text("❌ Заявка отклонена")
    await call.answer()


# ---------------- BACK BUTTON ----------------

@dp.callback_query(F.data == "back_menu")
async def back(call: CallbackQuery):
    photo = FSInputFile("start.jpg")

    caption = (
        f"👋 Здравствуй, {call.from_user.username}\n\n"
        "▸ Ты в боте AQRESSOR\n\n"
        "✦ Тут ты сможешь купить:\n\n"
        "▸ Сопровождение ✅\n"
        "▸ Веши 📦\n"
        "▸ Буст балика 🔥"
    )

    await call.message.answer_photo(
        photo=photo,
        caption=caption,
        reply_markup=main_menu()
    )

    await call.answer()


# ---------------- RUN ----------------

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
