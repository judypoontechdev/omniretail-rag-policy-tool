import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional

from core.extractor import extract_inquiry_details
from core.rag_engine import run_rag_pipeline

app = FastAPI(
    title="OmniRetail UK Operational RAG Service",
    version="1.0.0",
    description="Compliance-enforced retail assistant with policy verification and gap detection."
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class InquiryRequest(BaseModel):
    query: str = Field(..., example="Can I get an extra 10% manual discount on my cart?")
    order_id: Optional[str] = Field(default=None, example="OMNI-1001")

@app.get("/")
def serve_ui():
    """Serves the simple HTML interface."""
    html_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"status": "healthy", "service": "OmniRetail UK Operations AI"}

@app.post("/api/inquire")
def handle_customer_inquiry(payload: InquiryRequest):
    """
    Main resolution endpoint: extracts intent, verifies against policy store,
    performs order fact lookup, and generates compliance-enforced resolution.
    """
    try:
        inquiry_obj = extract_inquiry_details(payload.query)
        if payload.order_id and not inquiry_obj.order_id:
            inquiry_obj.order_id = payload.order_id

        result = run_rag_pipeline(inquiry_obj)

        return {
            "order_id": result["order_id"],
            "category": result["category"],
            "decision": result["decision"],
            "matched_sections": result["matched_sections"],
            "gap_detected": result["gap_detected"],
            "final_answer": result["final_answer"],
            "order_details": result["order_info"]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)