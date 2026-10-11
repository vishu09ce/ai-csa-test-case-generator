import logging
import os
import socket

# host and pid in every line so logs from different Render instances can be told apart
_FORMAT = f"%(asctime)s %(levelname)s [{socket.gethostname()} pid=%(process)d] %(name)s: %(message)s"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
        logger.propagate = False
    return logger


def describe_path(path: str) -> str:
    """Absolute path plus whether it exists and its size, for log lines."""
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        return f"{abs_path} (exists, {os.path.getsize(abs_path)} bytes)"
    return f"{abs_path} (MISSING)"
