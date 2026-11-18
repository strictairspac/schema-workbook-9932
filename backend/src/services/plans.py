from sqlalchemy import select
from redis import Redis
from fastapi import HTTPException
from src.models.entities import Relation,DecompositionPlan
from src.config.settings import REDIS_URL
from src.constants.enums import PLAN_QUEUE
from src.utils.serialization import record
from .common import save
from . import rules
from .normalization import check_plan_input
queue=Redis.from_url(REDIS_URL,decode_responses=True)
def listing(db):return [record(x) for x in db.scalars(select(DecompositionPlan).order_by(DecompositionPlan.id.desc()))]
def detail(db,ident):
    obj=db.get(DecompositionPlan,ident)
    if not obj:raise HTTPException(404,'核验任务不存在')
    return record(obj)
def create(db,data,user):
    relation=rules.lock_relation(db,data.relation_id)
    if not relation:raise HTTPException(404,'关系不存在')
    dependencies=rules.dependencies_of(db,relation.id)
    epoch,fingerprint=rules.sync_version(db,relation)
    try:
        # 入队前先算一次覆盖校验，坏方案直接422，不让它占据核验队列。
        check_plan_input(relation.attributes,dependencies,data.fragments)
    except ValueError as error:
        raise HTTPException(422,str(error))
    snapshot={'relation':record(relation),'attributes':relation.attributes,'dependencies':dependencies,'fragments':data.fragments,'rules_epoch':epoch,'rules_fingerprint':fingerprint}
    obj=DecompositionPlan(**data.model_dump(),input_snapshot=snapshot,status='queued',rules_fingerprint=fingerprint)
    result=save(db,obj,user,'登记分表核验方案 '+data.name)
    try:queue.rpush(PLAN_QUEUE,str(obj.id))
    except Exception:
        obj.status='failed';obj.error='队列暂时不可用，请重新提交方案';db.commit();raise HTTPException(503,obj.error)
    return result
