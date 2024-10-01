import logging
import colorlog

LOG_FORMAT = '%(log_color)s[%(name)s][%(levelname)s]%(message)s'
LOG_COLORS = {
    'INFO': 'cyan',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'purple',
}

def init_log(level=logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger('Onekey')
    logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    fmt = colorlog.ColoredFormatter(LOG_FORMAT, log_colors=LOG_COLORS)
    stream_handler.setFormatter(fmt)

    # 避免重复添加处理器
    if not logger.handlers:
        logger.addHandler(stream_handler)

    return logger


log = init_log()
