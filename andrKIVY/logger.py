import logging
import sys
import os
import tempfile
from pathlib import Path


def _get_log_dir():
    candidates = [
        os.environ.get("FASTMUSIC_DATA_DIR"),
        str(Path(__file__).parent / "logs"),
        os.path.join(tempfile.gettempdir(), "FastMusicLogs"),
    ]
    for c in candidates:
        if not c:
            continue
        try:
            p = Path(c)
            p.mkdir(parents=True, exist_ok=True)
            test = p / ".write_test"
            test.touch()
            test.unlink()
            return p
        except Exception:
            continue
    return None


_LOG_DIR = _get_log_dir()

_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)-7s %(name)s:%(lineno)d — %(message)s",
    datefmt="%H:%M:%S",
)

_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.INFO)
_ch.setFormatter(_formatter)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_ch)
    if _LOG_DIR is not None:
        try:
            _fh = logging.FileHandler(_LOG_DIR / "fastmusic.log", encoding="utf-8", mode="w")
            _fh.setLevel(logging.DEBUG)
            _fh.setFormatter(_formatter)
            logger.addHandler(_fh)
        except Exception:
            pass
    return logger
