from fastapi.testclient import TestClient
from backend.app.main import app
client=TestClient(app)
def test_health(): assert client.get("/api/health").status_code==200
def test_upload_list_preview_delete():
    payload={"name":"Support sample","subject_column":"subject","body_column":"body","ground_truth_columns":'{"intent":"intent"}'}
    response=client.post("/api/datasets",data=payload,files={"file":("mail.csv",b"id,subject,body,intent\na,Refund,Please help,refund\n","text/csv")})
    assert response.status_code==201,response.text
    dataset=response.json(); assert dataset["total_records"]==1
    assert client.get("/api/datasets").json()[0]["id"]==dataset["id"]
    preview=client.get(f"/api/datasets/{dataset['id']}/preview").json(); assert preview["records"][0]["ground_truth"]["intent"]=="refund"
    assert client.delete(f"/api/datasets/{dataset['id']}").status_code==204

