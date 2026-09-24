from datetime import UTC,datetime
from sqlalchemy import DateTime,ForeignKey,Index,Integer,JSON,String,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .db import Base
def now_utc(): return datetime.now(UTC)
class Dataset(Base):
    __tablename__="datasets"
    id:Mapped[str]=mapped_column(String(36),primary_key=True)
    name:Mapped[str]=mapped_column(String(255),index=True)
    source_filename:Mapped[str]=mapped_column(String(255)); source_format:Mapped[str]=mapped_column(String(16))
    total_records:Mapped[int]=mapped_column(Integer,default=0); columns_json:Mapped[list]=mapped_column("columns",JSON,default=list)
    subject_column:Mapped[str]=mapped_column(String(255)); body_column:Mapped[str]=mapped_column(String(255)); ground_truth_columns:Mapped[dict]=mapped_column(JSON,default=dict)
    file_size:Mapped[int]=mapped_column(Integer,default=0); status:Mapped[str]=mapped_column(String(32),default="READY",index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now_utc); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now_utc,onupdate=now_utc)
    emails:Mapped[list["Email"]]=relationship(back_populates="dataset",cascade="all, delete-orphan")
class Email(Base):
    __tablename__="emails"
    id:Mapped[str]=mapped_column(String(80),primary_key=True); dataset_id:Mapped[str]=mapped_column(ForeignKey("datasets.id",ondelete="CASCADE"),index=True)
    external_id:Mapped[str]=mapped_column(String(255)); subject:Mapped[str]=mapped_column(Text,default=""); body:Mapped[str]=mapped_column(Text,default="")
    ground_truth:Mapped[dict]=mapped_column(JSON,default=dict); metadata_json:Mapped[dict]=mapped_column("metadata",JSON,default=dict); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now_utc)
    dataset:Mapped[Dataset]=relationship(back_populates="emails")
    __table_args__=(Index("ix_emails_dataset_external_id","dataset_id","external_id"),)
