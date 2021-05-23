import datetime
import re
import sqlite3
import uuid
from sqlite3.dbapi2 import IntegrityError

from aiogram.types import user
from attr.setters import convert

# root_dir = os.path.dirname(__file__)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


con = sqlite3.connect('notes.db')
con.row_factory = dict_factory
cur = con.cursor()
sql_f = open('create.sql').read()
cur.executescript(sql_f)


def add_user(user_id, offset: dict):
    offset_min = int(offset["hours"]) * 60
    if offset_min < 0 and offset["minutes"]:
        offset_min -= int(offset["minutes"])
    elif offset_min > 0 and offset["minutes"]:
        offset_min += int(offset["minutes"])
    cur.execute("""
    --sql
    INSERT OR IGNORE INTO users(id, utc_offset) VALUES(?, ?) 
    ;
    """, (user_id, str(offset_min)))
    con.commit()


def get_notes(limit=10):
    cur.execute("""
    --sql
    select * from notes order by created_at limit ?
    ;
    """, (limit,))

    response = ''
    for note in cur:
        response += render_response_body(note)

    if not response:
        return 'Notes are not found'

    return response


def insert_note(note_dict: dict, user_id):
    try:
        user_category_id = _get_user_category_id(
            note_dict['category_name'], user_id)
        if not user_category_id:
            return f"""
            The "{note_dict["category_name"]}" category does not exist.\nIf you want to add it, write: /add_category {note_dict["category_name"]}
            """
        user_time = _get_user_time(user_id)
        note_id = uuid.uuid3(uuid.NAMESPACE_DNS, 'hello world')
        cur.execute(f"""
        --sql
        insert into notes(id, title, content, created_at, user_category_id) 
        values(?, ?, ?, ?)
        ;
        """, (note_id, note_dict['title'], note_dict['content'], user_time, user_category_id))
        con.commit()
        return 'The note was written down.'
    except sqlite3.IntegrityError:
        return f"The {note_dict['category_name']} category does not exist."


def get_note(ids:tuple, user_id) -> list:
    notes = []
    for id in ids:
        cur.execute("""
        --sql
        SELECT notes.title as title, notes.content as content, users_categories.category_name as category_name, notes.created_at as created_at, notes.id as id
        FROM notes JOIN users_categories ON notes.user_category_id == users_categories.id
        WHERE notes.id == ? AND users_categories.user_id == ?
        ;
        """, (id, user_id))
        note = cur.fetchone()
        if note:
            notes.append(note)
        else:
            notes.append(id)
    return notes

def del_note(id, user_id):
    id_exist = []  
    for i in id:
        cur.execute(f"""
        --sql
        SELECT notes.id as id
        FROM notes JOIN users_categories ON notes.user_category_id == users_categories.id
        WHERE notes.id == ? AND users_categories.user_id =={user_id}
        ;
        """, (i, user_id))
        note_id = cur.fetchone()
        id_exist.append(bool(note_id))
    return dict(zip(id, id_exist))

def get_category(category_name):
    cur.execute("""
    --sql
    SELECT * FROM notes 
    WHERE category == ?
    ORDER BY created_at DESC
    ;
    """, (category_name,))
    response = ''

    for note in cur:
        response += render_response_body(note)

    if not response:
        return 'Notes are not found'

    return response


def add_user_category(category_name: str, user_id):
    try:
        _add_category(category_name)
        cur.execute("""
        --sql
        INSERT INTO users_categories(user_id, category_name) VALUES(?, ?)  
        ;
        """, (user_id, category_name))
        con.commit()
        return f'The "{category_name}" category was added'

    except IntegrityError:
        return f'The "{category_name}" category already exists'


def del_category(category_name: str):
    cur.execute("""
    --sql
    DELET * FROM categories 
    WHERE name == ? 
    ;
    """, (category_name,))
    con.commit()


def render_response_body(note_dict: dict):
    response = ''

    response += response_body.render(note_dict=note_dict, show_date=show_date)

    return response


def create_note_dict(cur):

    return


def _add_category(category_name):
    cur.execute("""
    --sql
    INSERT OR IGNORE INTO categories(name) VALUES(?) 
    ;
    """, (category_name, ))


def _get_user_category_id(category_name, user_id):
    cur.execute("""
    --sql
    SELECT id FROM users_categories 
    WHERE  category_name == ? AND user_id == ?  
    ;
    """, (category_name, user_id))
    id = cur.fetchone()
    if not id['id']:
        return False
    return id['id']


def init_user(user_id, offset):
    add_user(user_id, offset)
    add_user_category('non_category', user_id)
    add_user_category('today', user_id)


def _get_user_time(user_id):
    offset = _get_user_offset(user_id)
    utc0 = datetime.datetime.utcnow()
    user_time = utc0 + datetime.timedelta(minutes=offset)
    return str(user_time.strftime('%d.%m.%y %H:%M'))


def _get_user_offset(user_id):
    cur.execute("""
    --sql
    SELECT utc_offset FROM users
    WHERE id == ?
    ;
    """, (user_id, ))
    offset = cur.fetchone()['utc_offset']
    return int(offset)
# def get_category_id_by_name(name, user_id):
#     category_id = cur.execute("""
#     --sql
#     SELECT id FROM categories WHERE name == ? AND user_id == ?
#     ;
#     """, (name, user_id))
#     return category_id[0]


# def get_category_name_by_id(id, user_id):
#     category_id = cur.execute("""
#     --sql
#     SELECT name FROM categories WHERE id == ? AND user_id == ?
#     ;
#     """, (id, user_id))
#     return category_id[0]
