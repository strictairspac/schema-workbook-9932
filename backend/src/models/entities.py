from sqlalchemy import Column,Integer,String,JSON,DateTime,ForeignKey,Text
from datetime import datetime,timezone
from src.config.database import Base
class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True);email=Column(String(120),unique=True,nullable=False);password=Column(String(300),nullable=False);role=Column(String(20),nullable=False)
class Relation(Base):
    __tablename__='relations'
    id=Column(Integer,primary_key=True);code=Column(String(80),unique=True,nullable=False);title=Column(String(160),nullable=False);attributes=Column(JSON,nullable=False);note=Column(String(300),default='')
class Dependency(Base):
    __tablename__='dependencies'
    id=Column(Integer,primary_key=True);relation_id=Column(Integer,ForeignKey('relations.id'),nullable=False);lhs=Column(JSON,nullable=False);rhs=Column(JSON,nullable=False);note=Column(String(300),default='')
class Report(Base):
    __tablename__='reports'
    id=Column(Integer,primary_key=True);name=Column(String(120),nullable=False);relation_id=Column(Integer,ForeignKey('relations.id'),nullable=False)
    status=Column(String(20),nullable=False,default='queued');input_snapshot=Column(JSON,nullable=False);result=Column(JSON,nullable=True);error=Column(Text,nullable=True)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class RuleVersion(Base):
    """每条关系的规则语义版本：epoch只增不减，fingerprint是F+闭包的哈希。"""
    __tablename__='rule_versions'
    id=Column(Integer,primary_key=True)
    relation_id=Column(Integer,ForeignKey('relations.id'),unique=True,nullable=False)
    epoch=Column(Integer,nullable=False,default=1)
    fingerprint=Column(String(64),nullable=False)
class DecompositionPlan(Base):
    """供应商给出的分表方案：待核验的候选分解，核验结果随规则语义变化而失效。"""
    __tablename__='decomposition_plans'
    id=Column(Integer,primary_key=True)
    name=Column(String(120),nullable=False)
    relation_id=Column(Integer,ForeignKey('relations.id'),nullable=False)
    status=Column(String(20),nullable=False,default='queued')
    input_snapshot=Column(JSON,nullable=False)
    fragments=Column(JSON,nullable=False)
    rules_fingerprint=Column(String(64),nullable=False)
    result=Column(JSON,nullable=True)
    error=Column(Text,nullable=True)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    completed_at=Column(DateTime(timezone=True),nullable=True)
class Audit(Base):
    __tablename__='audit_logs'
    id=Column(Integer,primary_key=True);actor=Column(String(120),nullable=False);action=Column(String(160),nullable=False);created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
