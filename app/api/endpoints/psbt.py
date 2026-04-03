from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.models.schemas import PSBTUploadRequest
from app.services.db_ops import save_psbt, get_psbts
from app.services.bitcoin_utils import combine_psbts

router = APIRouter()

@router.post("/{contract_id}/upload")
async def upload_psbt(contract_id: str, request: PSBTUploadRequest):
    data = {
        "psbt_base64": request.psbt_base64,
        "signer_role": request.signer_role
    }
    saved = save_psbt(contract_id, data)
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to save PSBT")
    return {"message": "PSBT saved successfully", "id": saved["id"]}

@router.post("/{contract_id}/combine")
async def combine_contract_psbts(contract_id: str):
    psbts = get_psbts(contract_id)
    if not psbts:
        raise HTTPException(status_code=404, detail="No PSBTs found for contract")
        
    base64_list = [p["psbt_base64"] for p in psbts]
    try:
        combined = combine_psbts(base64_list)
        return {"combined_psbt": combined}
        # In a real app, this logic would also test if the transaction is fully 
        # signed and attempt to broadcast it via RPC / Mempool.space
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error combining PSBTs: {str(e)}")
