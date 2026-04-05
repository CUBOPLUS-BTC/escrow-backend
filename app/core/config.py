from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    bitcoin_network: str = "testnet"
    mempool_api_url: str = "https://mempool.space/testnet/api"
    alby_hub_nwc: str = ""  # Opcional por ahora, string vacío por defecto si no está en el env
    nostr_private_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
