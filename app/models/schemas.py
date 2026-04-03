from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class EscrowCreateRequest(BaseModel):
    buyer_pubkey: str
    seller_pubkey: str
    arbiter_pubkey: str
    amount: int
    timelock_blocks: int

class EscrowResponse(BaseModel):
    id: UUID
    buyer_pubkey: str
    seller_pubkey: str
    arbiter_pubkey: str
    amount: int
    p2wsh_address: str
    redeem_script: str
    timelock_blocks: int
    status: str

class PSBTUploadRequest(BaseModel):
    psbt_base64: str
    signer_role: str # buyer, seller, arbiter

class DocumentUploadRequest(BaseModel):
    document_url: str
    document_type: str
    uploaded_by: str
