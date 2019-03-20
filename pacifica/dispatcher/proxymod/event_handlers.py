#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pacifica-dispatcher-proxymod: pacifica/dispatcher/proxymod/event_handlers.py
#
# Copyright (c) 2019, Battelle Memorial Institute
# All rights reserved.
#
# See LICENSE and WARRANTY for details.

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

from .exceptions import ConfigNotFoundProxEventHandlerError, InvalidConfigProxEventHandlerError, InvalidModelProxEventHandlerError

RE_PATTERN_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_ = re.compile(r'^' + re.escape('.').join([
    re.escape('proxymod'),
    r'([^' + re.escape('.') + r']+)', # 1. config_id
    r'([^' + re.escape('.') + r']+)', # 2. header_name
    r'([^' + re.escape('.') + r']+)', # 3. subheader_name
]) + r'$')

RE_GROUP_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_CONFIG_ID_ = 1

RE_GROUP_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_HEADER_NAME_ = 2

RE_GROUP_PROXYMOD_TRANSACTION_KEY_VALUE_QUAD_SUBHEADER_NAME_ = 3

def _format_proxymod_config(config: typing.Dict[str, typing.Dict[str, typing.Any]] = {}) -> str:
    lines = []

    for header_name, header_values in config.items():
        lines.append('[{0}]'.format(header_name))

        for subheader_name, subheader_value in header_values.items():
            lines.append('{0} = {1}'.format(subheader_name, subheader_value))

    lines.append('')

    return os.linesep.join(lines)

def _is_valid_proxymod_config(config: typing.Dict[str, typing.Dict[str, typing.Any]] = {}) -> bool:
    for header_name, header_values in config.items():
        subheader_names = header_values.keys()

        if 'PROJECT' == header_name:
            for subheader_name in ['runtime', 'failure']:
                if subheader_name not in subheader_names:
                    return False

            for subheader_name in subheader_names:
                if subheader_name not in ['runtime', 'failure']:
                    return False
        elif 'INPUTS' == header_name:
            for subheader_name in ['in_dir', 'in_file_one', 'in_file_two']:
                if subheader_name not in subheader_names:
                    return False

            for subheader_name in subheader_names:
                if subheader_name not in ['in_dir', 'in_file_one', 'in_file_two']:
                    return False
        elif 'OUTPUTS' == header_name:
            for subheader_name in ['out_dir']:
                if subheader_name not in subheader_names:
                    return False

            for subheader_name in subheader_names:
                if subheader_name not in ['out_dir']:
                    return False
        else:
            return False

    return True

def _to_proxymod_config_by_config_id(transaction_key_values: typing.List[TransactionKeyValue] = []) -> typing.Dict[str, typing.Dict[str, typing.Dict[str, typing.Any]]]:
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

