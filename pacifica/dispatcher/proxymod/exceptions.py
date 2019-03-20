#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pacifica-dispatcher-proxymod: pacifica/dispatcher/proxymod/exceptions.py
#
# Copyright (c) 2019, Battelle Memorial Institute
# All rights reserved.
#
# See LICENSE and WARRANTY for details.

import typing

from cloudevents.model import Event

from pacifica.dispatcher.models import File

class ProxEventHandlerError(BaseException):
    def __init__(self, event: Event) -> None:
        super(ProxEventHandlerError, self).__init__()

        self.event = event

class ConfigNotFoundProxEventHandlerError(ProxEventHandlerError):
    def __init__(self, event: Event, config_id: str) -> None:
        super(ConfigNotFoundProxEventHandlerError, self).__init__(event)

        self.config_id = config_id

    def __str__(self) -> str:
        return 'proxymod configuration \'{0}\' not found'.format(self.config_id.replace('\'', '\\\''))

class InvalidConfigProxEventHandlerError(ProxEventHandlerError):
    def __init__(self, event: Event, config_id: str, config: typing.Dict[str, typing.Dict[str, typing.Any]]) -> None:
        super(InvalidConfigProxEventHandlerError, self).__init__(event)

        self.config_id = config_id
        self.config = config

    def __str__(self) -> str:
        return 'proxymod configuration \'{0}\' is invalid'.format(self.config_id.replace('\'', '\\\''))

class InvalidModelProxEventHandlerError(ProxEventHandlerError):
    def __init__(self, event: Event, file: File, reason: Exception) -> None:
        super(InvalidModelProxEventHandlerError, self).__init__(event)

        self.file = file
        self.reason = reason

    def __str__(self) -> str:
        return 'proxymod model for file \'{0}\' is invalid: {1}'.format(self.file.path.replace('\'', '\\\''), str(self.reason))

__all__ = ('ProxEventHandlerError', 'ConfigNotFoundProxEventHandlerError', 'InvalidConfigProxEventHandlerError', 'InvalidModelProxEventHandlerError', )
