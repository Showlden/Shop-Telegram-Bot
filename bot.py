'''Подключение'''
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Command
from aiogram.types import InputMediaPhoto, Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import os
from dotenv import load_dotenv
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
	desc = State()
	edit_photo = State()
	edit_name = State()
	edit_price = State()
	edit_desc = State()

'''Старт'''

@dp.message_handler(commands=["start", "menu"])
async def menu(message: Message, edit=None):
	menu = types.InlineKeyboardMarkup(row_width=1)
	catalog = types.InlineKeyboardButton(text="Каталог", callback_data="catalog1")
	reviews = types.InlineKeyboardButton(text="Отзывы", callback_data="reviews")
	menu.add(catalog, reviews)
	if message.chat.id == int(os.getenv("ADMIN_ID")):
		menu.add(types.InlineKeyboardButton(text="Админ панель", callback_data="admin"))
	if not edit:
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
		if not edit:
			if db.get_len_items() != 1:
				await bot.send_photo(chat_id=message.chat.id, 
						photo=data[1], 
						caption=f"""<b>Название:</b>: {data[2]} \n<b>Цена:</b> {data[3]} \n<b>Описание</b>: {data[4]}""", 
						reply_markup=board,
						parse_mode="html")	
			else:
				await bot.send_photo(chat_id=message.chat.id, 
						photo=data[1], 
						caption=f"""<b>Название:</b>: {data[2]} \n<b>Цена:</b> {data[3]} \n<b>Описание</b>: {data[4]}""", 
						parse_mode="html")	
		else:
			await bot.edit_message_media(chat_id=message.chat.id, 
										message_id=message.message_id, 
										media=InputMediaPhoto(media=data[1]))
			await bot.edit_message_caption(chat_id=message.chat.id, 
		                                message_id=message.message_id, 
		                                caption=f"""<b>Название:</b>: {data[2]} \n<b>Цена:</b> {data[3]} \n<b>Описание</b>: {data[4]}""",
		                                parse_mode="html",
		                                reply_markup=board)


'''Добавление товара'''

def get_cancel_kb():
	kb = ReplyKeyboardMarkup(resize_keyboard=True)
	kb.add(KeyboardButton(".Отмена", callback_data="cancel"))
	return kb

@dp.message_handler(Command(commands=["Отмена"], prefixes="."), state='*')
async def cancel(message: Message, state: FSMContext):
	if message.chat.id == int(os.getenv("ADMIN_ID")):
		cancel_msg = await message.answer("Отмена...", reply_markup=ReplyKeyboardRemove())
		await cancel_msg.delete()
		admin_menu = InlineKeyboardMarkup(row_width=1)
		add_btn = InlineKeyboardButton("Добавить товар", callback_data="add")
		edit_btn = InlineKeyboardButton("Редактировать товаров", callback_data="edit")
		main_menu_btn = InlineKeyboardButton("Главное меню", callback_data="main_menu")
		admin_menu.add(add_btn, edit_btn, main_menu_btn)
		await state.finish()
		await message.answer('Действие прервано!', reply_markup=admin_menu)
	else:
		await message.reply("Эта команда доступа только админам")

async def admin(message: Message):
	admin_menu = InlineKeyboardMarkup(row_width=1)
	add_btn = InlineKeyboardButton("Добавить товар", callback_data="add")
	edit_btn = InlineKeyboardButton("Редактировать товаров", callback_data="edit")
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

	await message.reply("Введите описание товара", reply_markup=get_cancel_kb())
	await ItemStatesGroup.next()

@dp.message_handler(state=ItemStatesGroup.desc)
async def load_desc(message: Message, state: FSMContext):
	async with state.proxy() as data:
		data["desc"] = message.text
		await bot.send_photo(chat_id=message.chat.id, 
			photo=data['photo'], 
			caption=f"""<b>Название:</b>: {data['name']} \n<b>Цена</b>: {data['price']} \n<b>Описание</b>: {data['desc']}""", 
			parse_mode="html",
			reply_markup=ReplyKeyboardRemove())

	db.set_item(
		photo_id=data['photo'],
		name=data['name'],
		price=data['price'],
		desc=data["desc"])
	await message.reply("Товар успешно добавлен")
	await state.finish()

'''Редактирование товара'''

