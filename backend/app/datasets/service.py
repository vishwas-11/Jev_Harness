from uuid import uuid4
from sqlalchemy.orm import Session
from ..models import Dataset
from .parser import parse_dataset,sample_rows
from .validator import validate_dataset
from .repository import DatasetRepository
class DatasetService:
    def __init__(self,db:Session): self.repo=DatasetRepository(db)
    def inspect(self,filename,content):
        parsed=parse_dataset(filename,content); report,_=validate_dataset(parsed)
        return {"source_filename":filename,"source_format":parsed.source_format,"file_size":len(content),"columns":parsed.columns,"sample_records":sample_rows(parsed),"report":report}
    def create(self,name,filename,content,subject_column,body_column,ground_truth_columns=None,id_column=None):
        parsed=parse_dataset(filename,content); report,records=validate_dataset(parsed,subject_column,body_column,ground_truth_columns,id_column)
        if not report.valid: return None,report
        dataset=Dataset(id=str(uuid4()),name=name,source_filename=filename,source_format=parsed.source_format,total_records=len(records),columns_json=parsed.columns,subject_column=subject_column,body_column=body_column,ground_truth_columns=ground_truth_columns or {},file_size=len(content),status="READY")
        return self.repo.create(dataset,records),report
