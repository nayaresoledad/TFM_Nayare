import os
from dotenv import load_dotenv
from typing import Any, Dict

load_dotenv()

REQUIRED = [
    'POSTGRES_USER',
    'POSTGRES_PASSWORD',
    'POSTGRES_DB',
]

class ConfigError(Exception):
    pass

class Config:
    def __init__(self):
        self._env = os.environ
        self._validate()

    def _validate(self):
        missing = [v for v in REQUIRED if not self._env.get(v)]
        if missing:
            raise ConfigError(f"Variables de entorno requeridas faltan: {', '.join(missing)}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._env.get(key, default)

    @property
    def database_url(self) -> str:
        user = self.get('POSTGRES_USER')
        pwd = self.get('POSTGRES_PASSWORD')
        db = self.get('POSTGRES_DB')
        host = self.get('POSTGRES_HOST', 'localhost')
        port = self.get('POSTGRES_PORT', '5432')
        return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

config = Config()