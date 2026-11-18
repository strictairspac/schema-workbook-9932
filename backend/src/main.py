import os,logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from src.config.database import Base,engine
from src.models import entities
from src.controllers.auth import router as auth
from src.routes import relations,dependencies,reports,plans,audit
from src.middlewares.errors import ErrorMiddleware
from src.middlewares.request_id import RequestIdMiddleware
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    if os.getenv('SEED_DEMO','true')=='true':
        try:
            from scripts.seed_demo import seed
            seed()
        except Exception: logging.exception('seed failed; manual retry is available')
    try:
        from src.config.database import Session
        from src.services.rules import ensure_versions
        with Session() as db: ensure_versions(db)
    except Exception: logging.exception('rule-version baseline failed; it will be built on the next rule edit')
    yield
app=FastAPI(title='实验委托模型拆解册',lifespan=lifespan)
app.add_middleware(ErrorMiddleware);app.add_middleware(RequestIdMiddleware)
for r in (auth,relations.router,dependencies.router,reports.router,plans.router,audit.router): app.include_router(r)
@app.get('/health')
def health():
    with engine.connect() as c: c.execute(text('SELECT 1'))
    from src.services.reports import queue
    queue.ping()
    return {'status':'healthy'}
