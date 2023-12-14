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
import pandas as pd

from nebula_bench.setting import (
    WORKSPACE_PATH,
    DINGDING_SECRET,
    DINGDING_WEBHOOK,
)


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
                if issubclass(_class, base_class) and _class.__name__ != base_class.__name__:
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


def csv_dump(output, data):
    header = [
        "Name",
        "Vu",
        "Accuracy(%)",
        "QPS",
        "LatencyP90(ms)",
        "LatencyP95(ms)",
        "LatencyP99(ms)",
        "ResponseTimeP90(ms)",
        "ResponseTimeP95(ms)",
        "ResponseTimeP99(ms)",
        "RowSizeP90",
        "RowSizeP95",
        "RowSizeP99",
    ]
    df = pd.DataFrame(columns=header)
    for d in data:
        for k6 in d["k6"]:
            row = pd.Series(dtype="float64")
            row["Name"] = d["case"]["name"]
            row["Vu"] = k6["vu"]
            total_checks = k6["report"]["metrics"]["checks"]["passes"] + k6["report"]["metrics"]["checks"]["fails"]
            passed_checks = k6["report"]["metrics"]["checks"]["passes"]
            row["Accuracy(%)"] = round(passed_checks/total_checks*100, 2)
            row["QPS"] = round(k6["report"]["metrics"]["iterations"]["rate"], 2)
            row["LatencyP90(ms)"] = round(k6["report"]["metrics"]["latency"]["p(90)"] / 1e3, 2)
            row["LatencyP95(ms)"] = round(k6["report"]["metrics"]["latency"]["p(95)"] / 1e3, 2)
            row["LatencyP99(ms)"] = round(k6["report"]["metrics"]["latency"]["p(99)"] / 1e2, 2)
            row["ResponseTimeP90(ms)"] = round(
                k6["report"]["metrics"]["responseTime"]["p(90)"] / 1e3, 2
            )
            row["ResponseTimeP95(ms)"] = round(
                k6["report"]["metrics"]["responseTime"]["p(95)"] / 1e3, 2
            )
            row["ResponseTimeP99(ms)"] = round(
                k6["report"]["metrics"]["responseTime"]["p(99)"] / 1e3, 2
            )
            row["RowSizeP90"] = k6["report"]["metrics"]["rowSize"]["p(90)"]
            row["RowSizeP95"] = k6["report"]["metrics"]["rowSize"]["p(95)"]
            row["RowSizeP99"] = k6["report"]["metrics"]["rowSize"]["p(99)"]
            df = pd.concat([df, row.to_frame().T], ignore_index=True)

    df = df.sort_values(by=["Name", "Vu"])
    df.to_csv(output, index=False)
