# ₿ Decentralized Escrow Backend

Backend para un Sistema de Escrow Descentralizado 2-de-3 sobre Bitcoin, diseñado para la importación de maquinaria pesada.

## Stack Tecnológico

- **Framework:** FastAPI (Python)
- **Base de Datos:** Supabase (PostgreSQL)
- **Bitcoin:** Scripts P2WSH nativos con `embit`, coordinación de PSBTs
- **Seguridad:** Non-custodial — el servidor **nunca** recibe ni almacena llaves privadas

## Arquitectura

```
app/
├── main.py                    # FastAPI app + routers
├── api/endpoints/
│   ├── escrow.py              # Crear/consultar contratos P2WSH
│   ├── psbt.py                # Upload y combinación de firmas
│   └── documents.py           # Pruebas de envío/logística
├── core/config.py             # Variables de entorno (pydantic-settings)
├── db/supabase.py             # Cliente Supabase
├── models/schemas.py          # Modelos Pydantic
└── services/
    ├── bitcoin_utils.py       # P2WSH, Timelock, PSBT
    └── db_ops.py              # CRUD Supabase
```

## Flujo del Escrow

1. **Creación:** Se reciben las pubkeys del Comprador, Vendedor y Árbitro (Aduana). Se genera un Redeem Script con multisig 2-de-3 + timelock de reembolso y su dirección P2WSH.
2. **Depósito:** El comprador deposita BTC en la dirección generada. El backend monitorea la confirmación.
3. **Envío:** El vendedor sube pruebas de logística y firma parcialmente (PSBT).
4. **Liberación:** El comprador confirma recepción y aporta su firma → el backend combina y transmite la TX.
5. **Disputa:** Si hay conflicto, el Árbitro (Aduana) aporta su firma para resolver.
6. **Timelock:** Si pasan N bloques sin actividad, el comprador puede reclamar un reembolso unilateral.

## Setup

```bash
cp .env.example .env
# Edita .env con tus credenciales de Supabase y configuración de red

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar tests de integración (Nostr/L402)
python -m pytest tests/test_l402_flow.py

# Ejecuta el schema SQL en tu proyecto Supabase (supabase_schema.sql)

fastapi dev app/main.py
```

Swagger UI disponible en `http://127.0.0.1:8000/docs`

## Licencia

MIT
