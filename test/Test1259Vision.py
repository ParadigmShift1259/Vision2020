# Importing required modules
import logging.config


class Test1259Vision:
    # Read logging configuration file
    logging.config.fileConfig('logging.conf')

    # create logger
    logger = logging.getLogger('Test1259Vision')
    logger.debug("Info level message")
    logger.info("Info level message")