class ProxEventHandler(EventHandler):
    def __init__(self, downloader_runner: DownloaderRunner, uploader_runner: UploaderRunner) -> None:
        super(ProxEventHandler, self).__init__()

        self.downloader_runner = downloader_runner
        self.uploader_runner = uploader_runner

    def handle(self, event: Event) -> None:
        transaction_inst = Transaction.from_cloudevents_model(event)
        transaction_key_value_insts = TransactionKeyValue.from_cloudevents_model(event)
        file_insts = File.from_cloudevents_model(event)

        config_by_config_id = _to_proxymod_config_by_config_id(transaction_key_values=transaction_key_value_insts)

        for config_id in ['config_1', 'config_2', 'config_3']:
            if config_id not in config_by_config_id:
                raise ConfigNotFoundProxEventHandlerError(event, config_id)

            config = config_by_config_id[config_id]

            if not _is_valid_proxymod_config(config):
                raise InvalidConfigProxEventHandlerError(event, config_id, config)

        input_file_insts = []
        model_file_insts = []

        _in_dir = config_by_config_id.get('config_1', {}).get('INPUTS', {}).get('in_dir', None)
        _in_file_one = config_by_config_id.get('config_1', {}).get('INPUTS', {}).get('in_file_one', None)
        _in_file_two = config_by_config_id.get('config_1', {}).get('INPUTS', {}).get('in_file_two', None)

        for file_inst in file_insts:
            if ('text/csv' == file_inst.mimetype) and (file_inst.subdir is not None) and (_in_dir == file_inst.subdir) and (file_inst.name is not None) and ((_in_file_one == file_inst.name) or (_in_file_two == file_inst.name)):
                input_file_insts.append(file_inst)
            elif ('text/x-python' == file_inst.mimetype) and ('models/' == file_inst.subdir):
                model_file_insts.append(file_inst)
            else:
                # NOTE Ignore other files.
                pass

        with tempfile.TemporaryDirectory() as downloader_tempdir_name:
            with tempfile.TemporaryDirectory() as uploader_tempdir_name:
                # model_file_openers = self.downloader_runner.download(downloader_tempdir_name, model_file_insts)

                with open(os.path.join(uploader_tempdir_name, 'download-stdout.log'), mode='w') as downloader_stdout_file:
                    with open(os.path.join(uploader_tempdir_name, 'download-stderr.log'), mode='w') as downloader_stderr_file:
                        with contextlib.redirect_stdout(downloader_stdout_file):
                            with contextlib.redirect_stderr(downloader_stderr_file):
                                model_file_openers = self.downloader_runner.download(downloader_tempdir_name, model_file_insts)

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

                with open(os.path.join(uploader_tempdir_name, 'download-stdout.log'), mode='a') as downloader_stdout_file:
                    with open(os.path.join(uploader_tempdir_name, 'download-stderr.log'), mode='a') as downloader_stderr_file:
                        with contextlib.redirect_stdout(downloader_stdout_file):
                            with contextlib.redirect_stderr(downloader_stderr_file):
                                input_file_openers = self.downloader_runner.download(downloader_tempdir_name, input_file_insts)

                abspath_config_by_config_id = copy.deepcopy(config_by_config_id)

                for config_id, config in abspath_config_by_config_id.items():
                    if 'INPUTS' in config:
                        if 'in_dir' in config['INPUTS']:
                            for input_file_inst, opener in zip(input_file_insts, input_file_openers):
                                with opener() as file:
                                    config['INPUTS']['in_dir'] = os.path.abspath(os.path.dirname(file.name))

                                    break

                    if 'OUTPUTS' in config:
                        if 'out_dir' in config['OUTPUTS']:
                            config['OUTPUTS']['out_dir'] = os.path.abspath(os.path.join(uploader_tempdir_name, config['OUTPUTS']['out_dir']))

                for config_id, config in config_by_config_id.items():
                    with open(os.path.join(uploader_tempdir_name, '{0}.ini'.format(config_id)), mode='w') as config_file:
                        config_file.write(_format_proxymod_config(config))

                with tempfile.NamedTemporaryFile(suffix='.ini') as config_1_file:
                    config_1_file.write(bytes(_format_proxymod_config(abspath_config_by_config_id['config_1']), 'utf-8'))
                    config_1_file.seek(0)

                    with tempfile.NamedTemporaryFile(suffix='.ini') as config_2_file:
                        config_2_file.write(bytes(_format_proxymod_config(abspath_config_by_config_id['config_2']), 'utf-8'))
                        config_2_file.seek(0)

                        with tempfile.NamedTemporaryFile(suffix='.ini') as config_3_file:
                            config_3_file.write(bytes(_format_proxymod_config(abspath_config_by_config_id['config_3']), 'utf-8'))
                            config_3_file.seek(0)

                            # for model_file_inst, model_file_func in zip(model_file_insts, model_file_funcs):
                            #     try:
                            #         model_file_func(config_1_file.name, config_2_file.name, config_3_file.name)
                            #     except Exception as reason:
                            #         raise InvalidModelProxEventHandlerError(event, model_file_inst, reason)

                            with open(os.path.join(uploader_tempdir_name, 'stdout.log'), mode='w') as stdout_file:
                                with open(os.path.join(uploader_tempdir_name, 'stderr.log'), mode='w') as stderr_file:
                                    with contextlib.redirect_stdout(stdout_file):
                                        with contextlib.redirect_stderr(stderr_file):
                                            for model_file_inst, model_file_func in zip(model_file_insts, model_file_funcs):
                                                try:
                                                    model_file_func(config_1_file.name, config_2_file.name, config_3_file.name)
                                                except Exception as reason:
                                                    raise InvalidModelProxEventHandlerError(event, model_file_inst, reason)

                # (bundle, job_id, state) = self.uploader_runner.upload(uploader_tempdir_name, transaction=Transaction(submitter=transaction_inst.submitter, instrument=transaction_inst.instrument, project=transaction_inst.project), transaction_key_values=[TransactionKeyValue(key='Transactions._id', value=transaction_inst._id)])

                with open(os.path.join(uploader_tempdir_name, 'upload-stdout.log'), mode='w') as uploader_stdout_file:
                    with open(os.path.join(uploader_tempdir_name, 'upload-stderr.log'), mode='w') as uploader_stderr_file:
                        with contextlib.redirect_stdout(uploader_stdout_file):
                            with contextlib.redirect_stderr(uploader_stderr_file):
                                (bundle, job_id, state) = self.uploader_runner.upload(uploader_tempdir_name, transaction=Transaction(submitter=transaction_inst.submitter, instrument=transaction_inst.instrument, project=transaction_inst.project), transaction_key_values=[TransactionKeyValue(key='Transactions._id', value=transaction_inst._id)])

                pass

            pass

        pass

__all__ = ('ProxEventHandler', )
