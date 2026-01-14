import logging

from src.config import settings


def configure_logging():
    # Configure root logger
    logging.basicConfig(level=settings.log_level)
    # Configure module-specific log levels
    if settings.module_log_levels:
        for module_config in settings.module_log_levels.split(","):
            module_config = module_config.strip()
            if ":" in module_config:
                module_name, level = module_config.split(":", 1)
                logging.getLogger(module_name.strip()).setLevel(level.strip())
