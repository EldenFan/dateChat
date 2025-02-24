import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    CallbackQuery
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import random
from config import API_TOKEN, ADMINS
from state import ProfileStates
import bd
from keyboardClass import Keyboard

logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage()) 


start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Создать анкету")],
        [KeyboardButton(text="Моя анкета")],
        [KeyboardButton(text="Посмотреть анкеты")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
@dp.message(F.text == "Начать")
async def send_welcome(message: Message):
    await message.answer("Привет! Я бот для знакомств. Выберите действие на клавиатуре ниже:", reply_markup=start_kb)

@dp.message(Command("create_profile"))
@dp.message(F.text == "Создать анкету")
async def start_creating_profile(message: Message, state: FSMContext):
    await bd.delete_user(message.chat.id)
    await message.answer("Как вас зовут?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ProfileStates.waiting_for_name)

@dp.message(ProfileStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Укажите ваш пол:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text = "Мужчина"), KeyboardButton(text = "Женщина")]], resize_keyboard=True))
    await state.set_state(ProfileStates.waiting_for_gender)

@dp.message(ProfileStates.waiting_for_gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Кого вы ищете?", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text = "Мужчина"), KeyboardButton(text = "Женщина")]], resize_keyboard=True))
    await state.set_state(ProfileStates.waiting_for_search_gender)

@dp.message(ProfileStates.waiting_for_search_gender)
async def process_search_gender(message: Message, state: FSMContext):
    await state.update_data(search_gender=message.text)
    await message.answer("Какая у вас цель общения?", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text = "Знакомство"), KeyboardButton(text = "Отношения")]], resize_keyboard=True))
    await state.set_state(ProfileStates.waiting_for_goal)

@dp.message(ProfileStates.waiting_for_goal)
async def process_goal(message: Message, state: FSMContext):
    await state.update_data(goal=message.text)
    await message.answer("Выберите ваши предпочтения (Когда закончите введите /stop):", reply_markup=trait_kb.get_page())
    await state.set_state(ProfileStates.waiting_for_preferences)

@dp.callback_query(ProfileStates.waiting_for_preferences, F.data.startswith("page_"))
async def next_page(callback_query: CallbackQuery):
    page_number = int(callback_query.data.split('_')[1])
    trait_page = trait_kb.get_page(current_page=page_number)
    await callback_query.message.edit_reply_markup(reply_markup=trait_page)
    await callback_query.answer()

@dp.callback_query(F.data.startswith("trait_"), ProfileStates.waiting_for_preferences)
async def add_preferences(callback_query: CallbackQuery):
    trait = callback_query.data.split('_')[1]
    print(trait)
    await bd.set_preference(callback_query.from_user.id, trait)

@dp.message(ProfileStates.waiting_for_preferences, Command("stop"))
async def stop_adding_preferences(message: Message, state: FSMContext):
    await message.answer("Что из этого описывает вас (Когда закончите введите /stop) :", reply_markup=trait_kb.get_page())
    await state.set_state(ProfileStates.waiting_for_selfcharacters)

@dp.callback_query(ProfileStates.waiting_for_selfcharacters, F.data.startswith("page_"))
async def next_page(callback_query: CallbackQuery):
    page_number = int(callback_query.data.split('_')[1])
    trait_page = trait_kb.get_page(current_page=page_number)
    await callback_query.message.edit_reply_markup(reply_markup=trait_page)
    await callback_query.answer()

@dp.callback_query(ProfileStates.waiting_for_selfcharacters, F.data.startswith("trait_"))
async def add_selfcharacters(callback_query: CallbackQuery):
    trait = callback_query.data.split('_')[1]
    await bd.set_selfcharacters(callback_query.from_user.id, trait)   

@dp.message(ProfileStates.waiting_for_selfcharacters, Command("stop"))
async def process_preferences(message: Message, state: FSMContext):
    await message.answer("Расскажите немного о себе:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ProfileStates.waiting_for_description)

@dp.message(ProfileStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Отправьте фото или нажмите 'Пропустить'.", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text = "Пропустить")]], resize_keyboard=True))
    await state.set_state(ProfileStates.waiting_for_photo)

@dp.message(ProfileStates.waiting_for_photo, F.content_type == "photo")
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(image=message.photo[-1].file_id)
    await message.answer("Отправьте вашу локацию или нажмите 'Пропустить'.", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить локацию", request_location=True)],
        [KeyboardButton(text="Пропустить")]], resize_keyboard=True))
    await state.set_state(ProfileStates.waiting_for_location)

