
import re
from typing import Pattern

from aiogram import types
from aiogram.types import Message


class MessageParser:
    def __init__(self, message: Message):
        self._message = message

    def get_id(self):
        id = re.search(r'(\s+\s)', self._message.text.strip())
        return id

    def get_ids(self):
        ids = re.findall(r'(?:\s+(\S+))+?', self._message.text.strip())
        return ids

    def get_name(self):
        name = re.search(r'/\S+\s+(\S+)', self._message.text).group(1)
        return name

    def get_note_dict(self):
        note_parts = re.search(
            r'([^(?:;;)]+);?;?([^(?:;;)]+)?;?;?([^(?:;;)]+)?', self._message.text).groups()
        note_parts = list(filter(lambda el: el, note_parts))
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


note_parts = re.search(r'([^(?:;;)]+);?;?([^(?:;;)]+)?;?;?([^(?:;;)]+)?',
                       'dawwaeda;;aedda;;efadeafaef;;dsas').groups()
print(list(filter(lambda el: el, note_parts)))
