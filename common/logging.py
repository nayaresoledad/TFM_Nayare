import logging
import json
from datetime import datetime, UTC
from logging.handlers import RotatingFileHandler

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.now(UTC).isoformat() + 'Z',
            'level': record.levelname,
            'module': record.module,
            'funcName': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(log_file: str = 'tfm_app.log', level: int = logging.INFO):
    logger = logging.getLogger('tfm')
    if logger.handlers:
        return logger

    logger.setLevel(level)

    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
