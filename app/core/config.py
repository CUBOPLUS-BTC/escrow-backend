from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    bitcoin_network: str = "regtest"
    bitcoin_rpc_host: str = "127.0.0.1"
    bitcoin_rpc_port: int = 18443
    bitcoin_rpc_wallet: str = ""
    # Path to the .cookie file. If set, this is used for auth instead of user/password.
    bitcoin_rpc_cookie_path: str = ""
    # Fallback user/password if cookie is not used
    bitcoin_rpc_user: str = ""
    bitcoin_rpc_password: str = ""

    model_config = SettingsConfigDict(env_file=".env")

    def get_rpc_auth(self) -> tuple[str, str]:
        """
        Returns (user, password) for RPC authentication.
        Reads the cookie file if configured; otherwise falls back to user/password.
        The cookie file is re-read every time because bitcoind regenerates it on restart.
        """
        if self.bitcoin_rpc_cookie_path:
            try:
                with open(self.bitcoin_rpc_cookie_path, "r") as f:
                    cookie = f.read().strip()
                user, password = cookie.split(":", 1)
                return user, password
            except Exception:
                pass  # Fall through to user/password
        return self.bitcoin_rpc_user, self.bitcoin_rpc_password

    @property
    def rpc_url(self) -> str:
        base = f"http://{self.bitcoin_rpc_host}:{self.bitcoin_rpc_port}"
        if self.bitcoin_rpc_wallet:
            return f"{base}/wallet/{self.bitcoin_rpc_wallet}"
        return base


settings = Settings()
