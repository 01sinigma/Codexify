import logging
import os

_configured = False
_buffer = []

class _MemoryLogHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            _buffer.append(msg)
            # cap buffer ~10k lines
            if len(_buffer) > 10000:
                del _buffer[: len(_buffer) - 10000]
        except Exception:
            pass

def _ensure_handlers():
    global _configured
    if _configured:
        return
    log_level = logging.DEBUG if os.environ.get("CODEXIFY_DEBUG") == "1" else logging.INFO
    logging.basicConfig(level=log_level)

    mem_handler = _MemoryLogHandler(level=log_level)
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(mem_handler.formatter)

    root = logging.getLogger("codexify")
    root.setLevel(log_level)
    root.addHandler(mem_handler)
    root.addHandler(console)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    _ensure_handlers()
    return logging.getLogger(f"codexify.{name}")


def get_in_memory_logs() -> str:
    """Returns aggregated in-memory logs as a single string."""
    _ensure_handlers()
    return "\n".join(_buffer)

