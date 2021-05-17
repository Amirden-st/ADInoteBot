import logging

from aiogram.dispatcher.filters import state
import db
import re
import parsers

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage



class DataInput(StatesGroup):
    state = State()


API_TOKEN = '1791066149:AAE3Ca3BRZZrQqVhUv2wckZ9HugTDVCCPuA'

# Configure logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands=['start'])
async def send_welcome(message:types.Message):
    await message.reply("""
    Hello!\nI'm a bot for notes. To start working with the bot, specify your UTS offset. for example:\n__+3__\n__-3__
    """)
    await DataInput.state.set()

    

@dp.message_handler(state=DataInput.state)
async def init(message:types.Message, state:FSMContext):
    offset = re.search(r'(?P<hours>[-+]?\d{,2}):?(?P<minutes>\d{2})?', message.text).groupdict()
    if not offset['hours']:
        await message.reply("Invalid structure.Please try again.\nHint:__hours:minutes__")
        return 
    db.init_user(message.chat.id, offset)
    await message.reply("""
    Now let's start to work!
    """)

    await state.finish()


@dp.message_handler(lambda m: m.text.startswith('/get_note '))
async def send_note(message: types.Message):
    ids = parsers.MessageParser(message).get_ids()
    response = db.get_note(ids, message.chat.id)
    await message.reply(response)


@dp.message_handler(lambda m: m.text.startswith('/del_note '))
async def del_note(message: types.Message):
    note_ids = parsers.MessageParser(message).get_ids()
    response = db.del_note(note_ids, message.chat.id)
    await message.reply(response)


@dp.message_handler(lambda m: m.text.startswith('/get_notes '))
async def send_notes(message: types.Message):
    match = re.search(r'/get_notes\s+(\d)+$', message.text)
    if match:
        response = db.get_notes(match.group(1))
    else:
        response = db.get_notes()
    await message.reply(response)


@dp.message_handler(lambda m: m.text.startswith('/get_category'))
async def send_category(message: types.Message):
    category_name = re.findall(r'/get_category\s+(\w+)$', message.text)[0]
    response = db.get_category(category_name)
    await message.reply(response)


@dp.message_handler(lambda m: m.text.startswith('/add_category'))
async def add_category(message: types.Message):
    category_name = re.findall(r'/add_category\s+(\w+)$', message.text)[0]
    response = db.add_user_category(category_name, message.chat.id)
    await message.reply(response)


@dp.message_handler(lambda m: m.text.startswith('/del_category'))
async def del_category(message: types.message):
    # category_name = re.findall(r'/get_category\s+(\w+)$', message.text)[0]
    # response = db.del_category(category_name)
    # await message.reply(response)
    pass


@dp.message_handler()
async def write_notes(message: types.Message):
    note_dict = parsers.MessageParser(message).get_note_dict()
    response = db.insert_note(note_dict, message.chat.id)
    await message.reply(response)


# def _parse_message(message_text: str, user_id):
#     pattern = r"([^-:]+)-?:?([^-:]+)?-?:?([^-:]+)?"
#     rows = list(filter(lambda string: string,
#                 re.search(pattern, message_text).groups()))
#     note_dict = {'title': None, 'content': None,
#                  'user_category_id': 'non_category'}
#     db._get_users_categories_id
#     return db.create_note_dict(rows, user_id)




if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
