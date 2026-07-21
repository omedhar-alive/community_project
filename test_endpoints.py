from fastapi.testclient import TestClient
from main import app,get_db
import sqlite3
import pytest
from apt_generator import apt_generator
from pathlib import Path
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
    connection = sqlite3.connect("test.db",check_same_thread=False)
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS owners (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone_number TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL)""")
    connection.commit()
    cursor.execute("""CREATE TABLE IF NOT EXISTS appartments (id INTEGER PRIMARY KEY AUTOINCREMENT,appartment_number INTEGER NOT NULL,building TEXT NOT NULL,floor INTEGER NOT NULL,display_name TEXT NOT NULL UNIQUE,owner_id INTEGER, FOREIGN KEY (owner_id) REFERENCES owners(id) ON DELETE SET NULL)""")
    connection.commit()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,role TEXT NOT NULL,phone_number TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,owner_id INTEGER NOT NULL,password_hash TEXT NOT NULL,FOREIGN KEY (owner_id) REFERENCES owners(id) ON DELETE CASCADE)""")
    connection.commit()
    yield connection
    cursor.execute("DROP TABLE owners")
    connection.commit()
    cursor.execute("DROP TABLE users")
    connection.commit()
    cursor.execute("DROP TABLE appartments")
    connection.commit()
    connection.close()


def test_owner_create_user(fresh_db):
    created_owner = client.post("/owners",json={"name":"test_check","phone_number":"1414","email":"testingthetest@example.com","password":"pwpwpw"})
    
    logged_owner = client.post("/owners/login",data={"username":"testingthetest@example.com","password":"pwpwpw"})
    token = logged_owner.json()["access_token"]
    owner_create_user = client.post("/users",headers={"Authorization" : f"Bearer {token}"},json={"name":"omartest","phone_number":"9999","email":"pytest@test.com","password":"pytest","role":"pytest","owner_id":4})
    owner = client.get("/owners",headers={"Authorization" : f"Bearer {token}"})
    owner_id = owner.json()["id"]
    connection = fresh_db
    connection.execute("PRAGMA foreign_keys= ON")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email= ?",("pytest@test.com",))
    user = cursor.fetchone()
    user_owner_id = user["owner_id"]
    assert user_owner_id == owner_id

def test_delete_owner(fresh_db):
    connection = fresh_db
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys= ON")
    cursor = connection.cursor()
    created_owner = client.post("/owners",json={"name":"Omar","phone_number": "123456789","email":"omedhar@gmail.com","password":"SECRET_KEY"})
    response = client.post("/owners/login",data={"username":"omedhar@gmail.com","password":"SECRET_KEY"})
    token = response.json()["access_token"]
    cursor.execute("SELECT * FROM owners WHERE email= ?",("omedhar@gmail.com",))
    owner = cursor.fetchone()
    assert owner is not None
    owner_id = owner["id"]
    created_user = client.post("/users",headers={"Authorization": f"Bearer {token}"},json={"name":"user","email":"user@example.com","phone_number":"54321","role":"tennant","password":"123456","owner_id":owner_id})
    cursor.execute("SELECT * FROM users WHERE email= ?",("user@example.com",))
    verify_user = cursor.fetchone()
    assert verify_user is not None
    cursor.execute("DELETE FROM owners WHERE email= ?",("omedhar@gmail.com",))
    connection.commit()
    cursor.execute("SELECT * FROM users WHERE owner_id= ?",(owner_id,))
    user = cursor.fetchall()
    assert user == []

def test_delete_owner_apt(fresh_db):
    client.post("/owners",json={"name":"Omar","phone_number": "123456789","email":"omedhar@gmail.com","password":"SECRET_KEY"})
    connection = fresh_db
    connection.execute("PRAGMA foreign_keys= ON")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM owners where email= ?",("omedhar@gmail.com",))
    owner = cursor.fetchone()
    assert owner is not None
    owner_id = owner["id"]
    config_file = Path(__file__).parent / "building_configs.json"
    client.post("/create_all_appartments",params={"path":str(config_file)})
    client.patch(f"/owner/{owner_id}/appartments",params={"display_name":"106/22"})
    cursor.execute("SELECT * FROM appartments WHERE display_name= ?",("106/22",))
    apt_verify = cursor.fetchone()
    assert apt_verify["owner_id"] is not None
    cursor.execute("DELETE FROM owners WHERE id= ?",(owner_id,))
    connection.commit()
    cursor.execute("SELECT * FROM appartments WHERE display_name= ?",("106/22",))
    appartment = cursor.fetchone()
    assert appartment["owner_id"] == None

