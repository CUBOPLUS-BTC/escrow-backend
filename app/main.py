from fastapi import FastAPI
from app.api.endpoints import escrow, psbt, documents

app = FastAPI(title="Bitcoin Escrow Backend", version="1.0.0")

app.include_router(escrow.router, prefix="/api/escrow", tags=["Escrow"])
app.include_router(psbt.router, prefix="/api/psbt", tags=["PSBT"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Decentralized Escrow System API"}
