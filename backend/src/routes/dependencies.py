from fastapi import APIRouter,Depends
from src.config.database import db_session
from src.utils.security import current,writer
from src.schemas.dependency import DependencyInput
from src.services import dependencies as service
router=APIRouter()
@router.get('/dependencies')
def listing(db=Depends(db_session),user=Depends(current)):return service.listing(db)
@router.post('/dependencies',status_code=201)
def create(data:DependencyInput,db=Depends(db_session),user=Depends(writer)):return service.create(db,data,user)
@router.put('/dependencies/{ident}')
def update(ident:int,data:DependencyInput,db=Depends(db_session),user=Depends(writer)):return service.update(db,ident,data,user)
