import logging
import colorlog


def setupLogging():
    # Create a stream handler for console output.
    consoleHandler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] - %(levelname)s - %(name)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "white",
            "INFO": "green",
            "WARNING": "purple",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    consoleHandler.setFormatter(formatter)

    # Get the root logger, clear existing handlers, and add the colored console handler.
    rootLogger = colorlog.getLogger()
    rootLogger.handlers = []  # Remove old handlers if any.
    rootLogger.addHandler(consoleHandler)
    rootLogger.setLevel(logging.DEBUG)
