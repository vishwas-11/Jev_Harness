from collections import Counter
from typing import Any
from .parser import DatasetRecord,ParsedDataset
from ..schemas import ValidationIssue,ValidationReport
def _s(v:Any): return "" if v is None else str(v)
def normalize_records(parsed,subject_column,body_column,ground_truth_columns=None,id_column=None):
    gt=ground_truth_columns or {}; out=[]
    for i,row in enumerate(parsed.rows,1):
        external_id=_s(row.get(id_column)) if id_column else _s(row.get("external_id",row.get("id",i)))
        truth={label:row.get(col) for label,col in gt.items() if col in row}
        metadata={k:v for k,v in row.items() if k not in {subject_column,body_column,id_column,*gt.values()}}
        out.append(DatasetRecord(external_id,_s(row.get(subject_column)),_s(row.get(body_column)),truth,metadata))
    return out
def validate_dataset(parsed,subject_column=None,body_column=None,ground_truth_columns=None,id_column=None):
    errors=[]; warnings=[]
    if not parsed.rows: errors.append(ValidationIssue(severity="error",code="empty_dataset",message="Dataset contains no records."))
    if subject_column and subject_column not in parsed.columns: errors.append(ValidationIssue(severity="error",code="missing_subject_column",message=f"Subject column '{subject_column}' was not found."))
    if body_column and body_column not in parsed.columns: errors.append(ValidationIssue(severity="error",code="missing_body_column",message=f"Body column '{body_column}' was not found."))
    for label,col in (ground_truth_columns or {}).items():
        if col and col not in parsed.columns: errors.append(ValidationIssue(severity="error",code="missing_ground_truth_column",message=f"Ground-truth column '{col}' for '{label}' was not found."))
    records=[]
    if not errors and subject_column and body_column:
        records=normalize_records(parsed,subject_column,body_column,ground_truth_columns,id_column)
        for ext,count in Counter(x.external_id for x in records).items():
            if count>1: errors.append(ValidationIssue(severity="error",code="duplicate_external_id",message=f"External ID '{ext}' appears {count} times."))
        for n,r in enumerate(records,1):
            if not r.subject.strip(): warnings.append(ValidationIssue(severity="warning",code="empty_subject",message="Record has an empty subject.",row=n))
            if not r.body.strip(): warnings.append(ValidationIssue(severity="warning",code="empty_body",message="Record has an empty body.",row=n))
    return ValidationReport(valid=not errors,errors=errors,warnings=warnings,record_count=len(parsed.rows),columns=parsed.columns),records
