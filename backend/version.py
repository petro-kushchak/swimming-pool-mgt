from __future__ import annotations

import os

from config import settings


def get_version() -> str:
    if settings.build_version and settings.build_version != "unknown":
        return settings.build_version
    if os.path.exists(settings.version_file):
        with open(settings.version_file, "r") as f:
            return f.read().strip()
    return "unknown"
