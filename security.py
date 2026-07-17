from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

SECURITY_KEY = os.getenv("TOKEN_SECURITY_KEY")
if SECURITY_KEY is None :
    raise RuntimeError("TOKEN_SECURITY_KEY is missing")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

def create_access_token(id:int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(id), "exp": expire}
    token = jwt.encode(payload,SECURITY_KEY,algorithm=ALGORITHM)
    return token

def verify_access_token(token:str) -> int:
    try:
        payload = jwt.decode(token,SECURITY_KEY,algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401,detail="Invalid token") 
        return int(user_id)
    except JWTError :
        raise HTTPException(status_code=401,detail="invalid token")
    