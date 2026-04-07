import os

VERSION_FILE = os.getenv("VERSION_FILE", "/app/VERSION")
BUILD_VERSION = os.getenv("BUILD_VERSION", "")

def get_version() -> str:
    if BUILD_VERSION:
        return BUILD_VERSION
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return "unknown"
