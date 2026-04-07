import os

from config import config


def get_version() -> str:
    if config.build_version and config.build_version != "unknown":
        return config.build_version
    if os.path.exists(config.version_file):
        with open(config.version_file, "r") as f:
            return f.read().strip()
    return "unknown"
