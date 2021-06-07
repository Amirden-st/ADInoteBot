PRAGMA foreign_keys = on;

CREATE TABLE IF NOT EXISTS users(
	id INTEGER PRIMARY KEY,
	active INTEGER NOT NULL DEFAULT TRUE,
	utc_offset VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS todos(
	id VARCHAR(10) PRIMARY KEY,
	content TEXT NOT NULL,
	user_id INTEGER NOT NULL,
	completed INTEGER NOT NULL DEFAULT FALSE,
	created_at VARCHAR(20) NOT NULL,
	deadline VARCHAR(20) NOT NULL,
	FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
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
	id VARCHAR(10) PRIMARY KEY,
	title VARCHAR(255) NULL,
	content TEXT NOT NULL,
	created_at VARCHAR(20) NOT NULL,
	user_category_id INTEGER NOT NULL,
	FOREIGN KEY(user_category_id) REFERENCES users_categories(id) ON DELETE CASCADE
);

-- SELECT name FROM categories;
-- DROP TABLE notes;
-- DROP TABLE todos;
-- DROP TABLE categories;
-- DROP TABLE users;
-- DROP TABLE users_categories;
