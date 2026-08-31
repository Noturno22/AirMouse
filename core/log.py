"""Structured logging for AirMouse.

Single logger tree (``airmouse``) with console + rotating file output.
The file lands in ``%LOCALAPPDATA%\\AirMouse\\logs\\airmouse.log`` on Windows
(or ``./logs`` when LOCALAPPDATA is unavailable), which survives across
runs and keeps the console clean.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOGGER_NAME = "airmouse"
DEFAULT_LEVEL = logging.INFO

log = logging.getLogger(LOGGER_NAME)

_FMT = "%(asctime)s %(levelname)-5s %(name)s: %(message)s"


def _log_dir():
    base = os.environ.get("LOCALAPPDATA")
    if base:
        path = os.path.join(base, "AirMouse", "logs")
    else:
        path = os.path.join(".", "logs")
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except OSError:
        return "."


def setup_logging(level=DEFAULT_LEVEL, console=True, log_file=None):
    """Configura handlers do logger raiz ``airmouse``. Idempotente."""
    log.setLevel(level)
    for h in list(log.handlers):
        log.removeHandler(h)
    log.propagate = False

    fmt = logging.Formatter(_FMT, datefmt="%Y-%m-%d %H:%M:%S")
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(fmt)
        log.addHandler(ch)
    if log_file is None:
        log_file = os.path.join(_log_dir(), "airmouse.log")
    fh = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8",
    )
    fh.setLevel(level)
    fh.setFormatter(fmt)
    log.addHandler(fh)
    return log


def get_logger(name=""):
    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return log
