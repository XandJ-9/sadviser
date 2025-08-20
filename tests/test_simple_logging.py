import logging


def test_simple_logging():
    logger = logging.getLogger("simple_logger")
    try:
        1 / 0 
    except ZeroDivisionError:
        logger.error("An error occurred", exc_info=True)
        logger.exception("An error occurred")



if __name__ == '__main__':
    test_simple_logging()