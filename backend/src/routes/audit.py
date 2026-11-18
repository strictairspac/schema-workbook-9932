from fastapi import APIRouter,Depends
from sqlalchemy import select
from src.config.database import db_session
from src.utils.security import admin
from src.models.entities import Audit
from src.utils.serialization import record
router=APIRouter()
@router.get('/audit')
def audit(db=Depends(db_session),user=Depends(admin)): return [record(x) for x in db.scalars(select(Audit).order_by(Audit.id.desc()).limit(100))]
