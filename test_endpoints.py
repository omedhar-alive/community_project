from fastapi.testclient import TestClient
from main import app,get_db
import sqlite3
import pytest
client = TestClient(app)

def overide_get_db():
    connection = sqlite3.connect("test.db",check_same_thread=False)
    connection.execute("PRAGMA foreign_keys= ON")
    connection.row_factory = sqlite3.Row
    try :    
        yield connection
    finally:
        connection.close()

app.dependency_overrides[get_db]= overide_get_db

@pytest.fixture
def fresh_db():
    connection = sqlite3.connect("test.db")
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS owners (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone_number TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL)""")
    connection.commit()
    cursor.execute("""CREATE TABLE IF NOT EXISTS appartments (id INTEGER PRIMARY KEY AUTOINCREMENT,appartment_number INTEGER NOT NULL,building TEXT NOT NULL,floor INTEGER NOT NULL,display_name TEXT NOT NULL UNIQUE,owner_id INTEGER, FOREIGN KEY (owner_id) REFERENCES owners(id))""")
    connection.commit()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,role TEXT NOT NULL,phone_number TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,owner_id INTEGER NOT NULL,password_hash TEXT NOT NULL,FOREIGN KEY (owner_id) REFERENCES owners(id))""")
    connection.commit()
    yield 
    cursor.execute("DROP TABLE owners")
    connection.commit()
    cursor.execute("DROP TABLE users")
    connection.commit()
    cursor.execute("DROP TABLE appartments")
    connection.commit()



def test_create_owner(fresh_db):
    response = client.post("/owners",json={"name":"test_check","phone_number":"1414","email":"testingthetest@example.com","password":"pwpwpw"})
    assert response.status_code == 200
