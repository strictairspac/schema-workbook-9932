from fastapi import APIRouter,Depends
from src.config.database import db_session
from src.utils.security import current,writer
from src.schemas.report import ReportInput
from src.services import reports as service
router=APIRouter()
@router.get('/reports')
def listing(db=Depends(db_session),user=Depends(current)):return service.listing(db)
@router.post('/reports',status_code=201)
def create(data:ReportInput,db=Depends(db_session),user=Depends(writer)):return service.create(db,data,user)
from fastapi.responses import Response
import json
@router.get('/reports/{ident}')
def detail(ident:int,db=Depends(db_session),user=Depends(current)):return service.detail(db,ident)
@router.get('/reports/{ident}/export')
def export(ident:int,db=Depends(db_session),user=Depends(current)):
    return Response(json.dumps(service.detail(db,ident),ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="report-{ident}.json"'})
