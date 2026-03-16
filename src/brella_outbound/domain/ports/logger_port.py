"""Logger port interface."""

from abc import ABC, abstractmethod
from typing import Any


class LoggerPort(ABC):
    """Abstract logger interface."""

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        raise NotImplementedError

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        raise NotImplementedError

    @abstractmethod
    def error(
        self,
        message: str,
        exc_info: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        """Log error message."""
        raise NotImplementedError

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        raise NotImplementedError
