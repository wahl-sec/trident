#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Notification Daemon

Controls the notification system for Trident runners.
@author: Jacob Wahlman
"""

from dataclasses import dataclass

from typing import AnyStr, Iterable, NewType, Dict, Any

TridentNotificationTypeHandler = NewType("TridentNotificationTypeHandler", None)
TridentRunner = NewType("TridentRunner", None)

import logging

logger = logging.getLogger("__main__")

from trident.lib.notification.handler import (
    TridentNotificationHTTPHandlerConfig,
    TridentNotificationEmailHandlerConfig,
    TridentNotificationHTTPHandler,
    TridentNotificationEmailHandler,
)


@dataclass
class TridentNotificationDaemonConfig:
    handlers: Iterable[TridentNotificationTypeHandler]

    def __init__(
        self, runner: TridentRunner, notifications: Dict[AnyStr, Dict[AnyStr, Any]]
    ):
        self.handlers = self._resolve_notification_handlers(
            notifications, runner.runner_id
        )

    def _resolve_notification_handlers(
        self, notifications: Dict[AnyStr, Dict[AnyStr, Any]], runner_id: AnyStr
    ) -> Iterable[TridentNotificationTypeHandler]:
        """Ensure that the selected types of notification handler exists and try to initialize each.
        If the configuration is invalid for a specific notification type this will be logged and the program will continue.

        :param notifications: Iterable of tuples describing (type of notification handler, configuration for handler).
        :type notifications: Iterable[Tuple[AnyStr, Dict[AnyStr, AnyStr]]]
        :param runner_id: The id of the :class:`TridentRunner` that is connected to the notification handlers.
        :type runner_id: AnyStrs
        :return: Iterable of initialized notification handlers.
        :rtype: Iterable[TridentNotificationTypeHandler]
        """
        handlers = list()
        for notification_name in notifications:
            for (notification_type, notification_config) in notifications[
                notification_name
            ].items():
                try:
                    handler_classes = {
                        "http": {
                            "config": TridentNotificationHTTPHandlerConfig,
                            "handler": TridentNotificationHTTPHandler,
                        },
                        "email": {
                            "config": TridentNotificationEmailHandlerConfig,
                            "handler": TridentNotificationEmailHandler,
                        },
                    }[notification_type.lower()]
                except KeyError:
                    logger.warning(
                        f"Unsupported notification type: '{notification_type}' for notification: '{notification_name}' in runner: '{runner_id}'"
                    )
                    continue

                try:
                    handler_config = handler_classes["config"](
                        name=notification_name, configuration=notification_config
                    )
                    handlers.append(handler_classes["handler"](handler_config))
                except Exception as e:
                    logger.error(
                        f"Failed to initialize notification handler: '{notification_name}' for runner: '{runner_id}'"
                    )
                    raise e

        return handlers


class TridentNotificationDaemon:
    def __init__(self, daemon_config: TridentNotificationDaemonConfig):
        self.daemon_config = daemon_config

    def send_notification(self, content):
        """Loop through all notification handlers and send a notification using the content provided.

        :param content: JSON parseable content to include in the notification
        :type content: Dict[AnyStr, Any]
        """
        for handler in self.daemon_config.handlers:
            try:
                logger.debug(
                    f"Sending notification for handler: '{handler.notification_config.name}'"
                )
                handler.send_notification(
                    content=content
                    if handler.notification_config.include_result
                    else None
                )
            except Exception as e:
                logger.error(
                    f"Failed to send notification for handler: '{handler.notification_config.name}' due to: {e}"
                )