@dp.message(ProfileStates.waiting_for_photo)
async def skip_photo(message: Message, state: FSMContext):
    await state.update_data(image=None)
    await message.answer("Отправьте вашу локацию или нажмите 'Пропустить'.", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить локацию", request_location=True)],
        [KeyboardButton(text="Пропустить")]], resize_keyboard=True))
    await state.set_state(ProfileStates.waiting_for_location)

@dp.message(ProfileStates.waiting_for_location, F.content_type == "location")
async def process_location(message: Message, state: FSMContext):
    user_data = await state.get_data()
    location = f"{message.location.latitude}, {message.location.longitude}"
    await bd.create_user(message.chat.id, user_data["name"], user_data['gender'], user_data['search_gender'],
                    user_data['goal'], user_data['description'], user_data['image'], location)
    await message.answer("Ваша анкета сохранена!", reply_markup=start_kb)
    await state.clear()

@dp.message(ProfileStates.waiting_for_location)
async def skip_location(message: Message, state: FSMContext):
    user_data = await state.get_data()
    location = None
    await bd.create_user(message.chat.id, user_data["name"], user_data['gender'], user_data['search_gender'],
                    user_data['goal'], user_data['description'], user_data['image'], location)
    await message.answer("Ваша анкета сохранена!", reply_markup=start_kb)
    await state.clear()

@dp.message(Command("my_profile"))
@dp.message(F.text == "Моя анкета")
async def my_profile(message: Message):
    profile_data = await bd.get_user(message.chat.id)
    if profile_data["image"]:
        await message.answer_photo(
            photo=profile_data["image"],
            caption=f"{profile_data['name']}\n"
                    f"Цель: {profile_data['goal']}\n"
                    f"Список предпочтений: {profile_data['preferences']}\n"
                    f"Свои черты: {profile_data['selfcharacters']}\n"
                    f"{profile_data['description']}"
        )
    else:
        await message.answer(
            text=f"{profile_data['name']}\n"
                 f"Цель: {profile_data['goal']}\n"
                 f"Предпочтения: {profile_data['preferences']}\n"
                 f"Свои черты: {profile_data['selfcharacters']}\n"
                 f"{profile_data['description']}"
        )

@dp.message(Command("find"))
@dp.message(F.text == "Посмотреть анкеты")
async def find_profile(message: Message):
    profiles = await bd.matching_profiles(message.chat.id)
    if len(profiles) == 0:
        if await bd.get_user(message.chat.id) is None:
            await message.answer("Вы не создали анкету")
        else:
            await message.answer("Не найдено подхадящих а")
    print(profiles)
    profile_data = random.choice(profiles)
    distance = "Расстояние не известно" if profile_data["distance"] is None else profile_data["distance"]
    if profile_data["image"]:
        await message.answer_photo(
            photo=profile_data["image"],
            caption=f"{profile_data['name']}, {distance}\n"
                    f"Цель: {profile_data['goal']}\n"
                    f"Предпочтения: {profile_data['preferences']}\n"
                    f"{profile_data['description']}"
        )
    else:
        await message.answer(
            text=f"{profile_data['name']}, {distance}\n"
                 f"Цель: {profile_data['goal']}\n"
                 f"Предпочтения: {profile_data['preferences']}\n"
                 f"{profile_data['description']}"
        )

@dp.message(Command("add_trait"), F.from_user.id.in_(ADMINS))
async def start_adding(message: Message, state: FSMContext):
    await message.answer("Вы можете вводить черты, когда закончите введите /stop")
    await state.set_state(ProfileStates.adding_traits)

@dp.message(ProfileStates.adding_traits, Command("stop"))
async def stop_adding(message: Message, state: FSMContext):
    await message.answer("Вы закончили добавлять черты")
    await state.clear()

@dp.message(ProfileStates.adding_traits)
async def add_more_trait(message: Message):
    await bd.add_trait(message.text)
    global trait_kb
    trait_kb = Keyboard(await bd.get_traits())


async def main():
    global trait_kb 
    await bd.start_bd()
    trait_kb = Keyboard(await bd.get_traits())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())