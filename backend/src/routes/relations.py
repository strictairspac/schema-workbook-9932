from fastapi import APIRouter,Depends
from src.config.database import db_session
from src.utils.security import current,writer
from src.schemas.relation import RelationInput
from src.services import relations as service
router=APIRouter()
@router.get('/relations')
def listing(db=Depends(db_session),user=Depends(current)):return service.listing(db)
@router.post('/relations',status_code=201)
def create(data:RelationInput,db=Depends(db_session),user=Depends(writer)):return service.create(db,data,user)
@router.put('/relations/{ident}')
def update(ident:int,data:RelationInput,db=Depends(db_session),user=Depends(writer)):return service.update(db,ident,data,user)
