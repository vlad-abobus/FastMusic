import logging
import sys
import os
from pathlib import Path


def _get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).parent


_LOG_DIR = _get_base_dir() / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / "fastmusic.log"

_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)-7s %(name)s:%(lineno)d — %(message)s",
    datefmt="%H:%M:%S",
)

_fh = logging.FileHandler(_LOG_FILE, encoding="utf-8", mode="w")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(_formatter)

_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.INFO)
_ch.setFormatter(_formatter)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_fh)
    logger.addHandler(_ch)
    return logger
