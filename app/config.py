from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    sunat_env: str = "beta"
    sunat_ruc: str = ""
    sunat_usuario_sol: str = ""
    sunat_clave_sol: str = ""
    pfx_path: str = "./certificados/certificado.pfx"
    pfx_password: str = ""
    api_secret_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./sunat.db"

    @property
    def is_produccion(self) -> bool:
        return self.sunat_env.lower() == "produccion"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
