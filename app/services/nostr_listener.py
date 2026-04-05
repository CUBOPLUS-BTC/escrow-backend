import asyncio
import logging
from typing import Optional
from nostr_sdk import Client, Keys, Filter, Kind, KindStandard, Event, NostrSigner, RelayUrl, HandleNotification
from app.services.nwc_manager import AlbyHubClient
from app.services.l402_agent import L402Agent
from app.core.config import settings

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NostrListener")

class NotificationHandler(HandleNotification):
    def __init__(self, nwc_client: AlbyHubClient, l402_agent: L402Agent):
        super().__init__()
        self.nwc_client = nwc_client
        self.l402_agent = l402_agent

    async def handle(self, relay_url: RelayUrl, subscription_id: str, event: Event):
        """
        Maneja eventos entrantes. En 0.44.2, handle recibe: relay_url, subscription_id, event.
        """
        try:
            kind_val = event.kind().as_u16()
            if kind_val == 1:
                content = event.content()
                logger.info(f"--- NUEVA NOTA (Kind 1) ---")
                logger.info(f"Autor: {event.author().to_bech32()}")
                logger.info(f"Contenido: {content}")
                
                # Sivar-Ad Protocol: Fase de Orquestación
                if "test_escrow" in content.lower():
                    logger.info("[ORCHESTRATOR] Palabra clave detectada. Iniciando Flujo L402...")
                    # 1. Crear Factura en Alby Hub (Mock)
                    invoice_data = await self.nwc_client.create_l402_invoice(100, "Cobro por servicio de maquinaria")
                    
                    # 2. Emitir Macaroon
                    payment_hash = invoice_data["payment_hash"]
                    macaroon = self.l402_agent.mint_macaroon(payment_hash)
                    
                    # 3. Presentar el L402 Challenge
                    payment_request = invoice_data["payment_request"]
                    logger.info(f"[ORCHESTRATOR] ✨ Reto L402 generado con éxito ✨")
                    logger.info(f"[L402] WWW-Authenticate: L402 macaroon=\"{macaroon}\", invoice=\"{payment_request}\"")
                
                logger.info(f"---------------------------")
        except Exception as e:
            logger.error(f"Error procesando evento: {e}")

    async def handle_msg(self, relay_url: RelayUrl, message):
        """
        Maneja mensajes de relay CRUD/Auth si fuera necesario.
        """
        pass

class NostrListener:
    def __init__(self, private_key_hex: Optional[str] = None):
        key_hex = private_key_hex or settings.nostr_private_key
        if key_hex:
            try:
                self.keys = Keys.parse(key_hex)
                logger.info("Keys cargadas desde configuración.")
            except Exception as e:
                logger.error(f"Error parseando NOSTR_PRIVATE_KEY: {e}. Generando nuevas...")
                self.keys = Keys.generate()
        else:
            self.keys = Keys.generate()
            logger.info(f"Nuevas Keys generadas: {self.keys.secret_key().to_bech32()}")
        
        signer = NostrSigner.keys(self.keys)
        self.client = Client(signer)
        
        # Inicializar servicios auxiliares (Sprint 2 y 3)
        self.nwc_client = AlbyHubClient()
        self.l402_agent = L402Agent()
        
    async def connect_and_listen(self):
        await self.client.add_relay(RelayUrl.parse("wss://relay.damus.io"))
        await self.client.add_relay(RelayUrl.parse("wss://nos.lol"))
        await self.client.add_relay(RelayUrl.parse("wss://relay.primal.net"))
        
        logger.info("Conectando...")
        await self.client.connect()
        
        f = Filter().kind(Kind.from_std(KindStandard.TEXT_NOTE)).limit(0)
        await self.client.subscribe(f, None)
        logger.info("=> Escuchando Kind 1...")
        
        # En 0.44.2 pasamos la instancia del handler
        handler = NotificationHandler(self.nwc_client, self.l402_agent)
        try:
            await self.client.handle_notifications(handler)
        except asyncio.CancelledError:
            logger.info("Listener detenido.")
        except Exception as e:
            logger.error(f"Error en handle_notifications: {e}")

if __name__ == "__main__":
    async def main_test():
        listener = NostrListener()
        await listener.connect_and_listen()

    try:
        asyncio.run(main_test())
    except KeyboardInterrupt:
        print("\nPrueba finalizada.")
