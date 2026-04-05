from embit import script, networks
from app.core.config import settings
import httpx
import json

# ─────────────────────────────────────────────────────────────
#  Bitcoin Core JSON-RPC helper
# ─────────────────────────────────────────────────────────────

def _rpc_call(method: str, params=None, wallet: str = None) -> dict:
    """
    Calls Bitcoin Core JSON-RPC.
    If `wallet` is given, the URL is scoped to that wallet.
    """
    if params is None:
        params = []

    base = f"http://{settings.bitcoin_rpc_host}:{settings.bitcoin_rpc_port}"
    if wallet:
        url = f"{base}/wallet/{wallet}"
    elif settings.bitcoin_rpc_wallet:
        url = f"{base}/wallet/{settings.bitcoin_rpc_wallet}"
    else:
        url = base

    payload = {
        "jsonrpc": "1.0",
        "id": "escrow-backend",
        "method": method,
        "params": params,
    }

    rpc_user, rpc_password = settings.get_rpc_auth()

    response = httpx.post(
        url,
        json=payload,
        auth=(rpc_user, rpc_password),
        timeout=30.0,
    )
    data = response.json()

    if data.get("error"):
        raise Exception(f"RPC error ({method}): {data['error']}")

    return data["result"]

# ─────────────────────────────────────────────────────────────
#  Network helpers
# ─────────────────────────────────────────────────────────────

def _get_embit_network():
    """Returns the embit network object matching the current config."""
    net_name = settings.bitcoin_network
    if net_name == "testnet":
        net_name = "test"
    return networks.NETWORKS[net_name]

# ─────────────────────────────────────────────────────────────
#  Script / address creation
# ─────────────────────────────────────────────────────────────

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
    data = b"\x63"  # OP_IF
    data += b"\x52"  # OP_2
    data += b"\x21" + buyer
    data += b"\x21" + seller
    data += b"\x21" + arbiter
    data += b"\x53"  # OP_3
    data += b"\xae"  # OP_CHECKMULTISIG
    data += b"\x67"  # OP_ELSE

    # Push timelock as a script number
    if timelock <= 16:
        data += bytes([0x50 + timelock])
    else:
        t_bytes = timelock.to_bytes((timelock.bit_length() + 8) // 8, 'little')
        data += bytes([len(t_bytes)]) + t_bytes

    data += b"\xb1"  # OP_CHECKLOCKTIMEVERIFY
    data += b"\x75"  # OP_DROP
    data += b"\x21" + buyer
    data += b"\xac"  # OP_CHECKSIG
    data += b"\x68"  # OP_ENDIF

    return script.Script(data)

def get_p2wsh_address(redeem_script: script.Script) -> str:
    """
    Takes a redeem script and returns its P2WSH address for the configured network.
    """
    network = _get_embit_network()
    return script.p2wsh(redeem_script).address(network)

# ─────────────────────────────────────────────────────────────
#  Balance & UTXO queries via Bitcoin Core RPC
# ─────────────────────────────────────────────────────────────

def get_address_balance(address: str) -> dict:
    """
    Uses Bitcoin Core `scantxoutset` to check the total unspent balance
    for a given address.  Works in regtest without needing to import
    the address into any wallet.
    """
    try:
        result = _rpc_call("scantxoutset", ["start", [f"addr({address})"]])
        total_sats = int(result.get("total_amount", 0) * 1e8)
        return {
            "address": address,
            "confirmed_sats": total_sats,
            "unconfirmed_sats": 0,   # scantxoutset only sees confirmed
            "total_sats": total_sats,
        }
    except Exception as e:
        return {"address": address, "error": str(e), "total_sats": 0}


def get_address_utxos(address: str) -> list:
    """
    Uses Bitcoin Core `scantxoutset` to return UTXOs for an address.
    Returns a list matching the format the rest of the code expects:
        [{"txid": "...", "vout": N, "value": sats_int}, ...]
    """
    try:
        result = _rpc_call("scantxoutset", ["start", [f"addr({address})"]])
        utxos = []
        for u in result.get("unspents", []):
            utxos.append({
                "txid": u["txid"],
                "vout": u["vout"],
                "value": int(u["amount"] * 1e8),
            })
        return utxos
    except Exception:
        return []

# ─────────────────────────────────────────────────────────────
#  PSBT helpers
# ─────────────────────────────────────────────────────────────

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
        for i, inp in enumerate(combined.inputs):
            inp.partial_sigs.update(p_obj.inputs[i].partial_sigs)

    return combined.to_base64()

def create_psbt(contract: dict, destination_address: str, fee_sats: int = 1000) -> str:
    """
    Creates an unsigned PSBT (base64) spending UTXOs from the escrow P2WSH address
    to a destination address, after deducting the miner fee.

    Args:
        contract: dict with contract data from DB (must include p2wsh_address,
                  redeem_script, buyer_pubkey, seller_pubkey, arbiter_pubkey)
        destination_address: address to send funds to
        fee_sats: miner fee in satoshis
    Returns:
        base64-encoded PSBT string
    """
    from embit.psbt import PSBT, InputScope, OutputScope
    from embit.transaction import Transaction, TransactionInput, TransactionOutput
    from embit import script as sc

    # --- 1. Get network ---
    network = _get_embit_network()

    # --- 2. Fetch UTXOs for the escrow address ---
    utxos = get_address_utxos(contract["p2wsh_address"])
    if not utxos:
        raise ValueError(f"No UTXOs found for address {contract['p2wsh_address']}")

    total_input_sats = sum(u["value"] for u in utxos)
    output_sats = total_input_sats - fee_sats
    if output_sats <= 0:
        raise ValueError(f"Insufficient funds: {total_input_sats} sats, fee requested: {fee_sats} sats")

    # --- 3. Rebuild the redeem script from hex ---
    redeem_script = sc.Script(bytes.fromhex(contract["redeem_script"]))
    p2wsh_script = sc.p2wsh(redeem_script)  # the scriptPubKey on-chain

    # --- 4. Build the unsigned transaction ---
    tx_inputs = [
        TransactionInput(bytes.fromhex(u["txid"])[::-1], u["vout"])
        for u in utxos
    ]

    # Decode destination address to a scriptPubKey
    dest_script = sc.Script.from_address(destination_address)
    tx_outputs = [
        TransactionOutput(output_sats, dest_script)
    ]

    tx = Transaction(vin=tx_inputs, vout=tx_outputs)

    # --- 5. Build the PSBT ---
    psbt = PSBT(tx)

    # Attach witness UTXO and redeem script to each input so signers
    # know what they are spending and what script to satisfy
    for i, utxo in enumerate(utxos):
        inp = psbt.inputs[i]
        inp.witness_utxo = TransactionOutput(utxo["value"], p2wsh_script)
        inp.witness_script = redeem_script

    return psbt.to_base64()

# ─────────────────────────────────────────────────────────────
#  Broadcast a raw transaction via RPC
# ─────────────────────────────────────────────────────────────

def broadcast_transaction(raw_tx_hex: str) -> str:
    """
    Broadcasts a fully-signed raw transaction via Bitcoin Core RPC.
    Returns the txid on success.
    """
    return _rpc_call("sendrawtransaction", [raw_tx_hex])
