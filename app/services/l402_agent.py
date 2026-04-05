import logging
from pymacaroons import Macaroon, Verifier
from pymacaroons.exceptions import MacaroonInvalidSignatureException

logger = logging.getLogger(__name__)

class L402Agent:
    """
    Agente encargado de la emisión (minting) y validación de tokens L402 (Macaroons).
    """
    def __init__(self, root_key: str = "l402-secret-root-key-replace-in-production"):
        self.root_key = root_key
        self.location = "escrow-service"

    def mint_macaroon(self, payment_hash: str) -> str:
        """
        Crea un nuevo Macaroon y le adjunta el payment_hash como caveat.
        """
        macaroon = Macaroon(
            location=self.location,
            identifier=f"l402_token_{payment_hash[:8]}", # Identificador único del token (para DB/logs)
            key=self.root_key
        )
        
        # Agregamos el caveat (condición de pago)
        macaroon.add_first_party_caveat(f"payment_hash = {payment_hash}")
        
        logger.info(f"[L402] Minting macaroon vinculado al hash: {payment_hash[:8]}...")
        return macaroon.serialize()

    def verify_macaroon(self, macaroon_raw: str, payment_hash: str) -> bool:
        """
        Comprueba que la firma criptográfica sea válida y que el caveat
        coincida con el payment_hash proporcionado.
        """
        try:
            macaroon = Macaroon.deserialize(macaroon_raw)
            v = Verifier()
            
            # Verificamos que el caveat coincida exactamente con nuestro requerimiento
            v.satisfy_exact(f"payment_hash = {payment_hash}")
            
            # Valida la firma del Macaroon usando nuestra root_key secreta
            return v.verify(macaroon, self.root_key)
            
        except MacaroonInvalidSignatureException:
            logger.error("[L402] Firma de Macaroon inválida.")
            return False
        except Exception as e:
            logger.error(f"[L402] Error verificando Macaroon: {e}")
            return False

def _test():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    agent = L402Agent()
    mock_hash = "1234567890abcdef1234567890abcdef"
    wrong_hash = "invalid987654321invalid987654321"

    # 1. Crear el token
    token = agent.mint_macaroon(mock_hash)
    logger.info(f"Token Serializado: {token}")

    # 2. Verificación exitosa
    es_valido = agent.verify_macaroon(token, mock_hash)
    logger.info(f"Verificación con hash correcto: {'EXITOSA' if es_valido else 'FALLIDA'}")

    # 3. Verificación fallida
    es_valido_fallo = agent.verify_macaroon(token, wrong_hash)
    logger.info(f"Verificación con hash incorrecto: {'EXITOSA' if es_valido_fallo else 'FALLIDA'}")

if __name__ == "__main__":
    _test()
