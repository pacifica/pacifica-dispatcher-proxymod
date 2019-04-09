#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pacifica-dispatcher-proxymod: pacifica/dispatcher/proxymod/event_handlers.py
#
# Copyright (c) 2019, Battelle Memorial Institute
# All rights reserved.
#
# See LICENSE and WARRANTY for details.
"""Proxymod Event Handler Module."""
import contextlib
import copy
import importlib
import os
import re
import tempfile
import typing

from cloudevents.model import Event

from pacifica.dispatcher.downloader_runners import DownloaderRunner
from pacifica.dispatcher.event_handlers import EventHandler
from pacifica.dispatcher.models import File, Transaction, TransactionKeyValue
from pacifica.dispatcher.uploader_runners import UploaderRunner

from .exceptions import ConfigNotFoundProxEventHandlerError, InvalidConfigProxEventHandlerError
from .exceptions import InvalidModelProxEventHandlerError

RE_PATTERN_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_ = re.compile(r'^' + re.escape('.').join([
    re.escape('proxymod'),
    r'([^' + re.escape('.') + r']+)',  # 1. config_id
    r'([^' + re.escape('.') + r']+)',  # 2. header_name
    r'([^' + re.escape('.') + r']+)',  # 3. subheader_name
]) + r'$')

RE_GROUP_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_CONFIG_ID_ = 1

RE_GROUP_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_HEADER_NAME_ = 2

RE_GROUP_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_SUBHEADER_NAME_ = 3


def _format_proxymod_config(config: typing.Dict[str, typing.Dict[str, typing.Any]]) -> str:
    lines = []

    for header_name, header_values in config.items():
        lines.append('[{0}]'.format(header_name))

        for subheader_name, subheader_value in header_values.items():
            lines.append('{0} = {1}'.format(subheader_name, subheader_value))

    lines.append('')

    return os.linesep.join(lines)


def _is_valid_proxymod_config(config: typing.Dict[str, typing.Dict[str, typing.Any]]) -> bool:
    valid_config_meta = {
        'PROJECT': ['runtime', 'failure'],
        'INPUTS': ['in_dir', 'in_file_one', 'in_file_two'],
        'OUTPUTS': ['out_dir']
    }
    for header_name, header_values in config.items():
        subheader_names = header_values.keys()
        if header_name not in valid_config_meta.keys():
            return False
        for subheader_name in valid_config_meta.get(header_name):
            if subheader_name not in subheader_names:
                return False
        for subheader_name in subheader_names:
            if subheader_name not in valid_config_meta.get(header_name):
                return False
    return True


def _to_proxymod_config_by_config_id(
        transaction_key_values: typing.List[TransactionKeyValue]
        ) -> typing.Dict[str, typing.Dict[str, typing.Dict[str, typing.Any]]]:
    config_by_config_id = {}

    for transaction_key_value in transaction_key_values:
        match = RE_PATTERN_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_.match(transaction_key_value.key)

        if match is not None:
            config_id = match.group(RE_GROUP_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_CONFIG_ID_)
            header_name = match.group(RE_GROUP_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_HEADER_NAME_)
            subheader_name = match.group(RE_GROUP_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_SUBHEADER_NAME_)

            if config_id not in config_by_config_id:
                config_by_config_id[config_id] = {}

            if header_name not in config_by_config_id[config_id]:
                config_by_config_id[config_id][header_name] = {}

            if subheader_name not in config_by_config_id[config_id][header_name]:
                config_by_config_id[config_id][header_name][subheader_name] = transaction_key_value.value

    return config_by_config_id


@contextlib.contextmanager
def _redirect_stdout_stderr(tempdir_name, prefix='', mode='w'):
    with open(os.path.join(tempdir_name, '{}stdout.log'.format(prefix)), mode) as stdout_file:
        with open(os.path.join(tempdir_name, '{}stderr.log'.format(prefix)), mode) as stderr_file:
            with contextlib.redirect_stdout(stdout_file):
                with contextlib.redirect_stderr(stderr_file):
                    yield (stdout_file, stderr_file)


def _assert_valid_proxevent(transaction_key_value_insts, event):
    config_by_config_id = _to_proxymod_config_by_config_id(transaction_key_values=transaction_key_value_insts)

    for config_id in ['config_1', 'config_2', 'config_3']:
        if config_id not in config_by_config_id:
            raise ConfigNotFoundProxEventHandlerError(event, config_id)

        config = config_by_config_id[config_id]

        if not _is_valid_proxymod_config(config):
            raise InvalidConfigProxEventHandlerError(event, config_id, config)
    return config_by_config_id


def _assert_valid_proxinputs(config_by_config_id, file_insts):
    input_file_insts = []
    _in_dir = config_by_config_id.get('config_1', {}).get('INPUTS', {}).get('in_dir', None)
    _in_file_one = config_by_config_id.get('config_1', {}).get('INPUTS', {}).get('in_file_one', None)
    _in_file_two = config_by_config_id.get('config_1', {}).get('INPUTS', {}).get('in_file_two', None)
    for file_inst in file_insts:
        # pylint: disable=too-many-boolean-expressions
        if (file_inst.mimetype == 'text/csv') and (file_inst.subdir is not None) and \
           (_in_dir == file_inst.subdir) and (file_inst.name is not None) and \
           ((_in_file_one == file_inst.name) or (_in_file_two == file_inst.name)):
            input_file_insts.append(file_inst)
        # pylint: enable=too-many-boolean-expressions
    return input_file_insts


