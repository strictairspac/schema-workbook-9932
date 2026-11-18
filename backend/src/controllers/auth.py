from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from src.config.database import db_session
from src.models.entities import User,Audit
from src.utils.security import check_password,issue,current
router=APIRouter()
class Login(BaseModel):
    email:str=Field(max_length=120)
    password:str=Field(max_length=100)
@router.post('/auth/login')
def login(data:Login,db=Depends(db_session)):
    user=db.scalar(select(User).where(User.email==data.email))
    if not user or not check_password(data.password,user.password): raise HTTPException(401,'账号或密码不正确')
    db.add(Audit(actor=user.email,action='登录'));db.commit()
    return {'token':issue(user),'user':{'email':user.email,'role':user.role}}
@router.get('/auth/me')
def me(user=Depends(current)): return {'email':user.email,'role':user.role}
