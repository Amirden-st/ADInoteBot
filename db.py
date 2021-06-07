import datetime
import sqlite3
import uuid
from sqlite3.dbapi2 import IntegrityError

from exeptions import CategoryError, InvalidTimeError
from aiogram.types import user
from attr.setters import convert


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
    offset_minutes = int(offset["hours"]) * 60
    if offset_minutes < 0 and offset["minutes"]:
        offset_minutes -= int(offset["minutes"])
    elif offset_minutes > 0 and offset["minutes"]:
        offset_minutes += int(offset["minutes"])
    cur.execute("""
    --sql
    INSERT OR IGNORE INTO users(id, utc_offset) VALUES(?, ?) 
    ;
    """, (user_id, str(offset_minutes)))
    con.commit()


def get_notes(user_id, limit=10):
    cur.execute("""
        --sql
        SELECT notes.title as title, notes.content as content, users_categories.category_name as category_name, notes.created_at as created_at, notes.id as id
        FROM notes JOIN users_categories ON notes.user_category_id == users_categories.id
        WHERE users_categories.user_id == ?
        ORDER BY created_at
        ;
    """, (user_id,))
    notes = []
    for note in cur:
        notes.append(note)

    return notes[-limit:]


def insert_note(note_dict: dict, user_id):

    user_category_id = _get_user_category_id(
        note_dict['category_name'], user_id)

    if not user_category_id:
        raise CategoryError

    user_time = get_user_time(user_id).strftime('%y.%m.%d %H:%M')
    note_id = str(uuid.uuid4())[:8]

    cur.execute(f"""
    --sql
    insert into notes(id, title, content, created_at, user_category_id) 
    values(?, ?, ?, ?, ?)
    ;
    """, (note_id, note_dict['title'], note_dict['content'], user_time, user_category_id))
    con.commit()
    return note_id


def get_note(ids: tuple, user_id) -> list:
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
    return notes[::-1]


def del_note(notes_id, user_id):
    found = []
    not_found = []
    for i in notes_id:
        cur.execute("""
        --sql
        SELECT notes.id as id
        FROM notes JOIN users_categories ON notes.user_category_id == users_categories.id
        WHERE notes.id == ? AND users_categories.user_id == ?
        ;
        """, (i, user_id))
        note = cur.fetchone()
        if note:
            found.append(note["id"])
        else:
            not_found.append(i)
    cur.executemany("""
    --sql
    DELETE FROM notes 
    WHERE id == ?
    ;
    """, list(map(lambda id: (id, ), found)))

    con.commit()
    return found, not_found


def get_category(category_name, user_id):
    cur.execute("""
        --sql
        SELECT notes.title as title, notes.content as content, users_categories.category_name as category_name, notes.created_at as created_at, notes.id as id
        FROM notes JOIN users_categories ON notes.user_category_id == users_categories.id
        WHERE category_name == ? AND users_categories.user_id == ?
        ORDER BY created_at
        ;
        """, (category_name, user_id))
    notes = cur.fetchall()
    if not notes:
        raise CategoryError
    return notes


def del_category(category_name: str, user_id):
    cur.execute("""
    --sql
    SELECT id FROM users_categories 
    WHERE category_name == ? and user_id == ? 
    ;
    """, (category_name, user_id))
    category = cur.fetchone()
    if not category:
        raise CategoryError

    cur.execute("""
    --sql
    SELECT notes.id as id
    FROM notes JOIN users_categories ON notes.user_category_id == users_categories.id
    WHERE category_name == ? AND users_categories.user_id == ?
    ORDER BY created_at
    ;
    """, (category_name, user_id))

    count_of_found = len(cur.fetchall())

    cur.execute("""
    --sql
    DELETE FROM users_categories 
    WHERE id == ?
    ;
    """, (category["id"],))

    con.commit()
    return count_of_found


def add_user_category(category_name: str, user_id):

    _add_category(category_name)
    cur.execute("""
    --sql
    INSERT INTO users_categories(user_id, category_name) VALUES(?, ?)  
    ;
    """, (user_id, category_name))
    con.commit()


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
    if not id:
        return False
    return id['id']


