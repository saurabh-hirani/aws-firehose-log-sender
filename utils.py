import logging
from datetime import datetime

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """ Custom json formatter for logging"""

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        if not log_record.get("timestamp"):
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now

        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


def setup_logging(name=None, fmt_string=None, log_level=None, critical_loggers=None):
    """ Setup logging """
    # Reset root level log handlers
    logging.getLogger().handlers = []

    # Reset current log handlers
    logger = logging.getLogger(name)
    logger.handlers = []

    if log_level is not None:
        log_level = getattr(logging, log_level)
    else:
        log_level = logging.INFO

    logger.setLevel(log_level)

    log_handler = logging.StreamHandler()

    if fmt_string is None:
        fmt_string = "%(level)s %(funcName)s %(lineno)s %(message)s"

    formatter = CustomJsonFormatter(fmt_string)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    if critical_loggers is None:
        critical_loggers = ["boto3", "botocore", "urllib3"]

    for lib_logger in critical_loggers:
        logging.getLogger(lib_logger).setLevel(logging.CRITICAL)

    return logger
