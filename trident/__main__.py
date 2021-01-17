#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Main Module Runner

Called when the program is run from the command line.
@author: Jacob Wahlman
"""

import logging
import logging.config

import time
import traceback
from datetime import datetime

from trident.lib.parser.arguments import TridentArgumentParser
from trident.lib.parser.config import TridentConfigParser
from trident import TridentConfig, Trident
from trident import LOGGER_CONFIG

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger(__name__)


def apply_runtime_arguments(args, config) -> None:
    """ Applies arguments used in runtime: logging, ... """
    MODIFIED_LOGGER_CONFIG = LOGGER_CONFIG.copy()
    if config["logging_level"] not in MODIFIED_LOGGER_CONFIG["handlers"]:
        logger.warning(f"Unrecognized logging level: '{config['logging_level']}' given by config file, setting to 'INFO'.")
        config["logging_level"] = "INFO"

    MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]["handlers"] = [config["logging_level"]]
    MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]["level"] = config["logging_level"]

    if args.verbose:
        MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]["handlers"] = ["DEBUG"]
        MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]["level"] = "DEBUG"

    if args.quiet:
        del MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]

    logging.config.dictConfig(MODIFIED_LOGGER_CONFIG)


if __name__ == "__main__":
    try:
        trident_argument_parser = TridentArgumentParser()
    except Exception as e:
        logger.fatal(f"Trident argument parser failed with unrecoverable error: {e}")
        exit(1)

    try:
        trident_config_parser = TridentConfigParser(
            config_file_path=trident_argument_parser.args.config,
            config_file_section=trident_argument_parser.args.section
        )
    except Exception as e:
        logger.fatal(f"Trident config parser failed with unrecoverable error: {e}")
        exit(1)

    apply_runtime_arguments(trident_argument_parser.args, trident_config_parser.args)
    logger = logging.getLogger(__name__)

    _resulting_arguments = {**trident_config_parser.args, **vars(trident_argument_parser.args)}
    try:
        trident_config = TridentConfig(_resulting_arguments)
    except Exception as e:
        logger.error(f"Failed to initialize Trident config: {e}")
        raise e
    else:
        trident = Trident(trident_config)

    start_time = time.time()
    try:
        trident.start_trident_daemon()
    except KeyboardInterrupt:
        logger.warning("Interrupt signal sent, killing all plugins...")
        trident.shut_down_trident_daemon()
    except Exception as e:
        logger.fatal(f"Trident daemon failed with unrecoverable error: {e}")
        if _resulting_arguments.get("logging_level") == "DEBUG":
            traceback.print_exc()

    logger.info(f"Trident finished execution on: '{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}' after: '{round(time.time() - start_time, 5)}' seconds.")
