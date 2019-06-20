import logging


class RiaLogger:
    log_format_info = '%(asctime)s %(levelname)s %(message)s'
    log_format_debug = '%(asctime)s.%(msecs)d %(levelname)s %(message)s'
    log_filename = 'ria.log'
    log_date_format = '%Y-%m-%d %H:%M:%S'
    logger = logging.getLogger("ria.run")

    @classmethod
    def log(cls, message, level='debug', suppress_stdout=False):
        if level == 'error':
            cls.logger.error(message)
        elif level == 'warn':
            cls.logger.warning(message)
        elif level == 'info':
            cls.logger.info(message)
        elif level == 'debug':
            cls.logger.debug(message)
        if not suppress_stdout:
            if message is not '':
                print(message)
