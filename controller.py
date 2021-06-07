import asyncio
import datetime
import logging
import math
import os
import re
from sqlite3.dbapi2 import IntegrityError

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import state
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import user
from aiogram.types.base import T
from aiogram.types.message import ParseMode
from aiogram.utils.executor import start_webhook
from attr import resolve_types

import config
import db
import parsers
import templates
from exeptions import (CategoryError, InvalidTimeError,
                       InvalidTimeStructureError)


class DataInput(StatesGroup):
    state = State()


API_TOKEN = '1791066149:AAE3Ca3BRZZrQqVhUv2wckZ9HugTDVCCPuA'

# webhook settings
WEBHOOK_HOST = 'https://frozen-wildwood-39904.herokuapp.com/'
WEBHOOK_URL = f"{WEBHOOK_HOST}//{API_TOKEN}"

# webserver settings
WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = int(os.environ.get('PORT', 5000))


# Configure logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("""
    Hello!\nI'm a bot for notes. To start working with the bot, specify your UTS offset. for example:\n__+3__\n__-3__
    """)
    await DataInput.state.set()


@dp.message_handler(state=DataInput.state)
async def init(message: types.Message, state: FSMContext):
    offset = re.search(
        r'(?P<hours>[-+]?\d{,2}):?(?P<minutes>\d{2})?', message.text).groupdict()
    if not offset['hours']:
        await message.reply("Invalid structure.Please try again.\nHint:_hours:minutes_", parse_mode="markdown")
        return
    db.init_user(message.chat.id, offset)
    await message.reply("""
    Now let's start to work!
    """)

    await state.finish()


@dp.message_handler(lambda m: m.text.startswith('/get_notes'))
async def send_notes(message: types.Message):
    limit = parsers.MessageParser(message).get_id()
    if limit:
        notes = db.get_notes(message.from_user.id, limit)
    else:
        notes = db.get_notes(message.from_user.id)
    if not notes:
        await message.reply("Notes are not found.")
    rendered = templates.notes_template.render(
        notes=notes, note_template=templates.note_template, content_length=50, show_date=config.show_date)
    await message.reply(rendered)


@dp.message_handler(lambda m: m.text.startswith('/get_note'))
async def send_note(message: types.Message):
    ids = parsers.MessageParser(message).get_ids()
    notes = db.get_note(ids, message.chat.id)
    response = templates.notes_template.render(
        notes=notes, note_template=templates.note_template, show_date=config.show_date)
    await message.reply(response)


@dp.message_handler(lambda m: m.text.startswith('/del_note '))
async def del_note(message: types.Message):
    note_ids = parsers.MessageParser(message).get_ids()
    found, not_found = db.del_note(note_ids, message.chat.id)
    response = templates.result_template.render(
        found=found, not_found=not_found, type="notes", action="deleted")
    await message.reply(response, parse_mode="Markdown")


@dp.message_handler(lambda m: m.text.startswith('/get_category'))
async def send_category(message: types.Message):
    category_name = parsers.MessageParser(message).get_name()
    try:
        notes = db.get_category(category_name, message.chat.id)
    except CategoryError:
        await message.reply(f'The "{category_name}" does not exist.')
        return
    response = templates.category_template.render(
        notes=notes, note_template=templates.note_template, category_name=category_name, show_date=config.show_date)
    await message.reply(response)


@dp.message_handler(lambda m: m.text.startswith('/add_category'))
async def add_category(message: types.Message):
    category_name = re.findall(r'/add_category\s+(\w+)$', message.text)[0]
    try:
        db.add_user_category(category_name, message.chat.id)

    except IntegrityError:
        await message.reply(f'The "{category_name}" category already exists.')
        return

    await message.reply(f'The "{category_name}" category was created.')


@dp.message_handler(lambda m: m.text.startswith('/del_category'))
async def del_category(message: types.Message):
    category_name = parsers.MessageParser(message).get_name()
    try:
        count_of_found = db.del_category(category_name, message.chat.id)
    except CategoryError:
        await message.reply(f'The "{category_name}" does not exist.')
        return
    response = templates.result_template.render(
        count_of_found=count_of_found, not_found=[], category_name=category_name, type="notes", action="deleted")
    await message.reply(response)


@dp.message_handler(lambda m: m.text.startswith('/get_todos'))
async def send_todos(message: types.Message):
    limit = parsers.MessageParser(message).get_id()
    if limit:
        todos = db.get_todos(message.from_user.id, limit)
    else:
        todos = db.get_todos(message.from_user.id)
    if not todos:
        await message.reply("Todos are not found.")
    user_time = db.get_user_time(message.chat.id).strftime("%y.%m.%d %H:%M")
    rendered = templates.todos_template.render(
        todos=todos, content_length=50, user_time=user_time, show_date=config.show_date)
    await bot.send_message(message.chat.id, rendered)


@dp.message_handler(lambda m: m.text.startswith('/get_todo'))
async def get_todo(message: types.Message):
    ids = parsers.MessageParser(message).get_ids()
    todos = db.get_todo(ids, message.chat.id)
    response = templates.todos_template.render(
        todo_template=templates.todo_template, todos=todos, show_date=config.show_date)
    await message.reply(response)


@dp.message_handler(lambda m: m.text.startswith('/todo'))
async def insert_todo(message: types.Message):
    try:
        todo = parsers.MessageParser(message).get_todo_dict()
        todo_id = db.insert_todo(todo, message.chat.id)
        await message.reply(f'The todo was writen down. Its id: _{todo_id}_',  parse_mode="Markdown")

    except InvalidTimeStructureError:
        await message.reply("You entered the time in the wrong format.")
    except InvalidTimeError:
        await message.reply("You entered wrong time.")


@dp.message_handler(lambda m: m.text.startswith('/del_todo'))
async def del_todo(message: types.Message):
    todo_ids = parsers.MessageParser(message).get_ids()
    found, not_found = db.del_todo(todo_ids, message.chat.id)
    response = templates.result_template.render(
        found=found, not_found=not_found, type="todos", action="deleted")
    await message.reply(response, parse_mode="Markdown")


@dp.message_handler(lambda m: m.text.startswith('/complete'))
async def complete_todo(message: types.Message):
    todo_ids = parsers.MessageParser(message).get_ids()
    found, not_found, already_completed = db.complete_todo(
        todo_ids, message.chat.id)
    response = templates.result_template.render(
        found=found, not_found=not_found, already_done=already_completed, type="todos", action="updated")
    await message.reply(response, parse_mode="Markdown")


@dp.message_handler(lambda m: m.text.startswith('/uncomplete'))
async def uncomplete_todo(message: types.Message):
    todo_ids = parsers.MessageParser(message).get_ids()
    found, not_found, already_uncompleted = db.uncomplete_todo(
        todo_ids, message.chat.id)
    response = templates.result_template.render(
        found=found, not_found=not_found, already_done=already_uncompleted, type="todos", action="uncompleted")
    await message.reply(response, parse_mode="Markdown")


@dp.message_handler()
async def write_notes(message: types.Message):
    note_dict = parsers.MessageParser(message).get_note_dict()
    try:
        note_id = db.insert_note(note_dict, message.chat.id)
    except CategoryError:
        await message.reply(f'"{note_dict["category_name"]}" category does not exist.')
    else:
        await message.reply(f'The note was writen down. Its id: _{note_id}_',  parse_mode="Markdown")



# async def sheduled(wait_for):
#     while True:
#         await asyncio.sleep(wait_for)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    # insert code here to run it after start


async def on_shutdown(dp):
    logging.warning('Shutting down..')

    # insert code here to run it before shutdown

    # Remove webhook (not acceptable in some cases)
    await bot.delete_webhook()

    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('Bye!')

if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # loop.create_task(sheduled(10))

    start_webhook(
        dispatcher=dp,
        webhook_path='//'+API_TOKEN,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
