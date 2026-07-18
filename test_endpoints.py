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



def test_owner_create_user(fresh_db):
    created_owner = client.post("/owners",json={"name":"test_check","phone_number":"1414","email":"testingthetest@example.com","password":"pwpwpw"})
    
    logged_owner = client.post("/owners/login",data={"username":"testingthetest@example.com","password":"pwpwpw"})
    token = logged_owner.json()["access_token"]
    owner_create_user = client.post("/user",headers={"Authorization" : f"bearer {token}"},json={"name":"omartest","phone_number":"9999","email":"pytest@test.com","password":"pytest","role":"pytest","owner_id":4})
    owner = client.get("/owners",headers={"Authorization" : f"bearer {token}"})
    owner_id = owner.json()["id"]
    connection = sqlite3.connect("test.db",check_same_thread=False)
    connection.execute("PRAGMA foreign_keys= ON")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT owners.email AS owner_email,users.email AS user_email,users.owner_id FROM owners JOIN users ON owners.id = users.owner_id WHERE owners.id = ?",(owner_id,))
    result = cursor.fetchall()
    created_user = next((u for u in result if u["user_email"]=="pytest@test.com"))
    user_owner_id = created_user["owner_id"]

    assert user_owner_id == owner_id 


