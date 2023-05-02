from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from bot import bot, dp
import config 

class ItemStatesGroup(StatesGroup):
	photo = State()
	name = State()
	price = State()

def get_cancel_kb():
	kb = ReplyKeyboardMarkup(row_width=1)
	kb.add(KeyboardButton("Отмена"))
	return kb

async def admin(message: Message):
	admin_menu = InlineKeyboardMarkup(row_width=1)
	add_btn = InlineKeyboardButton("Добавить товар", callback_data="add")
	edit_btn = InlineKeyboardButton("Редактировать товар", callback_data="edit")
	admin_menu.add(add_btn, edit_btn)
	await message.answer("Админ панель:", reply_markup=admin_menu)


async def cancel(message: Message, state: FSMContext):
	menu = InlineKeyboardMarkup(row_width=1)
	catalog = InlineKeyboardButton(text="Каталог", callback_data="catalog")
	reviews = InlineKeyboardButton(text="Отзывы", callback_data="reviews")
	menu.add(catalog, reviews)
	if message.chat.id == config.ADMIN_ID:
		menu.add(InlineKeyboardButton(text="Админ панель", callback_data="admin"))
	await state.finish()
	await message.reply('Вы прервали добавление товара!', reply_markup=menu)

async def add(message: Message):
	await message.answer("Пришлите фото товара", reply_markup=get_cancel_kb())
	await ItemStatesGroup.photo.set()

@dp.message_handler(content_types=["photo"], state=ItemStatesGroup.photo)
async def load_photo(message: Message, state: FSMContext):
	if not message.photo:
		await message.reply("Это не фото")
	else:
		async with state.proxy() as data:
			data['photo'] = message.photo[0].file_id

		await message.reply("Введите название товара")
		await ItemStatesGroup.next()

@dp.message_handler(state=ItemStatesGroup.name)
async def load_name(message: Message, state: FSMContext):
	async with state.proxy() as data:
		data['name'] = message.text

	await message.reply("Введите цену товара")
	await ItemStatesGroup.next()

@dp.message_handler(state=ItemStatesGroup.price)
async def load_name(message: Message, state: FSMContext):
	async with state.proxy() as data:
		await bot.send_photo(chat_id, message.chat.id, photo=data['photo'], caption=f"""
																			<b>Название:</b>: {data['name']}
																			<b>Цена:</b> {data['price']}
																				""")

	await message.reply("Товар успешно добавлен")
	await state.finish
