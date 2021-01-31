#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Notification Type Handlers

Implements each type of notification handler.
@author: Jacob Wahlman
"""

from dataclasses import dataclass
from urllib import request
import smtplib
import json

from typing import Union, AnyStr, Dict, Any, Iterable

import logging
logger = logging.getLogger("__main__")


@dataclass
class TridentNotificationHTTPHandlerConfig:
    destination: AnyStr
    method: Union["GET", "POST"]
    headers: Dict[AnyStr, AnyStr]
    payload: Dict[AnyStr, Any]
    include_result: bool

    def __init__(self, name: AnyStr, configuration: Dict[AnyStr, AnyStr]):
        self.name = name
        
        self._apply_notification_config(configuration)
        self._validate_config()

    def _apply_notification_config(self, notification_config: Dict[AnyStr, Any]):
        """ Apply any config parameter passed to this notification config.
        If some required values are not set then these are set to their default values.

        :param notification_config: The configuration that should be used when sending notifications.
        :type notification_config: Dict[AnyStr, AnyStr]
        """
        if "payload" not in notification_config:
            notification_config["payload"] = dict()

        if "include_result" not in notification_config:
            notification_config["include_result"] = False

        if "headers" not in notification_config:
            notification_config["headers"] = {
                "Content-Type": "application/json",
                "X-Source-Application": "Trident"
            }

        for arg, value in notification_config.items():
            setattr(self, arg, value)

    def _validate_config(self):
        """ Validate that the configuration for this notification handler.

        :raises ValueError: If the configuration is invalid (lacking required arguments, conflicting arguments) then raise ValueError.
        """
        if not hasattr(self, "destination") or not self.destination:
            raise ValueError(f"No destination for HTTP notification: '{self.name}' was defined")

        if not hasattr(self, "method") or not self.method:
            raise ValueError(f"No HTTP method was defined for notification: '{self.name}'")

        if self.method.upper() not in ["GET", "POST"]:
            raise ValueError(f"Unsupported HTTP method: '{self.method}' used for notitication: '{self.name}'")

        if self.method.upper() == "GET" and (self.payload or self.include_result):
            logger.warning("Payload/Include result can not be used with GET requests, will not include payload")
            self.include_result = False
            self.payload = dict()

        headers = {header.lower(): value.lower() for header, value in self.headers.items()}
        if "content-type" in headers and "application/json" not in headers["content-type"] and self.include_result:
            logger.warning(f"Include result was defined with an Content-Type that is not 'application/json', might produce unexpected results")
        

@dataclass 
class TridentNotificationEmailHandlerConfig:
    smtp_server: AnyStr
    sender: AnyStr
    receivers: Iterable[AnyStr]
    headers: Dict[AnyStr, AnyStr]
    subject: AnyStr
    message: AnyStr
    include_result: bool

    def __init__(self, name: AnyStr, configuration: Dict[AnyStr, AnyStr]):
        self.name = name

        self._apply_notification_config(configuration)
        self._validate_config()

    def _apply_notification_config(self, notification_config: Dict[AnyStr, Any]):
        """ Apply any config parameter passed to this notification config.

        :param notification_config: The configuration that should be used when sending notifications.
        :type notification_config: Dict[AnyStr, AnyStr]
        """
        if "subject" not in notification_config:
            notification_config["subject"] = f"Trident Notification for: '{self.name}'"

        if "headers" not in notification_config:
            notification_config["headers"] = {}

        if "include_result" not in notification_config:
            notification_config["include_result"] = False

        for arg, value in notification_config.items():
            setattr(self, arg, value)

    def _validate_config(self):
        """ Validate that the configuration for this notification handler.

        :raises ValueError: If the configuration is invalid (lacking required arguments, conflicting arguments) then raise ValueError.
        """
        if not hasattr(self, "smtp_server") or not self.smtp_server:
            raise ValueError(f"No SMTP server was defined for notification: '{self.name}'")

        if not hasattr(self, "receivers") or not self.receivers:
            raise ValueError(f"No receiver list was defined for notification: '{self.name}'")

        if not hasattr(self, "sender") or not self.sender:
            raise ValueError(f"No sender was defined for notification: '{self.name}'")

        if (not hasattr(self, "message") or not self.message) and (not hasattr(self, "include_result") or not self.include_result):
            logger.warning(f"No message body was defined and include results was unset or set to false for notification: '{self.name}'")


class TridentNotificationHTTPHandler:
    def __init__(self, notification_config: TridentNotificationHTTPHandlerConfig):
        self.notification_config = notification_config

    def send_notification(self, content: Dict[AnyStr, Any]):
        """ Send the notification using urllib to send the actual request to the destination.
        Uses the configuration provided by :class:`TridentNotificationHTTPHandlerConfig` to fill the request.
        If both content is used and payload/include result is used then we combine the two.
        The combine operation only supports content that is JSON parseable so if any other Content-Type header is set
        then we just send the payload that is defined in the configuration.

        :param content: JSON parseable content to include in the notification
        :type content: Dict[AnyStr, Any]
        """
        if self.notification_config.payload and content:
            self.notification_config.payload["content"] = content
            data = self.notification_config.payload
        else:
            data = self.notification_config.payload if self.notification_config.payload else content

        request.urlopen(request.Request(
            url=self.notification_config.destination,
            method=self.notification_config.method,
            headers=self.notification_config.headers,
            data=json.dumps(self.notification_config.payload).encode("utf-8") if self.notification_config.payload else b""
        ))


class TridentNotificationEmailHandler:
    def __init__(self, notification_config: TridentNotificationEmailHandlerConfig):
        self.notification_config = notification_config

    def send_notification(self, content: Dict[AnyStr, Any]):
        """ Send the notification using smtplib to send the e-mail.
        Uses the configuration provided by :class:`TridentNotificationEmailHandlerConfig` to fill the e-mail.
        If both content is used and payload/include result is used then these are separated and sent in the same e-mail.

        :param content: Content to include in the e-mail
        :type content: Dict[AnyStr, Any]
        """
        if self.notification_config.receivers and isinstance(self.notification_config.receivers, str):
            self.notification_config.receivers = [self.notification_config.receivers]

        message_body = self.notification_config.message
        if content is not None:
            message_body += "\r\n"
            for key, value in content.items():
                message_body += "{key}: {value}\r\n".format(key=key, value=value)

        for receiver in self.notification_config.receivers:
            message = """From: <{sender}>\r\nTo: <{receiver}>\r\nSubject: {subject}\r\n\r\n{content}""".format(
                    sender=self.notification_config.sender,
                    receiver=receiver,
                    subject=self.notification_config.subject,
                    content=message_body
                )
            
            smtp_obj = smtplib.SMTP(self.notification_config.smtp_server)
            smtp_obj.sendmail(self.notification_config.sender, [receiver], message)
