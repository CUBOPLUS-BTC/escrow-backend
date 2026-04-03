from fastapi import APIRouter, HTTPException
from app.models.schemas import EscrowCreateRequest, EscrowResponse
from app.services.bitcoin_utils import create_escrow_script, get_p2wsh_address
from app.services.db_ops import create_contract, get_contract

router = APIRouter()

@router.post("/create", response_model=EscrowResponse)
async def create_escrow(request: EscrowCreateRequest):
    try:
        # Create Redeem Script
        redeem_script = create_escrow_script(
            request.buyer_pubkey,
            request.seller_pubkey,
            request.arbiter_pubkey,
            request.timelock_blocks
        )
        
        # Get Address
        p2wsh_address = get_p2wsh_address(redeem_script)
        
        # Save to DB
        contract_data = {
            "buyer_pubkey": request.buyer_pubkey,
            "seller_pubkey": request.seller_pubkey,
            "arbiter_pubkey": request.arbiter_pubkey,
            "amount": request.amount,
            "p2wsh_address": p2wsh_address,
            "redeem_script": redeem_script.data.hex(),
            "timelock_blocks": request.timelock_blocks,
            "status": "pending"
        }
        
        created = create_contract(contract_data)
        if not created:
            raise HTTPException(status_code=500, detail="Database error")
            
        return created
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{contract_id}", response_model=EscrowResponse)
async def get_escrow(contract_id: str):
    contract = get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract
