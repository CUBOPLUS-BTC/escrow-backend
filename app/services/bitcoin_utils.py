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
    
    # We create the script using embit's list of opcodes and data pushes
    s = script.Script([
        script.OP_IF,
        script.OP_2,
        buyer,
        seller,
        arbiter,
        script.OP_3,
        script.OP_CHECKMULTISIG,
        script.OP_ELSE,
        timelock, # This will be pushed as a scriptnum by embit automatically
        script.OP_CHECKLOCKTIMEVERIFY,
        script.OP_DROP,
        buyer,
        script.OP_CHECKSIG,
        script.OP_ENDIF
    ])
    return s

def get_p2wsh_address(redeem_script: script.Script) -> str:
    """
    Takes a redeem script and returns its P2WSH address for the configured network.
    """
    network = networks.NETWORKS[settings.bitcoin_network]
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
    
    return combined.to_base64()
