#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pacifica-dispatcher-proxymod: pacifica/dispatcher/proxymod/tests/test_proxymod.py
#
# Copyright (c) 2019, Battelle Memorial Institute
# All rights reserved.
#
# See LICENSE and WARRANTY for details.
"""Module to test proxymod dispatcher."""
import json
import os
import unittest

from mock import patch
from cloudevents.model import Event
from jsonpath2.path import Path

from pacifica.dispatcher.downloader_runners import LocalDownloaderRunner
from pacifica.dispatcher.uploader_runners import LocalUploaderRunner

from pacifica.dispatcher_proxymod.event_handlers import ProxEventHandler, _is_valid_proxymod_config
from pacifica.dispatcher_proxymod.event_handlers import _assert_valid_proxevent
from pacifica.dispatcher_proxymod.router import router
from pacifica.dispatcher_proxymod.exceptions import ConfigNotFoundProxEventHandlerError
from pacifica.dispatcher_proxymod.exceptions import InvalidConfigProxEventHandlerError


class ProxTestCase(unittest.TestCase):
    """Proxymod unittest class."""

    def setUp(self):
        """Build temporary directories to start testing."""
        self.basedir_name = os.path.abspath(os.path.join('test_files', 'C234-1234-1234'))
        with open(os.path.join(self.basedir_name, 'event.json'), mode='r') as event_file:
            self.event_data = json.load(event_file)

    def test_event_handler(self):
        """Test the event handler."""
        event = Event(self.event_data)
        downloader_runner = LocalDownloaderRunner(os.path.join(self.basedir_name, 'data'))
        uploader_runner = LocalUploaderRunner()
        event_handler = ProxEventHandler(downloader_runner, uploader_runner)
        self.assertEqual(None, event_handler.handle(event))

    def test_proxymod_path(self):
        """Test proxymod path."""
        proxymod_path = Path.parse_file(os.path.join(
            os.path.dirname(__file__), '..', 'pacifica',
            'dispatcher_proxymod', 'jsonpath2', 'proxymod.txt'
        ))
        self.assertEqual(1, len(list(proxymod_path.match(self.event_data))))

    def test_router(self):
        """Test the router."""
        self.assertEqual(1, len(list(router.match(self.event_data))))

    def test_bad_configs(self):
        """Test some bad configuration files see if we catch them."""
        self.assertFalse(_is_valid_proxymod_config({'foo': {'bar': ''}}))
        self.assertFalse(_is_valid_proxymod_config({'PROJECTS': {'bar': ''}}))
        self.assertFalse(_is_valid_proxymod_config({'PROJECTS': {'runtime': ''}}))

    @patch('pacifica.dispatcher_proxymod.event_handlers._to_proxymod_config_by_config_id')
    def test_bad_configs_exception(self, config_id_method):
        """Test bad config files throw exceptions properly."""
        config_id_method.return_value = {'config_1': {}}
        with self.assertRaises(ConfigNotFoundProxEventHandlerError):
            _assert_valid_proxevent({}, self.event_data)
        config_id_method.return_value = {'config_1': {'foo': {}}, 'config_2': {}, 'config_3': {}}
        with self.assertRaises(InvalidConfigProxEventHandlerError):
            _assert_valid_proxevent({}, self.event_data)


if __name__ == '__main__':
    unittest.main()
