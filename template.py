from jinja2 import FunctionLoader, Template, Environment


def load_func(templ):
    if templ == "note_template":
        note_template = """
{% block header scoped %}
--------------------------------      
{% if note.title is none %}
({{note.id}})
{% else %}
{{note.title}} ({{note.id}})
{% endif %}
{% endblock %}
{% block content scoped %}
{{ note.content[:50] + '...' if note.content | length > 50 else note.content[:50] }}
{% endblock %}
{% block footer scoped %}
{% if show_date %}{{note.created_at}}    #{{note.category_name}}
{% else %}{{note.category_name}} 
{% endif %}
{% endblock %}
"""
        return note_template
    elif templ == "notes_template":
        notes_template = '''
{% extends note_template %}
{% for note in notes %}
{% if note is not string %}
{% block header %}{{super()}}{% endblock %}
{% block content %}{{super}}{% endblock %}
{% block footer %}{{self}}{% endblock %}

{% endif %}
{% endfor %}
{% set not_found = notes | selectattr("content", "undefined") | list %}
{% if not_found %}
Not found notes:
{% for id in not_found %}**{{ id }}**{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}
'''
        return notes_template


env = Environment(loader=FunctionLoader(load_func))
env.lstrip_blocks = True
env.trim_blocks = True

note_template = env.get_template("note_template")
notes_template = env.get_template("notes_template")
# category_template = env.get_template("category_template")
msg = notes_template.render(notes=[{"id": "wdea12", "content": "something",
                            "created_at": "02.02.2001", "category_name": "non_category"}], note_template=note_template)
print(msg)
