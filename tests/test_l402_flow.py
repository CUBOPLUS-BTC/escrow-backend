import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from nostr_sdk import Event, Keys, Kind, KindStandard, RelayUrl, NostrSigner, EventBuilder
from app.services.nostr_listener import NotificationHandler
from app.services.nwc_manager import AlbyHubClient
from app.services.l402_agent import L402Agent

@pytest.mark.asyncio
class TestL402Flow:
    """
    Suite de pruebas de integración para validar que el Orquestador
    responde correctamente a los eventos de Nostr con desafíos L402.
    """
    
    @pytest.fixture
    def mock_services(self):
        # Mocks de los clientes externos
        nwc_mock = AsyncMock(spec=AlbyHubClient)
        l402_mock = MagicMock(spec=L402Agent)
        return nwc_mock, l402_mock

    @pytest.fixture
    def handler(self, mock_services):
        nwc_mock, l402_mock = mock_services
        return NotificationHandler(nwc_mock, l402_mock)

    @pytest.mark.asyncio
    async def test_handle_event_with_keyword(self, handler, mock_services):
        nwc_mock, l402_mock = mock_services
        
        # 1. Configurar Mocks
        nwc_mock.create_l402_invoice.return_value = {
            "payment_request": "ln1234567890abcdef",
            "payment_hash": "hash12345"
        }
        l402_mock.mint_macaroon.return_value = "macaroon-base64-token"

        # 2. Crear un evento simulado de Nostr mediante un Mock para no depender de EventBuilder
        event_mock = MagicMock()
        event_mock.kind.return_value.as_u16.return_value = 1
        event_mock.content.return_value = "Hacer un test_escrow ahora mismo"
        event_mock.author.return_value.to_bech32.return_value = "npub1mock..."
        
        # 3. Disparar el handler
        relay_url = RelayUrl.parse("wss://relay.damus.io")
        await handler.handle(relay_url, "sub-id-123", event_mock)

        # 4. Verificaciones (Assertions)
        # ¿Se llamó al creador de facturas?
        nwc_mock.create_l402_invoice.assert_called_once_with(100, "Cobro por servicio de maquinaria")
        
        # ¿Se llamó al emisor de Macaroons con el hash correcto?
        l402_mock.mint_macaroon.assert_called_once_with("hash12345")

    @pytest.mark.asyncio
    async def test_handle_event_without_keyword(self, handler, mock_services):
        nwc_mock, l402_mock = mock_services
        
        # 1. Crear un evento sin la palabra clave
        event_mock = MagicMock()
        event_mock.kind.return_value.as_u16.return_value = 1
        event_mock.content.return_value = "Hola mundo Nostr"
        event_mock.author.return_value.to_bech32.return_value = "npub1mock..."
        
        # 2. Disparar el handler
        relay_url = RelayUrl.parse("wss://relay.damus.io")
        await handler.handle(relay_url, "sub-id-123", event_mock)

        # 3. Verificaciones
        # No se debe haber llamado a ningún servicio de pago
        nwc_mock.create_l402_invoice.assert_not_called()
        l402_mock.mint_macaroon.assert_not_called()
