
import logging
import sys


class AppLogger:
    """
    Centralized logging configuration for the RAG service.

    All modules use this class instead of configuring
    their own logging handlers.

    Supports:
        DEBUG    - Detailed development information
        INFO     - Successful operations
        WARNING  - Unexpected but recoverable situations
        ERROR    - Failed operations
        EXCEPTION - Errors with traceback
    """

    LOG_FORMAT = (
        "%(asctime)s | %(levelname)-8s | "
        "%(name)s | %(message)s"
    )

    @classmethod
    def get_logger(
        cls,
        module_name: str
    ) -> logging.Logger:
        """
        Return a named logger using shared configuration.

        Args:
            module_name: Name of the calling Python module.

        Returns:
            Configured Python logger.
        """
        logger = logging.getLogger(module_name)

        # Configure a shared application handler only once.
        app_logger = logging.getLogger("app")

        if not app_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter(cls.LOG_FORMAT)
            )
            app_logger.addHandler(handler)
            app_logger.setLevel(logging.INFO)
            app_logger.propagate = False

        return logger
