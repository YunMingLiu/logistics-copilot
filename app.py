# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.query_handler import handle_query
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI()

class QueryRequest(BaseModel):
    question: str
    region: str = "default"
    app_version: str = "0.0.0"

@app.post("/ask")
def ask(req: QueryRequest):
    try:
        result = handle_query(req.question, {
            "region": req.region,
            "app_version": req.app_version
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)