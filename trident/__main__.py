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

from typing import Dict, AnyStr, NewType, Union
Namespace = NewType("Namespace", None)

from trident.lib.parser.arguments import TridentArgumentParser
from trident.lib.parser.config import TridentConfigParser
from trident import TridentConfig, Trident
from trident import LOGGER_CONFIG

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger(__name__)


def setup_logging(args: Namespace, config: Dict[AnyStr, Union[AnyStr, Dict]]) -> None:
    """ Selects the behavior of the logging that the program uses from the arguments and the config passed to the program.

    :param args: Config passed as arguments to the program.
    :type args: :class:`Namespace`
    :param config: Config passed through the config section chosen.
    :type config: dict
    """
    MODIFIED_LOGGER_CONFIG = LOGGER_CONFIG.copy()
    if config["logging_level"] not in MODIFIED_LOGGER_CONFIG["handlers"]:
        logger.warning(f"Unrecognized logging level: '{config['logging_level']}' given by config file, setting to 'INFO'.")
        config["logging_level"] = "INFO"

    MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]["handlers"] = [config["logging_level"]]
    MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]["level"] = config["logging_level"]

    if args.verbose or ("verbose" in config["args"]["trident"] and config["args"]["trident"]["verbose"]):
        MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]["handlers"] = ["DEBUG"]
        MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]["level"] = "DEBUG"

    if args.quiet or ("quiet" in config["args"]["trident"] and config["args"]["trident"]["quiet"]):
        del MODIFIED_LOGGER_CONFIG["loggers"]["__main__"]

    logging.config.dictConfig(MODIFIED_LOGGER_CONFIG)

def validate_config(config: Dict[AnyStr, Dict]) -> Dict[AnyStr, Dict]:
    """ Validate that the config contains the necessary options.
    If it doesn't then add the default values for missing options.

    :param config: Config passed as arguments to the program.
    :type config: dict
    :return: The modified config.
    :rtype: dict
    """
    for plugin_id, plugin_config in config["plugins"].items():
        if not plugin_config["args"]["store"] and ("no_store" not in plugin_config["args"]["store"] or not plugin_config["args"]["store"]["no_store"]):
            logger.warning(f"No 'store' args were specified for: '{plugin_id}', setting default values")
            
            if "global_store" not in plugin_config["args"]["store"]:
                logger.warning(f"Setting path for stores to 'data'")
                plugin_config["args"]["store"]["path_store"] = "data"

    if not config["args"]["daemon"]:
        logger.warning(f"No 'daemon' args were specified, setting default values")
        logger.warning(f"Setting worker count to '5'")
        config["args"]["daemon"] = {
            "workers": 5
        }

    return config

def setup_plugin_arguments(args: Dict[AnyStr, AnyStr], config: Dict[AnyStr, Dict]) -> Dict[AnyStr, Dict]:
    """ Setup the arguments for each plugin, if any arguments related to plugins are defined in the arguments
    then those arguments will override/add the value in the config.

    :param args: Config passed as arguments to the program.
    :type args: dict
    :param config: Config passed through the config section chosen.
    :type config: dict
    :return: The modified plugin config.
    :rtype: dict
    """
    for plugin_id, plugin_config in config["plugins"].items():
        if "args" in config:
            if "args" not in plugin_config:
                    plugin_config["args"] = {
                        "store": {},
                        "runner": {},
                        "notification": {}
                    }
            
            # Store and runner existence are necessary for the validation
            for category in ["store", "runner", "notification"]:
                if category not in plugin_config["args"]:
                    plugin_config["args"][category] = {}

            for section in config["args"]:
                if section not in ["store", "runner"]:
                    continue

                if section not in plugin_config["args"]:
                    plugin_config["args"][section] = {}
                
                for arg, value in config["args"][section].items():
                    # Don't overwrite values set in the specific plugin config if the arg is already defined.
                    if arg in plugin_config["args"][section]:
                        continue

                    plugin_config["args"][section][arg] = value
        else:
            config["args"] = {
               "daemon": {}
            }

        for section, value in args.items():
            if not value:
                continue
            
            if section not in plugin_config["args"]:
                plugin_config["args"][section] = {}

            plugin_config["args"][section].update(value)

    return config

def setup_daemon_arguments(args: Dict[AnyStr, AnyStr], config: Dict[AnyStr, Dict]) -> Dict[AnyStr, Dict]:
    """ Setup the arguments for the daemon, if any arguments related to the daemon are defined in the arguments
    then those arguments will override/add the value in the config.

    :param args: Config passed as arguments to the program.
    :type args: dict
    :param config: Config passed through the config section chosen.
    :type config: dict
    :return: The modified daemon config.
    :rtype: dict
    """
    for section, value in args.items():
        if value is None:
            continue

        if section not in config["args"]:
            config["args"][section] = {}

        config["args"][section].update(value)

    return config

def setup_trident_arguments(args: Dict[AnyStr, AnyStr], config: Dict[AnyStr, Dict]) -> Dict[AnyStr, Dict]:
    """ Setup the arguments for Trident, if any arguments related to Trident are defined in the arguments
    then those arguments will override/add the value in the config.

    :param args: Config passed as arguments to the program.
    :type args: dict
    :param config: Config passed through the config section chosen.
    :type config: dict
    :return: The modified daemon config.
    :rtype: dict
    """
    for section, value in args.items():
        if value is None:
            continue

        if section not in config["args"]:
            config["args"][section] = {}

        config["args"][section].update(value)

    return config

def apply_runtime_arguments(args: Namespace, config: Dict[AnyStr, Union[AnyStr, Dict]]) -> None:
    """ Applies and combines the arguments passed by arguments and the from the config selected.
    If the config values collides with the arguments values, then the argument values are selected.

    :param args: Config passed as arguments to the program.
    :type args: :class:`Namespace`
    :param config: Config passed through the config section chosen.
    :type config: dict
    """

    if "args" not in config:
        config["args"] = {}

    config = setup_trident_arguments(
        {
            "trident": {k: v for k, v in vars(args).items() if k in ["logging_level", "verbose", "quiet"] and v is not None}
        },
        config
    )
    setup_logging(args, config)

    config = setup_plugin_arguments(
        {
            "store": {k: v for k, v in vars(args).items() if k in ["no_store", "global_store", "path_store"] and v is not None},
            "runner": {k: v for k, v in vars(args).items() if k in ["dont_store_on_error", "filter_results"] and v is not None}
        },
        config
    )
    config = setup_daemon_arguments(
        {
            "daemon": {k: v for k, v in vars(args).items() if k in ["workers"] and v is not None}
        },
        config
    )
    return validate_config(config)


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

    config = apply_runtime_arguments(trident_argument_parser.args, trident_config_parser.args)
    logger = logging.getLogger(__name__)

    try:
        trident_config = TridentConfig(config)
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
        if config.get("logging_level") == "DEBUG":
            traceback.print_exc()

    logger.info(f"Trident finished execution on: '{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}' after: '{round(time.time() - start_time, 5)}' seconds.")
