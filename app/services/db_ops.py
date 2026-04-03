from app.db.supabase import supabase
from typing import Dict, Any, List

def create_contract(data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("contracts").insert(data).execute()
    return res.data[0] if res.data else None

def get_contract(contract_id: str) -> Dict[str, Any]:
    res = supabase.table("contracts").select("*").eq("id", contract_id).execute()
    return res.data[0] if res.data else None

def save_document(contract_id: str, doc_data: Dict[str, Any]) -> Dict[str, Any]:
    doc_data["contract_id"] = contract_id
    res = supabase.table("documents").insert(doc_data).execute()
    return res.data[0] if res.data else None

def save_psbt(contract_id: str, psbt_data: Dict[str, Any]) -> Dict[str, Any]:
    psbt_data["contract_id"] = contract_id
    res = supabase.table("psbt_signatures").insert(psbt_data).execute()
    return res.data[0] if res.data else None

def get_psbts(contract_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("psbt_signatures").select("*").eq("contract_id", contract_id).execute()
    return res.data
