"""日志模块"""

import logging
import colorama
import logzero
from logzero import setup_logger, LogFormatter

from .constants import LOG_DIR


class Logger:
    """统一的日志管理器"""

    def __init__(self, name: str, debug_mode: bool = False, log_file: bool = True):
        self.name = name
        self.debug_mode = debug_mode
        self.log_file = log_file
        self._logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        level = logzero.DEBUG if self.debug_mode else logzero.INFO

        colors = {
            logzero.DEBUG: colorama.Fore.CYAN,
            logzero.INFO: colorama.Fore.GREEN,
            logzero.WARNING: colorama.Fore.YELLOW,
            logzero.ERROR: colorama.Fore.RED,
            logzero.CRITICAL: colorama.Fore.MAGENTA,
        }

        terminal_formatter = LogFormatter(
            color=True,
            fmt="%(color)s%(message)s%(end_color)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            colors=colors,
        )

        logger = setup_logger(self.name, level=level, formatter=terminal_formatter)

        if self.log_file:
            LOG_DIR.mkdir(exist_ok=True)
            logfile = LOG_DIR / f"{self.name}.log"
            file_handler = logging.FileHandler(logfile, encoding="utf-8")
            file_formatter = logging.Formatter(
                "[%(asctime)s] | [%(name)s:%(levelname)s] | [%(module)s.%(funcName)s:%(lineno)d] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        return logger

    def debug(self, msg: str):
        self._logger.debug(msg)

    def info(self, msg: str):
        self._logger.info(msg)

    def warning(self, msg: str):
        self._logger.warning(msg)

    def error(self, msg: str):
        self._logger.error(msg)

    def critical(self, msg: str):
        self._logger.critical(msg)
