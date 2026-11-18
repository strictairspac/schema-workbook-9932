"""规则语义版本：同义改写不变更版本，含义变化则永久前进一步（不回退）。"""
from sqlalchemy import select
from src.models.entities import Relation,Dependency,RuleVersion,DecompositionPlan
from .normalization import semantic_fingerprint

def lock_relation(db,relation_id):
    """Lock the relation row so concurrent rule edits serialize per relation."""
    return db.execute(select(Relation).where(Relation.id==relation_id).with_for_update()).scalar_one_or_none()

def dependencies_of(db,relation_id):
    return [{'lhs':x.lhs,'rhs':x.rhs} for x in db.scalars(select(Dependency).where(Dependency.relation_id==relation_id).order_by(Dependency.id))]

def current_fingerprint(db,relation):
    return semantic_fingerprint(relation.attributes,dependencies_of(db,relation.id))

def sync_version(db,relation):
    """Bring the stored rule version in line with the current dependency meaning.

    Returns (epoch,fingerprint). Fingerprint equal to the stored one means the edit was
    an equivalent rewrite: the epoch stays put and existing verdicts remain valid.
    Otherwise the epoch advances monotonically; already-completed verdicts of that
    relation become outdated and stay that way even if the rules are later reverted.
    """
    version=db.scalar(select(RuleVersion).where(RuleVersion.relation_id==relation.id).with_for_update())
    fingerprint=current_fingerprint(db,relation)
    if version is None:
        version=RuleVersion(relation_id=relation.id,epoch=1,fingerprint=fingerprint)
        db.add(version);db.flush()
        return version.epoch,version.fingerprint
    if version.fingerprint!=fingerprint:
        version.epoch+=1;version.fingerprint=fingerprint
        db.flush()
        plans=db.scalars(select(DecompositionPlan).where(DecompositionPlan.relation_id==relation.id,DecompositionPlan.status.in_(('lossless','lossy')))).all()
        for plan in plans:
            plan.status='stale'
            if plan.result:
                updated=dict(plan.result)
                updated['current_rules_epoch']=version.epoch
                updated['valid_for_current_rules']=False
                updated['stale_reason']='规则含义已变化，本结论仅对当时的规则语义（epoch %s）成立，不能标为当前有效；改回规则也不恢复，需重新核验。'%plan.result.get('rules_epoch',plan.input_snapshot.get('rules_epoch') if plan.input_snapshot else None)
                plan.result=updated
        db.flush()
    return version.epoch,version.fingerprint

def current_epoch(db,relation):
    version=db.scalar(select(RuleVersion).where(RuleVersion.relation_id==relation.id))
    return version.epoch if version else 0


def ensure_versions(db):
    """Give every relation a baseline rule version so the first edit is detected."""
    known=set(db.scalars(select(RuleVersion.relation_id)))
    for relation in db.scalars(select(Relation)):
        if relation.id in known:continue
        db.add(RuleVersion(relation_id=relation.id,epoch=1,fingerprint=current_fingerprint(db,relation)))
    db.commit()
