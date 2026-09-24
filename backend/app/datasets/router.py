from datetime import UTC,datetime
import json
from fastapi import APIRouter,Depends,File,Form,HTTPException,UploadFile,Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Dataset
from ..schemas import DatasetPreview,DatasetSummary,EmailPreview,InspectResponse,ValidationReport
from .service import DatasetService
from .repository import DatasetRepository
router=APIRouter(prefix="/api/datasets",tags=["datasets"])
def summary(d): return DatasetSummary(id=d.id,name=d.name,source_filename=d.source_filename,source_format=d.source_format,total_records=d.total_records,columns=d.columns_json,subject_column=d.subject_column,body_column=d.body_column,ground_truth_columns=d.ground_truth_columns or {},file_size=d.file_size,status=d.status,created_at=d.created_at,updated_at=d.updated_at)
def parse_gt(raw):
    if not raw: return {}
    try: value=json.loads(raw)
    except json.JSONDecodeError as e: raise HTTPException(422,"ground_truth_columns must be valid JSON") from e
    if not isinstance(value,dict): raise HTTPException(422,"ground_truth_columns must be an object")
    return {str(k):str(v) for k,v in value.items() if v}
@router.post("/inspect",response_model=InspectResponse)
async def inspect(file:UploadFile=File(...)):
    try: return DatasetService(None).inspect(file.filename or "upload",await file.read())
    except ValueError as e: raise HTTPException(422,str(e)) from e
@router.post("",response_model=DatasetSummary,status_code=201)
async def create(name:str=Form(...),subject_column:str=Form(...),body_column:str=Form(...),ground_truth_columns:str=Form("{}"),id_column:str|None=Form(None),file:UploadFile=File(...),db:Session=Depends(get_db)):
    try: dataset,report=DatasetService(db).create(name,file.filename or "upload",await file.read(),subject_column,body_column,parse_gt(ground_truth_columns),id_column)
    except ValueError as e: raise HTTPException(422,str(e)) from e
    if not report.valid: raise HTTPException(422,report.model_dump())
    return summary(dataset)
@router.get("",response_model=list[DatasetSummary])
def list_datasets(db:Session=Depends(get_db)): return [summary(d) for d in DatasetRepository(db).list()]
@router.get("/{dataset_id}",response_model=DatasetSummary)
def get_dataset(dataset_id:str,db:Session=Depends(get_db)):
    d=DatasetRepository(db).get(dataset_id)
    if not d: raise HTTPException(404,"Dataset not found")
    return summary(d)
@router.get("/{dataset_id}/preview",response_model=DatasetPreview)
def preview(dataset_id:str,page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),db:Session=Depends(get_db)):
    repo=DatasetRepository(db); d=repo.get(dataset_id)
    if not d: raise HTTPException(404,"Dataset not found")
    return DatasetPreview(dataset=summary(d),records=[EmailPreview(id=e.id,external_id=e.external_id,subject=e.subject,body=e.body,ground_truth=e.ground_truth or {},metadata=e.metadata_json or {}) for e in repo.preview(dataset_id,page,page_size)],page=page,page_size=page_size,total=repo.count(dataset_id))
@router.post("/{dataset_id}/validate",response_model=ValidationReport)
def validate(dataset_id:str,db:Session=Depends(get_db)):
    repo=DatasetRepository(db); d=repo.get(dataset_id)
    if not d: raise HTTPException(404,"Dataset not found")
    return ValidationReport(valid=d.status=="READY",errors=[] if d.status=="READY" else [{"severity":"error","code":"dataset_not_ready","message":"Dataset is not ready."}],warnings=[],record_count=repo.count(dataset_id),columns=d.columns_json)
@router.delete("/{dataset_id}",status_code=204)
def delete(dataset_id:str,db:Session=Depends(get_db)):
    repo=DatasetRepository(db); d=repo.get(dataset_id)
    if not d: raise HTTPException(404,"Dataset not found")
    repo.delete(d)
