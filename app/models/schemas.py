from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
import re

class EscrowCreateRequest(BaseModel):
    buyer_pubkey: str
    seller_pubkey: str
    arbiter_pubkey: str
    amount: int
    timelock_blocks: int

    @field_validator("buyer_pubkey", "seller_pubkey", "arbiter_pubkey")
    @classmethod
    def validate_pubkey(cls, v: str) -> str:
        if not re.fullmatch(r"[0-9a-fA-F]{66}", v):
            raise ValueError("Must be a valid 66-character hexadecimal compressed public key")
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "buyer_pubkey": "02e4827d041a84f3c059874c44896fea416db49187320c15383f069176378e1101",
                    "seller_pubkey": "035623091df887bed496e59aa123b08e503387b328734033b0068846c99c488801",
                    "arbiter_pubkey": "0295843b67975878415d862f1c8418f4adeee155d140e4f8abb7ec86e885d56220",
                    "amount": 100000,
                    "timelock_blocks": 144
                }
            ]
        }
    }

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
