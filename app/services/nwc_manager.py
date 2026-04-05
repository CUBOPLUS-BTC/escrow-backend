import asyncio
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class AlbyHubClient:
    """
    Cliente para comunicarse con Alby Hub a través de NIP-47 (Nostr Wallet Connect).
    (Versión Mock para la Fase 2 - Sprint 2)
    """
    def __init__(self, nwc_uri: Optional[str] = None):
        self.nwc_uri = nwc_uri or settings.alby_hub_nwc
        if not self.nwc_uri:
            logger.warning("[NWC] No se ha proporcionado una URI de NWC. Funcionando en modo MOCK estricto.")
        else:
            logger.info("[NWC] Alby Hub Client inicializado con NWC URI.")

    async def create_l402_invoice(self, amount_sats: int, description: str) -> Dict[str, Any]:
        """
        Solicita una nueva factura Lightning al Hub.
        Retorna el payment_request (invoice) y payment_hash.
        """
        logger.info(f"[NWC] Solicitando factura de {amount_sats} sats para: '{description}'")
        
        # Simulamos latencia de red
        await asyncio.sleep(1.0)
        
        # Datos mockeados
        mock_invoice = "lnbcc100n1pn...mock...invoice"
        mock_payment_hash = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        
        logger.info(f"[NWC] Factura generada con éxito. Hash: {mock_payment_hash[:8]}...")
        
        return {
            "payment_request": mock_invoice,
            "payment_hash": mock_payment_hash
        }

    async def check_invoice_status(self, payment_hash: str) -> Dict[str, Any]:
        """
        Verifica si una factura ha sido pagada.
        Retorna información incluyendo la preimage si está pagada.
        """
        logger.info(f"[NWC] Verificando estado de la factura: {payment_hash[:8]}...")
        
        # Simulamos latencia
        await asyncio.sleep(0.5)
        
        # Simulamos que siempre está pagada (para testing)
        mock_preimage = "preimage...mock...value"
        
        logger.info("[NWC] ¡Factura pagada!")
        
        return {
            "paid": True,
            "preimage": mock_preimage
        }

async def _test():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    client = AlbyHubClient()
    
    # 1. Crear factura
    invoice_data = await client.create_l402_invoice(50, "Test L402")
    
    # 2. Verificar pago
    status_data = await client.check_invoice_status(invoice_data["payment_hash"])
    print("Test Completado. Resultado:", status_data)

if __name__ == "__main__":
    asyncio.run(_test())
