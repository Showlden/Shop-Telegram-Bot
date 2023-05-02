'''Подключение'''
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Command
from aiogram.types import InputMediaPhoto, Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv
import config
from db import Database

load_dotenv()
storage = MemoryStorage()
bot = Bot(str(os.getenv("TOKEN")))
dp = Dispatcher(bot, storage=storage)
db = Database("items.db")

class ItemStatesGroup(StatesGroup):
	photo = State()
	name = State()
	price = State()

'''Старт'''

@dp.message_handler(commands=["start", "menu"])
async def menu(message: Message, check=None):
	menu = types.InlineKeyboardMarkup(row_width=1)
	catalog = types.InlineKeyboardButton(text="Каталог", callback_data="catalog")
	reviews = types.InlineKeyboardButton(text="Отзывы", callback_data="reviews")
	menu.add(catalog, reviews)
	if message.chat.id == int(os.getenv("ADMIN_ID")):
		menu.add(types.InlineKeyboardButton(text="Админ панель", callback_data="admin"))
	if check == None:
		await message.answer(text="Выберите раздел:", reply_markup=menu)
	else:
	 	await message.edit_text(text="Выберите раздел:", reply_markup=menu)

'''Каталог'''

@dp.message_handler(Command("catalog"))
async def catalog(message: Message):
	await GetCard(message)

SelectedCardID = 1
async def GetCard(message, edit=None):
	board = types.InlineKeyboardMarkup()
	backcard = types.InlineKeyboardButton(text="<===", callback_data="back")
	nextcard = types.InlineKeyboardButton(text="===>", callback_data="next")
	if SelectedCardID == 1:
		board.add(nextcard)
	elif SelectedCardID == db.get_len_items():
		board.add(backcard)
	else:
		board.add(backcard, nextcard)

	data = db.get_item(item_id=SelectedCardID)
	if data is None:
		await message.answer("Список пуст")
	else:
		data = list(data)
		if edit == None:
			await bot.send_photo(chat_id=message.chat.id, 
					photo=data[1], 
					caption=f"""<b>Название:</b>: {data[2]} \n<b>Цена:</b> {data[3]}""", 
					reply_markup=board,
					parse_mode="html")	
		else:
			await bot.edit_message_media(chat_id=message.chat.id, 
										message_id=message.message_id, 
										media=InputMediaPhoto(media=data[1]))
			await bot.edit_message_caption(chat_id=message.chat.id, 
		                                message_id=message.message_id, 
		                                caption=f"""<b>Название:</b>: {data[2]} \n<b>Цена:</b> {data[3]}""",
		                                parse_mode="html",
		                                reply_markup=board)


'''Админ панель'''

def get_cancel_kb():
	kb = InlineKeyboardMarkup(resize_keyboard=True)
	kb.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
	return kb

async def cancel(message: Message, state: FSMContext):
	menu = InlineKeyboardMarkup(row_width=1)
	catalog = InlineKeyboardButton(text="Каталог", callback_data="catalog")
	reviews = InlineKeyboardButton(text="Отзывы", callback_data="reviews")
	menu.add(catalog, reviews)
	if message.chat.id == config.ADMIN_ID:
		menu.add(InlineKeyboardButton(text="Админ панель", callback_data="admin"))
	await state.finish()
	await message.reply('Вы прервали добавление товара!', reply_markup=menu)

async def admin(message: Message):
	admin_menu = InlineKeyboardMarkup(row_width=1)
	add_btn = InlineKeyboardButton("Добавить товар", callback_data="add")
	edit_btn = InlineKeyboardButton("Редактировать товар", callback_data="edit")
	main_menu_btn = InlineKeyboardButton("Главное меню", callback_data="main_menu")
	admin_menu.add(add_btn, edit_btn, main_menu_btn)
	await message.edit_text("Админ панель:", reply_markup=admin_menu)

async def add(message: Message):
	await message.answer("Пришлите фото товара", reply_markup=get_cancel_kb())
	await ItemStatesGroup.photo.set()

@dp.message_handler(lambda message: not message.photo, state=ItemStatesGroup.photo)
async def check_photo(message: Message):
	await message.reply("Это не фото")

@dp.message_handler(content_types=["photo"], state=ItemStatesGroup.photo)
async def load_photo(message: Message, state: FSMContext):
	async with state.proxy() as data:
		data['photo'] = message.photo[0].file_id

	await message.reply("Введите название товара", reply_markup=get_cancel_kb())
	await ItemStatesGroup.next()

@dp.message_handler(state=ItemStatesGroup.name)
async def load_name(message: Message, state: FSMContext):
	async with state.proxy() as data:
		data['name'] = message.text

	await message.reply("Введите цену товара", reply_markup=get_cancel_kb())
	await ItemStatesGroup.next()

@dp.message_handler(state=ItemStatesGroup.price)
async def load_price(message: Message, state: FSMContext):
	async with state.proxy() as data:
		data['price'] = message.text
		await bot.send_photo(chat_id=message.chat.id, 
			photo=data['photo'], 
			caption=f"""<b>Название:</b>: {data['name']} \n<b>Цена:</b> {data['price']}""", 
			parse_mode="html")

	db.set_item(
		photo_id=data['photo'],
		name=data['name'],
		price=data['price'])
	await message.reply("Товар успешно добавлен")
	await state.finish()

'''Обработчик callback запросов'''

@dp.callback_query_handler(lambda call: True, state='*')
async def callback_worker(call: CallbackQuery, state: FSMContext):
	if call.data == "catalog":
		await GetCard(call.message, "edit")
	if call.data == "admin":
		await admin(call.message)
	if call.data == "cancel":
		await cancel(call.message, state)
	if call.data == "add":
		await add(call.message)
	if call.data == "edit":
		await call.message("Данная фукнция пока-что не работает")
	if call.data == "main_menu":
		await menu(call.message, "edit")
	global SelectedCardID
	if call.data == "back":
		if SelectedCardID == 1:
			await GetCard(call.message, "edit")
		SelectedCardID -= 1
		await GetCard(call.message, "edit")
	if call.data == "next":
		SelectedCardID += 1
		await GetCard(call.message, "edit")

'''Запуск бота'''

if __name__ == "__main__":
	executor.start_polling(dp)


