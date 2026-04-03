from fastapi import APIRouter, HTTPException
from app.models.schemas import DocumentUploadRequest
from app.services.db_ops import save_document, get_contract

router = APIRouter()

@router.post("/{contract_id}/upload")
async def upload_document(contract_id: str, request: DocumentUploadRequest):
    # Verify contract exists
    contract = get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
        
    data = {
        "document_url": request.document_url,
        "document_type": request.document_type,
        "uploaded_by": request.uploaded_by
    }
    
    saved = save_document(contract_id, data)
    if not saved:
        raise HTTPException(status_code=500, detail="Could not link document to contract")
        
    return {"message": "Document linked to contract successfully", "id": saved["id"]}
