from embit import script, networks
from app.core.config import settings

def create_escrow_script(buyer_pub: str, seller_pub: str, arbiter_pub: str, timelock: int) -> script.Script:
    """
    Creates a custom Redeem Script:
    OP_IF
        2 <buyer> <seller> <arbiter> 3 OP_CHECKMULTISIG
    OP_ELSE
        <timelock> OP_CHECKLOCKTIMEVERIFY OP_DROP
        <buyer> OP_CHECKSIG
    OP_ENDIF
    """
    buyer = bytes.fromhex(buyer_pub)
    seller = bytes.fromhex(seller_pub)
    arbiter = bytes.fromhex(arbiter_pub)
    
    # Build raw script bytes manually for maximum compatibility
    data = b"\x63" # OP_IF
    data += b"\x52" # OP_2
    data += b"\x21" + buyer
    data += b"\x21" + seller
    data += b"\x21" + arbiter
    data += b"\x53" # OP_3
    data += b"\xae" # OP_CHECKMULTISIG
    data += b"\x67" # OP_ELSE
    
    # Push timelock - handling as a script number
    # For small numbers under 16, we can use OP_1..OP_16 (0x51..0x60)
    # For simplicity and support for larger numbers, we push as minimal data
    from embit.compact import to_bytes
    if timelock <= 16:
        data += bytes([0x50 + timelock])
    else:
        # Pushing a script number (CScriptNum style)
        # Note: simplistic implementation for timelock pushes
        t_bytes = timelock.to_bytes((timelock.bit_length() + 8) // 8, 'little')
        data += bytes([len(t_bytes)]) + t_bytes

    data += b"\xb1" # OP_CHECKLOCKTIMEVERIFY
    data += b"\x75" # OP_DROP
    data += b"\x21" + buyer
    data += b"\xac" # OP_CHECKSIG
    data += b"\x68" # OP_ENDIF
    
    return script.Script(data)

def get_p2wsh_address(redeem_script: script.Script) -> str:
    """
    Takes a redeem script and returns its P2WSH address for the configured network.
    """
    net_name = settings.bitcoin_network
    if net_name == "testnet":
        net_name = "test"
    
    network = networks.NETWORKS[net_name]
    return script.p2wsh(redeem_script).address(network)

def combine_psbts(psbt_list: list) -> str:
    """
    Combines a list of PSBTs (base64 strings) and returns the combined PSBT.
    """
    from embit.psbt import PSBT
    
    if not psbt_list:
        return ""
        
    combined = PSBT.from_base64(psbt_list[0])
    for p in psbt_list[1:]:
        p_obj = PSBT.from_base64(p)
        # Attempt to combine signatures
        # Note: embit PSBT handles simple combination if structured properly
        for i, inp in enumerate(combined.inputs):
            inp.partial_sigs.update(p_obj.inputs[i].partial_sigs)
    
import httpx

def get_address_balance(address: str) -> dict:
    """
    Connects to mempool.space API to check UTXOs and total balance for the address.
    """
    url = f"{settings.mempool_api_url}/address/{address}"
    try:
        response = httpx.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Get balance: confirmed + unconfirmed
        chain_stats = data.get("chain_stats", {})
        mempool_stats = data.get("mempool_stats", {})
        
        confirmed = chain_stats.get("funded_txo_sum", 0) - chain_stats.get("spent_txo_sum", 0)
        unconfirmed = mempool_stats.get("funded_txo_sum", 0) - mempool_stats.get("spent_txo_sum", 0)
        
        return {
            "address": address,
            "confirmed_sats": confirmed,
            "unconfirmed_sats": unconfirmed,
            "total_sats": confirmed + unconfirmed
        }
    except Exception as e:
        # If API fails, return zeros or handle properly
        return {"address": address, "error": str(e), "total_sats": 0}

def get_address_utxos(address: str) -> list:
    """
    Returns a list of unspent transaction outputs (UTXOs) for the address.
    """
    url = f"{settings.mempool_api_url}/address/{address}/utxo"
    try:
        response = httpx.get(url)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []
