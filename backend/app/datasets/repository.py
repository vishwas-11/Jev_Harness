from sqlalchemy import func,select
from sqlalchemy.orm import Session
from ..models import Dataset,Email
class DatasetRepository:
    def __init__(self,db:Session): self.db=db
    def list(self): return list(self.db.scalars(select(Dataset).order_by(Dataset.created_at.desc())).all())
    def get(self,id): return self.db.get(Dataset,id)
    def count(self,id): return int(self.db.scalar(select(func.count()).select_from(Email).where(Email.dataset_id==id)) or 0)
    def preview(self,id,page,size): return list(self.db.scalars(select(Email).where(Email.dataset_id==id).order_by(Email.created_at,Email.id).offset((page-1)*size).limit(size)).all())
    def create(self,dataset,records):
        self.db.add(dataset); self.db.flush(); self.db.add_all([Email(id=f"{dataset.id}:{i}",dataset_id=dataset.id,external_id=r.external_id,subject=r.subject,body=r.body,ground_truth=r.ground_truth,metadata_json=r.metadata) for i,r in enumerate(records,1)]); self.db.commit(); self.db.refresh(dataset); return dataset
    def delete(self,dataset): self.db.delete(dataset); self.db.commit()
