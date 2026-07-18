import sqlite3

connection = sqlite3.connect("")
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS owners (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone_number TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL)""")
connection.commit()
cursor.execute("""CREATE TABLE IF NOT EXISTS appartments (id INTEGER PRIMARY KEY AUTOINCREMENT,appartment_number INTEGER NOT NULL,building TEXT NOT NULL,floor INTEGER NOT NULL,display_name TEXT NOT NULL UNIQUE,owner_id INTEGER, FOREIGN KEY (owner_id) REFERENCES owners(id))""")
connection.commit()
cursor.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,role TEXT NOT NULL,phone_number TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,owner_id INTEGER NOT NULL,password_hash TEXT NOT NULL,FOREIGN KEY (owner_id) REFERENCES owners(id))""")
connection.commit()
