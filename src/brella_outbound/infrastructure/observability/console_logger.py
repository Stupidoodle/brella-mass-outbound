"""Console logger implementation using structlog."""

from typing import Any

import structlog

from brella_outbound.domain.ports.logger_port import LoggerPort


class ConsoleLogger(LoggerPort):
    """Structlog-based console logger."""

    def __init__(self, name: str = "brella_outbound") -> None:
        self._logger = structlog.get_logger(name)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(message, **kwargs)

    def error(
        self,
        message: str,
        exc_info: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        """Log error message."""
        self._logger.error(message, exc_info=exc_info, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(message, **kwargs)
