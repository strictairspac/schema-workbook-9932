import hashlib,hmac,os,jwt
from datetime import datetime,timedelta,timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy import select
from src.config.settings import JWT_SECRET
from src.config.database import db_session
from src.models.entities import User
from src.constants.enums import ROLES
bearer=HTTPBearer()
def password_hash(value,salt=None):
    salt=salt or os.urandom(16).hex()
    return salt+':'+hashlib.pbkdf2_hmac('sha256',value.encode(),salt.encode(),180000).hex()
def check_password(value,encoded): return hmac.compare_digest(password_hash(value,encoded.split(':')[0]),encoded)
def issue(user): return jwt.encode({'sub':str(user.id),'exp':datetime.now(timezone.utc)+timedelta(hours=8)},JWT_SECRET,algorithm='HS256')
def current(token=Depends(bearer),db=Depends(db_session)):
    try:
        payload=jwt.decode(token.credentials,JWT_SECRET,algorithms=['HS256'])
        user=db.get(User,int(payload['sub']))
        if not user or user.role not in ROLES: raise ValueError()
        return user
    except Exception: raise HTTPException(401,'登录已过期，请重新登录')
def writer(user=Depends(current)):
    if user.role not in ('operator','admin'): raise HTTPException(403,'观察员仅可查看和导出')
    return user
def admin(user=Depends(current)):
    if user.role!='admin': raise HTTPException(403,'仅管理员可访问审计')
    return user
