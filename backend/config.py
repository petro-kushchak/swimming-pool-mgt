import os


class Config:
    _instance = None

    def __init__(self):
        self.pools_config = os.getenv("POOLS_CONFIG", "/data/pools.json")
        self.scheduler_interval = int(os.getenv("SCHEDULER_INTERVAL", "60"))
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.build_version = os.getenv("BUILD_VERSION", "unknown")
        self.version_file = os.getenv("VERSION_FILE", "/app/VERSION")

    @classmethod
    def get_instance(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None


config = Config.get_instance()
