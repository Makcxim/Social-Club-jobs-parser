try:
    from loguru import logger
except ImportError:
    import logging
    logging.basicConfig(
        level=logging.INFO
    )