import os
import logging as log

class NullHandler(log.Handler):
    """Empty handler.
    """
    def emit(self, record):
        """Record a message.
        """
        pass
    
def debug_on():
    """Turn debugging logging on.
    """
    logging_on(log.DEBUG)

_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_is_logging_on = False
def logging_on(level=None):
    """Turn logging on.
    """
    global _is_logging_on

    if level == None:
        if os.environ.get("DEBUG", ''):
            level = log.DEBUG
        else:
            level = log.INFO

    if not _is_logging_on:
        console = log.StreamHandler()
        console.setFormatter(log.Formatter(_format, '%Y-%m-%d %H:%M:%S'))
        console.setLevel(level)
        log.getLogger('').addHandler(console)
        _is_logging_on = True

    logger = log.getLogger('')
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

def logging_off():
    """Turn logging off.
    """
    global _is_logging_on
    logger = log.getLogger('')
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)
    logger.handlers = [NullHandler()]
    _is_logging_on = False
    
def get_logger(name):
    """Return logger with null handle
    """
    
    logger = log.getLogger(name)
    if not logger.handlers:
        logger.addHandler(NullHandler())
    return logger
