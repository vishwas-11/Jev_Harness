from datetime import datetime
from typing import Any
from pydantic import BaseModel,ConfigDict,Field
class ValidationIssue(BaseModel): severity:str; code:str; message:str; row:int|None=None
class ValidationReport(BaseModel): valid:bool; errors:list[ValidationIssue]=Field(default_factory=list); warnings:list[ValidationIssue]=Field(default_factory=list); record_count:int; columns:list[str]
class DatasetSummary(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:str; name:str; source_filename:str; source_format:str; total_records:int; columns:list[str]; subject_column:str; body_column:str; ground_truth_columns:dict[str,str]; file_size:int; status:str; created_at:datetime; updated_at:datetime
class EmailPreview(BaseModel): id:str; external_id:str; subject:str; body:str; ground_truth:dict[str,Any]; metadata:dict[str,Any]
class DatasetPreview(BaseModel): dataset:DatasetSummary; records:list[EmailPreview]; page:int; page_size:int; total:int
class InspectResponse(BaseModel): source_filename:str; source_format:str; file_size:int; columns:list[str]; sample_records:list[dict[str,Any]]; report:ValidationReport
