import traceback,json
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy import select
from src.config.database import Session
from src.models.entities import Report,DecompositionPlan,Relation,RuleVersion
from src.services.reports import queue
from src.services.normalization import analyze,verify_decomposition

PLAN_QUEUE='schemaworkbook:plan-queue'

def run_report(ident):
    with Session() as db:
        obj=db.get(Report,ident);obj.status='running';db.commit();snapshot=obj.input_snapshot
    result=analyze(snapshot['relation']['attributes'],snapshot['dependencies'])
    with Session() as db:
        obj=db.get(Report,ident);obj.result=result;obj.status='completed';db.commit()
    Path(f'/artifacts/report-{ident}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))

def run_plan(ident):
    with Session() as db:
        obj=db.get(DecompositionPlan,ident)
        if not obj:return
        obj.status='running';db.commit();snapshot=obj.input_snapshot
    result=verify_decomposition(snapshot['attributes'],snapshot['dependencies'],snapshot['fragments'])
    with Session() as db:
        obj=db.get(DecompositionPlan,ident)
        if not obj:return
        # Lock the rule version row: a concurrent rule edit either waits for this
        # commit (then marks the fresh verdict stale) or is already visible here.
        version=db.scalar(select(RuleVersion).where(RuleVersion.relation_id==obj.relation_id).with_for_update())
        current_epoch=version.epoch if version else 0
        result['rules_epoch']=snapshot.get('rules_epoch')
        result['current_rules_epoch']=current_epoch
        # A verdict that arrives after the rules changed is kept for the record of
        # the then-current rules, but it is stale for the present rules.
        if current_epoch!=snapshot.get('rules_epoch'):
            obj.status='stale';result['valid_for_current_rules']=False
            result['stale_reason']='核验完成前规则已变更，本结论仅对当时的规则语义（epoch %s）成立，不能标为当前有效。'%(snapshot.get('rules_epoch'),)
        else:
            obj.status=result['status'];result['valid_for_current_rules']=True
        obj.result=result;obj.completed_at=obj.completed_at or datetime.now(timezone.utc)
        db.commit()
    Path(f'/artifacts/plan-{ident}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))

def main():
    while True:
        Path('/tmp/worker-heartbeat').touch()
        item=queue.blpop(['schemaworkbook:queue',PLAN_QUEUE],timeout=2)
        if not item:continue
        name,raw=item
        try:
            ident=int(raw)
            if name==PLAN_QUEUE:run_plan(ident)
            else:run_report(ident)
        except Exception as e:
            traceback.print_exc()
            with Session() as db:
                if name==PLAN_QUEUE:
                    obj=db.get(DecompositionPlan,int(raw))
                    if obj:obj.status='failed';obj.error=str(e);db.commit()
                else:
                    obj=db.get(Report,int(raw))
                    if obj:obj.status='failed';obj.error=str(e);db.commit()

if __name__=='__main__':main()
