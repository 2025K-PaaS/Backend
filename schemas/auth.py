# schemas/auth.py

from typing import Annotated
from pydantic import BaseModel, Field

UsernameStr = Annotated[str, Field(min_length=3, max_length=50)]
PasswordStr = Annotated[str, Field(min_length=8, max_length=128)]
NameStr     = Annotated[str, Field(min_length=1, max_length=100)]
NickStr     = Annotated[str, Field(min_length=1, max_length=50)]

class SignUpIn(BaseModel):
    username: UsernameStr
    password: PasswordStr
    name: NameStr
    phone: str 
    nickname: NickStr 

class LoginIn(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = "bearer"
