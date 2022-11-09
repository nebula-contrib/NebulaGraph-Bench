# -*- coding: utf-8 -*-
import os
import subprocess
import inspect
import importlib
import socket
import logging
import datetime

import jinja2
import click

from nebula_bench.setting import WORKSPACE_PATH, DINGDING_SECRET, DINGDING_WEBHOOK


def load_class(package_name, load_all, base_class, class_name=None):
    r = []
    if load_all:
        _package = importlib.import_module(package_name)
        for attr in dir(_package):
            _module = getattr(_package, attr)
            if not inspect.ismodule(_module):
                continue

            # _module = importlib.import_module(package_name + "." + name)
            for name in dir(_module):
                _class = getattr(_module, name)
                if not inspect.isclass(_class):
                    continue
                if (
                    issubclass(_class, base_class)
                    and _class.__name__ != base_class.__name__
                ):
                    r.append(_class)
    else:
        assert class_name is not None, "class_name should not be None"
        _module_name, _class_name = class_name.split(".")
        _module = importlib.import_module(".".join([package_name, _module_name]))
        _class = getattr(_module, _class_name)
        assert _class is not None, "cannot find the class"
        r.append(_class)
    return r


def get_current_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    r = s.getsockname()[0]
    s.close()
    return r


def jinja_dump(template_file_name, dump_file, kwargs=None):
    """
    :param template_file_name:
    :param dump_file:
    :param kwargs:
    :return:
    """
    kwargs = {} or kwargs
    assert template_file_name is not None
    p = WORKSPACE_PATH / "templates" / template_file_name
    with open(str(p), "r") as fl:
        template_body = fl.read()
    template = jinja2.Template(template_body)
    template.stream(**kwargs).dump(dump_file, encoding="utf8")


def get_logger(logger_name, level=logging.INFO):
    l = logging.getLogger(logger_name)
    l.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)06d - %(levelname)s %(filename)s [line:%(lineno)d] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    for handler in (console_handler,):
        l.addHandler(handler)
    logging.root = l
    return l


logger = get_logger("nebula-bench")


def run_process(command, env=None):
    my_env = os.environ.copy()
    if env:
        my_env.update(env)
    with subprocess.Popen(command, env=my_env, stdout=subprocess.PIPE) as s:
        while True:
            output = str(s.stdout.readline().decode("utf8"))
            if output == "" and s.poll() is not None:
                return s.returncode
            if output:
                output = output.replace("\n", "")
                click.echo(output)


def get_now_str():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")
