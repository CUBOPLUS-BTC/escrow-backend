from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from app.api.endpoints import escrow, psbt, documents
from app.services.nostr_listener import NostrListener

# Instancia global del listener (opcional, o se usa local)
nostr_listener = NostrListener()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arrancamos el bot en una tarea de fondo (background task) sin bloquear el backend
    bot_task = asyncio.create_task(nostr_listener.connect_and_listen())
    yield
    # Lógica de cierre (shutdown)
    bot_task.cancel()

app = FastAPI(title="Bitcoin Escrow Backend", version="1.0.0", lifespan=lifespan)

app.include_router(escrow.router, prefix="/api/escrow", tags=["Escrow"])
app.include_router(psbt.router, prefix="/api/psbt", tags=["PSBT"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Decentralized Escrow System API"}
