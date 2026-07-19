import sqlite3 
from fastapi import FastAPI , Depends , HTTPException
from pydantic import BaseModel , EmailStr
from apt_generator import apt_generator
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
import bcrypt
import security

app = FastAPI()
oauth2_scheme_owner = OAuth2PasswordBearer(tokenUrl="/owners/login",scheme_name="OwnerAuth")
oauth2_scheme_user = OAuth2PasswordBearer(tokenUrl="/users/login",scheme_name="UserAuth")

###HELPER_FUNCTIONS###
def get_db():
    connection = sqlite3.connect("community_project.db",check_same_thread=False)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    try :
        yield connection
    finally :
        connection.close()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"),salt)
    return hashed.decode("utf-8")

def authorize_owner(token:str= Depends(oauth2_scheme_owner),db:sqlite3.Connection= Depends(get_db)):
    user_id = security.verify_access_token(token)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM owners WHERE id= ?",(user_id,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=401,detail="User not found")
    return user

def authorize_user(token:str=Depends(oauth2_scheme_user),db:sqlite3.Connection=Depends(get_db)):
    user_id = security.verify_access_token(token)
    cursor = db.cursor()    
    cursor.execute("SELECT * FROM users WHERE id= ?",(user_id,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=401,detail="No user found")
    return user

###BASE_MODELS###

class CreateUser(BaseModel):
    name : str
    phone_number : str
    email : EmailStr
    password : str
    role : str

class UpdateUser(BaseModel):
    name : str | None = None
    phone_number : str | None = None
    email : EmailStr | None = None
    password : str | None = None

class Owners(BaseModel):
    name : str
    phone_number : str
    email : EmailStr
    password : str 

class UpdateOwners(BaseModel):
    name : str | None = None
    phone_number : str | None = None
    email : EmailStr | None = None
    password_hash : str | None = None


###CREATE_ENDPOINTS###

@app.post("/create_all_appartments")
def create_all_appartments(path:str,db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    appartments = apt_generator(path)
    for apt in appartments:
        apt_number = apt["apt_num"]
        floor = apt["floor"]
        building = apt["building"]
        display_name = apt["display_name"]
        cursor.execute("INSERT INTO appartments (appartment_number,building,floor,display_name) VALUES (?,?,?,?)",(apt_number,building,floor,display_name))
    db.commit()
    return f"Appartments added succsessfully"


@app.post("/user")
def create_user(data:CreateUser,current_owner=Depends(authorize_owner),db:sqlite3.Connection=Depends(get_db)):
    owner_id = current_owner["id"]
    password_hash = hash_password(data.password)
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users (name,phone_number,email,role,owner_id,password_hash) VALUES (?,?,?,?,?,?)",(data.name,data.phone_number,data.email,data.role,owner_id,password_hash))
        db.commit()
    except sqlite3.IntegrityError as e:
        if "users.phone_number" in str(e):
            raise HTTPException(status_code=409,detail="phone_number already exists")
        elif "users.email" in str(e):
            raise HTTPException(status_code=409,detail="email already exists")  
        else :
            raise HTTPException(status_code=409,detail="database constraint violated")
    return {"message": "User added successfully"}

@app.post("/owners")
def create_owner(owners :Owners,db:sqlite3.Connection=Depends(get_db)):
    hashed_pw = hash_password(owners.password)
    cursor = db.cursor()
    try :
        cursor.execute("INSERT INTO owners (name,phone_number,email,password_hash) VALUES (?,?,?,?)",(owners.name,owners.phone_number,owners.email,hashed_pw))
        db.commit()
    except sqlite3.IntegrityError as e:
        if "owners.phone_number" in str(e):
            raise HTTPException(status_code=409,detail="phone number already exists")
        elif "owners.email" in str(e):
            raise HTTPException(status_code=409,detail="email already exists")
        else :
            raise HTTPException(status_code=409,detail="Database constraint violation")
    return f"Owner created succsesfully"

###UPDATE_ENDPOINTS###

@app.patch("/users/{id}")
def update_user(id:int,form:UpdateUser,db:sqlite3.Connection= Depends(get_db)):
    data = form.model_dump(exclude_none=True)
    if not data :
        raise HTTPException(status_code=401,detail="No fields added")
    values = list(data.values())
    values.append(id)
    set_column = ", ".join(f"{column}= ?" for column in data)
    cursor = db.cursor()
    cursor.execute(f"UPDATE users SET {set_column} WHERE id= ?",values)
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=401,detail="No user found")
    return {"message":"User updated successfully"}

@app.patch("/owners/{id}")
def update_owner(id:int,data:UpdateOwners,db: sqlite3.Connection= Depends(get_db)):
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400,detail="No field provided for update")
    values = list(update_data.values())
    values.append(id)
    set_column = ", ".join(f"{column}= ?" for column in update_data)
    cursor = db.cursor()
    cursor.execute(f"UPDATE owners SET {set_column} WHERE id = ?",values)
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404,detail="No owner id found")
    db.commit()
    return {"message": "Updated successfully"}

