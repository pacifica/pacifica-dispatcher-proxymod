#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pacifica-dispatcher-proxymod: pacifica/dispatcher/proxymod/exceptions.py
#
# Copyright (c) 2019, Battelle Memorial Institute
# All rights reserved.
#
# See LICENSE and WARRANTY for details.
"""Exceptions Module."""
import typing

from cloudevents.model import Event

from pacifica.dispatcher.models import File


class ProxEventHandlerError(BaseException):
    """Proxymod event handler exception."""

    def __init__(self, event: Event) -> None:
        """Save the event to be referenced later."""
        super(ProxEventHandlerError, self).__init__()
        self.event = event


class ConfigNotFoundProxEventHandlerError(ProxEventHandlerError):
    """Configuration not found exception."""

    def __init__(self, event: Event, config_id: str) -> None:
        """Save the event and configuration file id for later."""
        super(ConfigNotFoundProxEventHandlerError, self).__init__(event)
        self.config_id = config_id

    def __str__(self) -> str:
        """Have a nice output printing the configuration file id."""
        return 'proxymod configuration \'{0}\' not found'.format(self.config_id.replace('\'', '\\\''))


class InvalidConfigProxEventHandlerError(ProxEventHandlerError):
    """Configuration invalid exception."""

    def __init__(self, event: Event, config_id: str, config: typing.Dict[str, typing.Dict[str, typing.Any]]) -> None:
        """Save the event, configuration file id and configfile data for later."""
        super(InvalidConfigProxEventHandlerError, self).__init__(event)
        self.config_id = config_id
        self.config = config

    def __str__(self) -> str:
        """Have a nice output, printing configuration file id."""
        return 'proxymod configuration \'{0}\' is invalid'.format(self.config_id.replace('\'', '\\\''))


class InvalidModelProxEventHandlerError(ProxEventHandlerError):
    """Invalid model file for proxymod exception."""

    def __init__(self, event: Event, file: File, reason: Exception) -> None:
        """Save the event and the file containing the model and a reason exception."""
        super(InvalidModelProxEventHandlerError, self).__init__(event)
        self.file = file
        self.reason = reason

    def __str__(self) -> str:
        """Have a nice output, printing the file path and the exception."""
        return 'proxymod model for file \'{0}\' is invalid: {1}'.format(
            self.file.path.replace('\'', '\\\''), str(self.reason)
        )


__all__ = ('ProxEventHandlerError', 'ConfigNotFoundProxEventHandlerError',
           'InvalidConfigProxEventHandlerError', 'InvalidModelProxEventHandlerError', )
