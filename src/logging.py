import os
import json
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "gateway.log")
SECURITY_LOG_FILE = os.path.join(LOG_DIR, "security.log")
MAX_LOG_LINES = 5000

_log_level = "INFO"


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def configure_logging():
    """Initialize gateway log storage."""
    _ensure_log_dir()
    return True


def get_log_level():
    return _log_level


def set_log_level(level):
    global _log_level

    level = str(level).upper()
    allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "SECURITY"}

    if level not in allowed:
        raise ValueError(f"Invalid log level: {level}")

    _log_level = level
    return _log_level


def _write_log(level, message, security=False):
    _ensure_log_dir()

    entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "level": level,
        "message": str(message),
    }

    path = SECURITY_LOG_FILE if security else LOG_FILE

    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")


def log_info(message):
    _write_log("INFO", message)


def log_warning(message):
    _write_log("WARNING", message)


def log_error(message):
    _write_log("ERROR", message)


def log_security_event(message):
    _write_log("SECURITY", message, security=True)


def _read_log_file(path, limit=500):
    if not os.path.exists(path):
        return []

    entries = []

    with open(path, "r", encoding="utf-8", errors="replace") as file:
        for line in file.readlines()[-limit:]:
            line = line.strip()
            if not line:
                continue

            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                entries.append({
                    "timestamp": None,
                    "level": "UNKNOWN",
                    "message": line,
                })

    return entries


def get_logs():
    """Return general and security logs."""
    return {
        "general": _read_log_file(LOG_FILE),
        "security": _read_log_file(SECURITY_LOG_FILE),
    }


def rotate_logs():
    """Keep only the newest MAX_LOG_LINES entries in each log."""
    _ensure_log_dir()

    for path in (LOG_FILE, SECURITY_LOG_FILE):
        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8", errors="replace") as file:
            lines = file.readlines()

        if len(lines) > MAX_LOG_LINES:
            lines = lines[-MAX_LOG_LINES:]

            with open(path, "w", encoding="utf-8") as file:
                file.writelines(lines)

    return True