@app.patch("/owner/{id}/appartments")
def update_owner_to_apt(id:int,display_name:str,db:sqlite3.Connection= Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("UPDATE appartments SET owner_id = ? WHERE display_name = ?",(id,display_name))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=400,detail="No owner id found")
    db.commit()

###DELETE_ENDPOINTS###

@app.delete("/delete/{id}")
def delete_owner(id:int,db:sqlite3.Connection= Depends(get_db)):
    cursor = db.cursor()    
    cursor.execute("DELETE FROM owners WHERE id = ?",(id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=400,detail="No owner id found")
    db.commit()
    return {"message": "Owner deleted successfully"}

@app.delete("/user/{email}")
def delete_user(email:str,current_owner=Depends(authorize_owner),db:sqlite3.Connection=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE from users WHERE email= ?",(email,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=401,detail="No user found")
    db.commit()
    return {"message": "User deleted successfully"}
    
###READ_ENDPOINTS###

@app.get("/owners")
def get_owner(current_owner=Depends(authorize_owner)):
    return current_owner

@app.get("/users")
def get_user(current_user= Depends(authorize_user)):
    return current_user

@app.get("/owner/users")
def get_owner_users(current_owner= Depends(authorize_owner),db:sqlite3.Connection= Depends(get_db)):
    cursor= db.cursor()
    owner_id = current_owner["id"]
    cursor.execute("SELECT owners.name AS owner_name, users.name AS user_name,users.role FROM owners JOIN users ON owners.id= users.owner_id WHERE owners.id= ?",(owner_id,))
    owner_users = cursor.fetchall()
    return owner_users

###LOGIN_ENDPOINTS###

@app.post("/owners/login")
def owner_login(form_data:OAuth2PasswordRequestForm= Depends(),db:sqlite3.Connection= Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM owners WHERE email= ?",(form_data.username,))
    owner = cursor.fetchone()
    if owner is None:
        raise HTTPException(status_code=401,detail="Invalid email or password")
    hashed_pw = owner["password_hash"]
    try :
        if not bcrypt.checkpw(form_data.password.encode("utf-8"),hashed_pw.encode("utf-8")):
            raise HTTPException(status_code=401,detail="Invalid password")
    except ValueError :
            raise HTTPException(status_code=401,detail="Invalid email or password")
    id = owner["id"]
    token = security.create_access_token(id)
    return {"access_token": token,"token_type": "Bearer"}

@app.post("/users/login")
def user_login(form_data:OAuth2PasswordRequestForm=Depends(),db:sqlite3.Connection=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email= ?",(form_data.username,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=401,detail="Invalid email or password") 
    hash_password =user["password_hash"]
    try:
        if not bcrypt.checkpw(form_data.password.encode(),hash_password.encode()):
            raise HTTPException(status_code=401,detail="invalid password")  
    except ValueError:
        raise HTTPException(status_code=401,detail="invalid password")
    id = user["id"] 
    token = security.create_access_token(id)
    return {"access_token": token,"token_type": "bearer"}


    

























































