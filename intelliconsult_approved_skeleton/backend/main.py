from fastapi import FastAPI
from .contracts import ConsultRequest, ConsultReport
from .graph import consult
app=FastAPI(title='IntelliConsult AI',version='0.1.0')
@app.get('/health')
def health():return {'status':'ok','architecture':'fastapi-langgraph-hybrid'}
@app.post('/consult',response_model=ConsultReport)
def consult_endpoint(request:ConsultRequest):
    return consult(request.question)
