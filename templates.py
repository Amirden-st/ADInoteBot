from jinja2 import FunctionLoader, Environment
from jinja2.loaders import FileSystemLoader


loader = FileSystemLoader("templates")
env = Environment(loader=loader)
env.lstrip_blocks = True
env.trim_blocks = True

note_template = env.get_template("note.jinja2")
notes_template = env.get_template("notes.jinja2")

todo_template = env.get_template("todo.jinja2")
todos_template = env.get_template("todos.jinja2")

category_template = env.get_template("category.jinja2")

result_template = env.get_template("result.jinja2")