def test_owner_view_other_user(fresh_db):
    Connection = fresh_db
    Connection.execute("PRAGMA foreign_keys= ON")
    Connection.row_factory = sqlite3.Row
    cursor = Connection.cursor()
    owner_a = client.post("/owners",json={"name":"Omar","phone_number": "123456789","email":"omedhar@gmail.com","password":"SECRET_KEY"})
    logged_owner_a = client.post("/owners/login",data={"username":"omedhar@gmail.com","password":"SECRET_KEY"})
    assert logged_owner_a.status_code == 200
    token = logged_owner_a.json()["access_token"]
    get_owner_a = client.get("/owners",headers={"Authorization":f"Bearer {token}"})
    owner_id = get_owner_a.json()["id"]
    user_under_owner_a = client.post("/users",headers={"Authorization":f"Bearer {token}"},json={"name":"user","email":"user@example.com","phone_number":"54321","role":"tennant","password":"123456","owner_id":owner_id})
    assert user_under_owner_a.status_code == 200
    owner_b = client.post("/owners",json={"name":"ahmed","phone_number": "6666666789","email":"ahmed@gmail.com","password":"SECRET_KEY"}) 
    logged_owner_b = client.post("/owners/login",data={"username":"ahmed@gmail.com","password":"SECRET_KEY"})
    assert logged_owner_b.status_code == 200
    token_b = logged_owner_b.json()["access_token"]
    get_user_under_b = client.get("/owner/users",headers={"Authorization":f"Bearer {token_b}"})
    assert get_user_under_b.status_code == 200
    assert get_user_under_b.json() == []
    get_user_under_a = client.get("/owner/users",headers={"Authorization":f"Bearer {token}"})
    assert get_user_under_a.status_code == 200
    assert get_user_under_a.json() != []

def test_update_to_other_user(fresh_db):
    connection = fresh_db
    connection.execute("PRAGMA foreign_keys= ON")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    owner_a = client.post("/owners",json={"name":"Omar","phone_number": "123456789","email":"omedhar@gmail.com","password":"SECRET_KEY"})
    logged_owner_a = client.post("/owners/login",data={"username":"omedhar@gmail.com","password":"SECRET_KEY"})
    assert logged_owner_a.status_code == 200
    token = logged_owner_a.json()["access_token"]
    owner_b = client.post("/owners",json={"name":"ahmed","phone_number": "6666666789","email":"ahmed@gmail.com","password":"SECRET_KEY"}) 
    logged_owner_b = client.post("/owners/login",data={"username":"ahmed@gmail.com","password":"SECRET_KEY"})
    assert logged_owner_b.status_code == 200
    token_b = logged_owner_b.json()["access_token"]
    get_owner_a = client.get("/owners",headers={"Authorization":f"Bearer {token}"})
    get_owner_b = client.get("/owners",headers={"Authorization":f"Bearer {token_b}"})
    owner_a_id = get_owner_a.json()["id"]
    owner_b_id = get_owner_b.json()["id"]
    user_under_owner_a = client.post("/users",headers={"Authorization":f"Bearer {token}"},json={"name":"user","email":"user@example.com","phone_number":"54321","role":"tennant","password":"123456","owner_id":owner_a_id})
    assert user_under_owner_a.status_code == 200
    logged_user_a = client.post("/users/login",data={"username":"user@example.com","password":"123456"})
    assert logged_user_a.status_code == 200
    token_user_a = logged_user_a.json()["access_token"]
    get_user_a = client.get("/users",headers={"Authorization":f"Bearer {token_user_a}"})
    user_a_email = get_user_a.json()["email"]
    b_update_user_a = client.patch(f"/users/{user_a_email}",headers={"Authorization":f"Bearer {token_b}"},json={"name":"shada"})
    assert b_update_user_a.status_code == 401

def test_delete_other_owner_user(fresh_db):
    connection = fresh_db
    connection.execute("PRAGMA foreign_keys= ON")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor() 
    owner_a = client.post("/owners",json={"name":"Omar","phone_number": "123456789","email":"omedhar@gmail.com","password":"SECRET_KEY"})
    logged_owner_a = client.post("/owners/login",data={"username":"omedhar@gmail.com","password":"SECRET_KEY"})
    assert logged_owner_a.status_code == 200
    token = logged_owner_a.json()["access_token"]
    owner_b = client.post("/owners",json={"name":"ahmed","phone_number": "6666666789","email":"ahmed@gmail.com","password":"SECRET_KEY"}) 
    logged_owner_b = client.post("/owners/login",data={"username":"ahmed@gmail.com","password":"SECRET_KEY"})
    assert logged_owner_b.status_code == 200
    token_b = logged_owner_b.json()["access_token"]
    get_owner_a = client.get("/owners",headers={"Authorization":f"Bearer {token}"})
    get_owner_b = client.get("/owners",headers={"Authorization":f"Bearer {token_b}"})
    owner_a_id = get_owner_a.json()["id"]
    owner_b_id = get_owner_b.json()["id"]
    user_under_owner_a = client.post("/users",headers={"Authorization":f"Bearer {token}"},json={"name":"user","email":"user@example.com","phone_number":"54321","role":"tennant","password":"123456","owner_id":owner_a_id})
    assert user_under_owner_a.status_code == 200
    logged_user_a = client.post("/users/login",data={"username":"user@example.com","password":"123456"})
    assert logged_user_a.status_code == 200
    token_user_a = logged_user_a.json()["access_token"]
    get_user_a = client.get("/users",headers={"Authorization":f"Bearer {token_user_a}"})
    user_a_email = get_user_a.json()["email"]
    delete_user_a_by_owner_b = client.delete(f"/user/{user_a_email}",headers={"Authorization":f"Bearer {token_b}"})
    assert delete_user_a_by_owner_b.status_code == 401
