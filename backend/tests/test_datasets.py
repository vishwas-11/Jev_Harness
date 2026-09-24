import json
from backend.app.datasets.parser import DatasetParseError,parse_dataset
from backend.app.datasets.validator import validate_dataset

def test_csv_normalizes_and_warns_empty_subject():
    parsed=parse_dataset("mail.csv",b"id,subject,body,intent\n1,,hello,refund\n")
    report,records=validate_dataset(parsed,"subject","body",{"intent":"intent"},"id")
    assert report.valid and report.warnings[0].code=="empty_subject"
    assert records[0].external_id=="1" and records[0].ground_truth["intent"]=="refund"

def test_jsonl_malformed():
    try: parse_dataset("mail.jsonl",b'{"subject":"x"}\nnot-json\n')
    except DatasetParseError as e: assert "line 2" in str(e)
    else: raise AssertionError("expected parse error")

def test_duplicate_ids_fail():
    parsed=parse_dataset("mail.jsonl",b'{"id":"a","subject":"x","body":"y"}\n{"id":"a","subject":"z","body":"q"}\n')
    report,_=validate_dataset(parsed,"subject","body",{},"id")
    assert not report.valid and report.errors[0].code=="duplicate_external_id"
