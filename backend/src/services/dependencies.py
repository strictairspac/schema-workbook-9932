from sqlalchemy import select,func
from fastapi import HTTPException
from src.models.entities import Relation,Dependency
from src.utils.serialization import record
from .common import save
from . import rules
def listing(db):return [record(x) for x in db.scalars(select(Dependency).order_by(Dependency.id))]
def validate(db,data,exclude=None):
    relation=db.get(Relation,data.relation_id)
    if not relation:raise HTTPException(404,'关系不存在')
    if not set(data.lhs+data.rhs)<=set(relation.attributes):raise HTTPException(422,'依赖属性必须属于选定关系')
    count=db.scalar(select(func.count()).select_from(Dependency).where(Dependency.relation_id==data.relation_id))
    if not exclude and count>=64:raise HTTPException(422,'最多64条函数依赖，请合并后重试')
def create(db,data,user):
    relation=rules.lock_relation(db,data.relation_id)
    if not relation:raise HTTPException(404,'关系不存在')
    validate(db,data)
    obj=Dependency(**data.model_dump());db.add(obj);db.flush()
    rules.sync_version(db,relation)
    return save(db,obj,user,'创建函数依赖')
def update(db,ident,data,user):
    obj=db.get(Dependency,ident)
    if not obj:raise HTTPException(404,'依赖不存在')
    relation_ids=sorted({obj.relation_id,data.relation_id})
    for relation_id in relation_ids:rules.lock_relation(db,relation_id)
    validate(db,data,ident)
    for k,v in data.model_dump().items():setattr(obj,k,v)
    db.flush()
    for relation_id in relation_ids:
        relation=db.get(Relation,relation_id)
        if relation:rules.sync_version(db,relation)
    return save(db,obj,user,'更新函数依赖')
