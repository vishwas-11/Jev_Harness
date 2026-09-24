from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from .config import get_settings
class Base(DeclarativeBase): pass
def database_url():
    s=get_settings()
    if s.supabase_db_url: return s.supabase_db_url
    p=Path(__file__).resolve().parents[1]/"data"/"jevscale.db"; p.parent.mkdir(parents=True,exist_ok=True)
    return f"sqlite:///{p.as_posix()}"
_url=database_url(); engine=create_engine(_url,connect_args={"check_same_thread":False} if _url.startswith("sqlite") else {},pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
def get_db():
    with SessionLocal() as db: yield db
def init_db():
    from . import models
    Base.metadata.create_all(bind=engine)