SelectedCardIDEdit = 1
async def editing(message: Message, edit=None):
	edit_menu = InlineKeyboardMarkup(row_width=4)
	edit_photo = InlineKeyboardButton("Фото", callback_data="edit_photo")
	edit_name = InlineKeyboardButton("Название", callback_data="edit_name")
	edit_price = InlineKeyboardButton("Цена", callback_data="edit_price")
	edit_desc = InlineKeyboardButton("Описание", callback_data="edit_desc")
	delete = InlineKeyboardButton("Удалить", callback_data="delete")
	backcard = types.InlineKeyboardButton(text="<===", callback_data="backEdit")
	nextcard = types.InlineKeyboardButton(text="===>", callback_data="nextEdit")

	edit_menu.add(edit_photo, edit_name, edit_price, edit_desc, delete)
	if db.get_len_items() == 1:
		pass
	elif SelectedCardIDEdit == 1:
		edit_menu.add(nextcard)
	elif SelectedCardIDEdit == db.get_len_items():
		edit_menu.add(backcard)
	else:
		edit_menu.add(backcard, nextcard)

	for button in edit_menu.inline_keyboard:
		for b in button:
			b.height = 2
			b.width = 10

	data = db.get_item(item_id=SelectedCardIDEdit)
	if data is None:
		await message.answer("Список пуст")
	else:
		data = list(data)
		if not edit:
			await bot.send_photo(chat_id=message.chat.id, 
					photo=data[1], 
					caption=f"""<b>Название:</b>: {data[2]} \n<b>Цена:</b> {data[3]} \n<b>Описание</b>: {data[4]}""", 
					reply_markup=edit_menu,
					parse_mode="html")	

		else:
			await bot.edit_message_media(chat_id=message.chat.id, 
										message_id=message.message_id, 
										media=InputMediaPhoto(media=data[1]))
			await bot.edit_message_caption(chat_id=message.chat.id, 
		                                message_id=message.message_id, 
		                                caption=f"""<b>Название:</b>: {data[2]} \n<b>Цена:</b> {data[3]} \n<b>Описание</b>: {data[4]}""",
		                                parse_mode="html",
		                                reply_markup=edit_menu)



async def edit_photo(message: Message, edit=None):
	await message.answer("Пришлите новое фото товара", reply_markup=get_cancel_kb())
	await ItemStatesGroup.edit_photo.set()

@dp.message_handler(lambda message: not message.photo, state=ItemStatesGroup.photo)
async def check_photo(message: Message):
	await message.reply("Это не фото")

@dp.message_handler(content_types=["photo"], state=ItemStatesGroup.edit_photo)
async def load_new_photo(message: Message, state: FSMContext):
	async with state.proxy() as data:
		data['edit_photo'] = message.photo[0].file_id

	db.update_photo(id=SelectedCardIDEdit, new_photo_id=data["edit_photo"])
	await message.answer("Фото товара успешно обновлено", reply_markup=ReplyKeyboardRemove())
	await state.finish()

async def edit_name(message: Message, edit=None):
	await message.answer("Пришлите новое название товара", reply_markup=get_cancel_kb())
	await ItemStatesGroup.edit_name.set()

@dp.message_handler(content_types=["text"], state=ItemStatesGroup.edit_name)
async def load_new_name(message: Message, state: FSMContext):
	async with state.proxy() as data:
		data['edit_name'] = message.text

	db.update_name(id=SelectedCardIDEdit, new_name=data["edit_name"])
	await message.answer("Название товара успешно обновлено", reply_markup=ReplyKeyboardRemove())
	await state.finish()

async def edit_price(message: Message, edit=None):
	await message.answer("Пришлите новую цену товара", reply_markup=get_cancel_kb())
	await ItemStatesGroup.edit_price.set()

@dp.message_handler(content_types=["text"], state=ItemStatesGroup.edit_price)
async def load_new_price(message: Message, state: FSMContext):
	async with state.proxy() as data:
		data['edit_price'] = message.text

	db.update_price(id=SelectedCardIDEdit, new_price=data["edit_price"])
	await message.answer("Цена товара успешно обновлена", reply_markup=ReplyKeyboardRemove())
	await state.finish()

async def edit_desc(message: Message, edit=None):
	await message.answer("Пришлите новое описание товара", reply_markup=get_cancel_kb())
	await ItemStatesGroup.edit_desc.set()

@dp.message_handler(content_types=["text"], state=ItemStatesGroup.edit_desc)
async def load_new_desc(message:Message, state:FSMContext):
	async with state.proxy() as data:
		data["edit_desc"] = message.text

	db.update_desc(id=SelectedCardIDEdit, new_desc=data["edit_desc"])
	await message.answer("Описание товара успешно обновлено")
	await state.finish()

'''Обработчик callback запросов'''

@dp.callback_query_handler(lambda call: True, state='*')
async def callback_worker(call: CallbackQuery, state: FSMContext):
	if call.data == "catalog":
		await GetCard(call.message, "edit")
	if call.data == "catalog1":
		await GetCard(call.message)
	if call.data == "admin":	
		await admin(call.message)
	if call.data == "cancel":
		await cancel(call.message, state)
	if call.data == "add":
		await add(call.message)
	if call.data == "edit":
		await editing(call.message)
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
	global SelectedCardIDEdit
	if call.data == "backEdit":	
		if SelectedCardIDEdit == 1:
			await editing(call.message, "edit")
		SelectedCardIDEdit -= 1
		await editing(call.message, "edit")
	if call.data == "nextEdit":
		SelectedCardIDEdit += 1
		await editing(call.message, "edit")
	if call.data == "edit_photo":
		await edit_photo(call.message)
	if call.data == "edit_name":
		await edit_name(call.message)
	if call.data == "edit_price":
		await edit_price(call.message)
	if call.data == "edit_desc":
		await edit_desc(call.message)

'''Запуск бота'''

if __name__ == "__main__":
	executor.start_polling(dp)