def insert_todo(todo, user_id):
    user_datetime = get_user_time(user_id)
    user_datetime_dict = {
        "year": user_datetime.year,
        "month": user_datetime.month,
        "day": user_datetime.day,
        "hour": 12,
        "minute": 0
    }
    deadline = todo["deadline"]
    for k in user_datetime_dict:
        if deadline.get(k, False) is False:
            deadline[k] = user_datetime_dict[k]

    try:
        deadline_datetime = datetime.datetime(
            year=deadline["year"],
            month=deadline["month"],
            day=deadline["day"],
            hour=deadline["hour"],
            minute=deadline["minute"]
        )
    except ValueError:
        raise InvalidTimeError

    now = datetime.datetime.now()
    if now > deadline_datetime:
        raise InvalidTimeError

    user_time = get_user_time(user_id).strftime('%y.%m.%d %H:%M')
    todo_id = str(uuid.uuid4())[:8]

    cur.execute("""
    --sql
    INSERT INTO todos(id, content, deadline, created_at, user_id) VALUES(?, ?, ?, ?, ?) 
    ;
    """, (todo_id, todo["content"], deadline_datetime.strftime("%y.%m.%d %H:%M"), user_time, user_id))
    con.commit()
    return todo_id


def get_todos(user_id, limit=10):
    cur.execute("""
        --sql
        SELECT id, content, completed, created_at, deadline
        FROM todos
        WHERE user_id == ?
        ORDER BY created_at
        LIMIT ?
        ;
    """, (user_id, limit))
    todos = cur.fetchall()
    return todos


def get_todo(ids, user_id):
    todos = []
    for id in ids:
        cur.execute("""
        --sql
        SELECT id, content, completed, created_at, deadline 
        FROM todos
        WHERE id == ? AND user_id == ?
        ;
        """, (id, user_id))
        todo = cur.fetchone()
        if todo:
            todos.append(todo)
        else:
            todos.append(id)
    return todos[::-1]


def del_todo(ids, user_id):
    found = []
    not_found = []
    for i in ids:
        cur.execute("""
        --sql
        SELECT id 
        FROM todos 
        WHERE id == ? AND user_id == ?
        ;
        """, (i, user_id))
        todo = cur.fetchone()
        if todo:
            found.append(todo["id"])
        else:
            not_found.append(i)
    cur.executemany("""
    --sql
    DELETE FROM todos 
    WHERE id == ? 
    ;
    """, list(map(lambda id: (id, ), found)))

    con.commit()
    return found, not_found


def complete_todo(ids, user_id):
    found = []
    not_found = []
    already_completed = []
    for i in ids:
        cur.execute("""
        --sql
        SELECT id, completed as already_completed 
        FROM todos 
        WHERE id == ? AND user_id == ?
        ;
        """, (i, user_id))
        todo = cur.fetchone()
        if todo:
            if not todo["already_completed"]:
                found.append(todo["id"])
            else:
                already_completed.append(todo["id"])
        else:
            not_found.append(i)
    cur.executemany("""
    --sql
    UPDATE todos
    SET completed = 1 
    WHERE id == ?
    ;
    """, list(map(lambda id: (id, ), found)))

    con.commit()
    return found, not_found, already_completed


def uncomplete_todo(ids, user_id):
    found = []
    not_found = []
    already_uncompleted = []
    for i in ids:
        cur.execute("""
        --sql
        SELECT id, completed  
        FROM todos 
        WHERE id == ? AND user_id == ?
        ;
        """, (i, user_id))
        todo = cur.fetchone()
        if todo:
            if todo["completed"]:
                found.append(todo["id"])
            else:
                already_uncompleted.append(todo["id"])
        else:
            not_found.append(i)
    cur.executemany("""
    --sql
    UPDATE todos
    SET completed = 0 
    WHERE id == ?
    ;
    """, list(map(lambda id: (id, ), found)))

    con.commit()
    return found, not_found, already_uncompleted


def init_user(user_id, offset):
    add_user(user_id, offset)
    add_user_category('non_category', user_id)


def get_user_time(user_id):
    offset = _get_user_offset(user_id)
    utc0 = datetime.datetime.utcnow()
    user_time = utc0 + datetime.timedelta(minutes=offset)
    return user_time


def _get_user_offset(user_id):
    cur.execute("""
    --sql
    SELECT utc_offset FROM users
    WHERE id == ?
    ;
    """, (user_id, ))
    offset = cur.fetchone()['utc_offset']
    return int(offset)
