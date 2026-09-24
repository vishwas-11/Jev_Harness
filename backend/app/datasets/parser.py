import csv,io,json
from dataclasses import dataclass,field
from typing import Any
FORMATS={"csv","jsonl","parquet"}
@dataclass
class DatasetRecord:
    external_id:str; subject:str; body:str; ground_truth:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict)
@dataclass
class ParsedDataset:
    source_format:str; columns:list[str]; rows:list[dict[str,Any]]
class DatasetParseError(ValueError): pass
def detect_format(filename):
    ext=filename.lower().rsplit(".",1)[-1] if "." in filename else ""
    if ext=="json": ext="jsonl"
    if ext not in FORMATS: raise DatasetParseError(f"Unsupported dataset format: .{ext or 'unknown'}")
    return ext
def parse_dataset(filename,content):
    fmt=detect_format(filename)
    if not content: raise DatasetParseError("The uploaded file is empty.")
    if fmt=="csv":
        try: text=content.decode("utf-8-sig")
        except UnicodeDecodeError: text=content.decode("latin-1")
        reader=csv.DictReader(io.StringIO(text))
        if not reader.fieldnames: raise DatasetParseError("CSV is missing a header row.")
        return ParsedDataset(fmt,[str(x) for x in reader.fieldnames],[dict(row) for row in reader])
    if fmt=="jsonl":
        rows=[]
        for n,line in enumerate(content.decode("utf-8-sig").splitlines(),1):
            if not line.strip(): continue
            try: value=json.loads(line)
            except json.JSONDecodeError as e: raise DatasetParseError(f"Malformed JSONL at line {n}: {e.msg}") from e
            if not isinstance(value,dict): raise DatasetParseError(f"JSONL line {n} must contain an object.")
            rows.append(value)
        return ParsedDataset(fmt,list(dict.fromkeys(k for row in rows for k in row)),rows)
    try:
        import pyarrow.parquet as pq
        table=pq.read_table(io.BytesIO(content)); return ParsedDataset(fmt,[str(x) for x in table.column_names],table.to_pylist())
    except Exception as e: raise DatasetParseError(f"Unable to read Parquet file: {e}") from e
def sample_rows(parsed,limit=10): return parsed.rows[:limit]
