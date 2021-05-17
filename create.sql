PRAGMA foreign_keys = on;


CREATE TABLE IF NOT EXISTS users(
	id INTEGER PRIMARY KEY,
	active INTEGER NOT NULL DEFAULT TRUE,
	utc_offset VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS categories(
	name VARCHAR(255) PRIMARY KEY 
);

CREATE TABLE IF NOT EXISTS users_categories(
	id INTEGER PRIMARY KEY,
	user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
	category_name VARCHAR(255) REFERENCES categories(name),
	UNIQUE (user_id, category_name)
);

CREATE TABLE IF NOT EXISTS notes(
	id INTEGER PRIMARY KEY,
	title VARCHAR(255) NULL,
	content TEXT NOT NULL,
	created_at VARCHAR(20) NOT NULL,
	user_category_id INTEGER NOT NULL,
	FOREIGN KEY(user_category_id) REFERENCES users_categories(id) ON DELETE CASCADE
);

-- SELECT name FROM categories;
-- DROP TABLE notes;
-- DROP TABLE categories;
-- DROP TABLE users;
-- DROP TABLE users_categories;