def _assert_valid_proxmodels(file_insts):
    model_file_insts = []
    for file_inst in file_insts:
        if (file_inst.mimetype == 'text/x-python') and (file_inst.subdir == 'models/'):
            model_file_insts.append(file_inst)
    return model_file_insts


# pylint: disable=too-few-public-methods
class ProxEventHandler(EventHandler):
    """
    Proxymod Event Handler Class.

    Handle a proxymod event and run proxymod.
    """

    def __init__(self, downloader_runner: DownloaderRunner, uploader_runner: UploaderRunner) -> None:
        """Save the download and upload runner classes for later use."""
        super(ProxEventHandler, self).__init__()
        self.downloader_runner = downloader_runner
        self.uploader_runner = uploader_runner

    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    def handle(self, event: Event) -> None:
        """Handle the proxymod event."""
        transaction_inst = Transaction.from_cloudevents_model(event)
        transaction_key_value_insts = TransactionKeyValue.from_cloudevents_model(event)
        file_insts = File.from_cloudevents_model(event)
        config_by_config_id = _assert_valid_proxevent(transaction_key_value_insts, event)
        input_file_insts = _assert_valid_proxinputs(config_by_config_id, file_insts)
        model_file_insts = _assert_valid_proxmodels(file_insts)

        with tempfile.TemporaryDirectory() as downloader_tempdir_name:
            with tempfile.TemporaryDirectory() as uploader_tempdir_name:
                # model_file_openers = self.downloader_runner.download(downloader_tempdir_name, model_file_insts)
                with _redirect_stdout_stderr(uploader_tempdir_name, 'download-'):
                    model_file_openers = self.downloader_runner.download(
                        downloader_tempdir_name, model_file_insts)

                model_file_funcs = []

                for model_file_inst, model_file_opener in zip(model_file_insts, model_file_openers):
                    with model_file_opener() as file:
                        try:
                            name = os.path.splitext(model_file_inst.name)[0]

                            spec = importlib.util.spec_from_file_location(name, file.name)
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            # NOTE Deliberately raise `AttributeError` if `name` does not exist.
                            func = getattr(module, name)

                            if callable(func):
                                model_file_funcs.append(func)
                            else:
                                # NOTE Deliberately raise `TypeError` by calling an uncallable.
                                func()
                        except Exception as reason:
                            raise InvalidModelProxEventHandlerError(event, model_file_inst, reason)

                # input_file_openers = self.downloader_runner.download(downloader_tempdir_name, input_file_insts)

                with _redirect_stdout_stderr(uploader_tempdir_name, 'download-', 'a'):
                    input_file_openers = self.downloader_runner.download(
                        downloader_tempdir_name, input_file_insts)

                abspath_config_by_config_id = copy.deepcopy(config_by_config_id)

                for config_id, config in abspath_config_by_config_id.items():
                    if 'INPUTS' in config:
                        if 'in_dir' in config['INPUTS']:
                            for opener in input_file_openers:
                                with opener() as file:
                                    config['INPUTS']['in_dir'] = os.path.abspath(os.path.dirname(file.name))

                                    break

                    if 'OUTPUTS' in config:
                        if 'out_dir' in config['OUTPUTS']:
                            config['OUTPUTS']['out_dir'] = os.path.abspath(
                                os.path.join(uploader_tempdir_name, config['OUTPUTS']['out_dir']))

                for config_id, config in config_by_config_id.items():
                    with open(os.path.join(uploader_tempdir_name, '{0}.ini'.format(config_id)), 'w') as config_file:
                        config_file.write(_format_proxymod_config(config))

                config_1_file = tempfile.NamedTemporaryFile(suffix='.ini', delete=False)
                config_1_file.write(bytes(_format_proxymod_config(
                    abspath_config_by_config_id['config_1']), 'utf-8'))
                config_1_file.close()

                config_2_file = tempfile.NamedTemporaryFile(suffix='.ini', delete=False)
                config_2_file.write(bytes(_format_proxymod_config(
                    abspath_config_by_config_id['config_2']), 'utf-8'))
                config_2_file.close()

                config_3_file = tempfile.NamedTemporaryFile(suffix='.ini', delete=False)
                config_3_file.write(bytes(_format_proxymod_config(
                    abspath_config_by_config_id['config_3']), 'utf-8'))
                config_3_file.close()

                with _redirect_stdout_stderr(uploader_tempdir_name):
                    inst_func_zip = zip(model_file_insts, model_file_funcs)
                    for model_file_inst, model_file_func in inst_func_zip:
                        try:
                            model_file_func(config_1_file.name,
                                            config_2_file.name, config_3_file.name)
                        except Exception as reason:
                            raise InvalidModelProxEventHandlerError(
                                event, model_file_inst, reason)

                os.unlink(config_1_file.name)
                os.unlink(config_2_file.name)
                os.unlink(config_3_file.name)
                with _redirect_stdout_stderr(uploader_tempdir_name, 'upload-'):
                    # pylint: disable=protected-access
                    (_bundle, _job_id, _state) = self.uploader_runner.upload(
                        uploader_tempdir_name, transaction=Transaction(
                            submitter=transaction_inst.submitter,
                            instrument=transaction_inst.instrument,
                            project=transaction_inst.project
                        ), transaction_key_values=[
                            TransactionKeyValue(key='Transactions._id', value=transaction_inst._id)
                        ]
                    )
                    # pylint: enable=protected-access
    # pylint: enable=too-many-locals
    # pylint: enable=too-many-branches
    # pylint: enable=too-many-statements
# pylint: enable=too-few-public-methods


__all__ = ('ProxEventHandler', )
