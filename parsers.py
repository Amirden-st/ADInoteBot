from datetime import time
from math import e
import math
from exeptions import InvalidTimeStructureError, StructureError
import re
from typing import Pattern

from aiogram import types
from aiogram.types import Message


class MessageParser:
    def __init__(self, message: Message):
        self._message = message

    def get_id(self):
        id = re.findall(r'\S+\s+(\S+)', self._message.text.strip())
        if id:
            return int(id[0])
        else:
            return None

    def get_ids(self):
        ids = re.findall(r'(?:\s+(\S+))+?', self._message.text.strip())
        return ids

    def get_name(self):
        name = re.search(r'/\S+\s+(\S+)', self._message.text).group(1)
        return name

    def get_note_dict(self):
        note_parts = self._message.text.split(';;')
        note_dict = {'title': None, 'content': None,
                     'category_name': 'non_category'}
        if len(note_parts) == 1:
            note_dict['content'] = note_parts[0]
        elif len(note_parts) == 2:
            note_dict['content'] = note_parts[0]
            note_dict['category_name'] = note_parts[1]
        elif len(note_parts) == 3:
            note_dict['title'] = note_parts[0]
            note_dict['content'] = note_parts[1]
            note_dict['category_name'] = note_parts[2]

        return note_dict

    def get_todo_dict(self):
        try:
            todo_parts = re.search(r'\w\s+([^(;;)]+);;([^(;;)]+)$',
                                   self._message.text).groups()
        except AttributeError:
            raise StructureError
        todo_dict = {'content': None,
                     'deadline': None}

        time_dict = self._get_time_dict(todo_parts[1])

        todo_dict["content"] = todo_parts[0]
        todo_dict["deadline"] = time_dict
        return todo_dict

    @staticmethod
    def _get_time_dict(time_str):
        match = re.search(
            r'(?P<year>\d{2,4}(?=\.\d{2}\.\d{2}))?\.?(?P<month>\d{2}(?=\.\d{2}))?\.?(?P<day>\d{2})?(?:\s+)?(?P<hour>\d{1,2}):?(?P<minute>\d{2})?', time_str)
        if not match:
            raise InvalidTimeStructureError
        time_dict = match.groupdict()
        time_dict = {k: int(v) for k, v in time_dict.items() if not v is None}

        return time_dict

