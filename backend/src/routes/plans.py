from fastapi import APIRouter,Depends
from src.config.database import db_session
from src.utils.security import current,writer
from src.schemas.plan import PlanInput
from src.services import plans as service
router=APIRouter()
@router.get('/plans')
def listing(db=Depends(db_session),user=Depends(current)):return service.listing(db)
@router.post('/plans',status_code=201)
def create(data:PlanInput,db=Depends(db_session),user=Depends(writer)):return service.create(db,data,user)
@router.get('/plans/{ident}')
def detail(ident:int,db=Depends(db_session),user=Depends(current)):return service.detail(db,ident)
