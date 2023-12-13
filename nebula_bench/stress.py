# -*- encoding: utf-8 -*-
import os
import sys
import inspect
import copy
from pathlib import Path
import json

import click

from nebula_bench.utils import load_class, jinja_dump, run_process
from nebula_bench.common.base import BaseScenario
from nebula_bench.utils import logger, get_now_str
from nebula_bench import setting


def load_scenarios(scenarios):
    if scenarios.strip().upper() == "ALL":
        r = load_class("nebula_bench.scenarios", True, BaseScenario)
    else:
        r = load_class("nebula_bench.scenarios", False, BaseScenario, scenarios)

    r = [x for x in r if x.abstract == False]
    r = sorted(r, key=lambda x: x.rank)
    return r


class Stress(object):
    DEFAULT_DURATION = "60s"

    def __init__(
        self,
        folder,
        address,
        user,
        password,
        space,
        vid_type,
        output_folder,
        scenarios,
        args,
        dry_run,
        **kwargs
    ):
        self.folder = folder or setting.DATA_FOLDER
        self.address = address or setting.NEBULA_ADDRESS
        self.user = user or setting.NEBULA_USER
        self.password = password or setting.NEBULA_PASSWORD
        self.space = space or setting.NEBULA_SPACE
        self.vid_type = vid_type
        self.scenarios = []
        self.output_folder = output_folder
        self.dry_run = dry_run
        self.args = args
        self.scenarios = load_scenarios(scenarios)
        logger.info("total stress test scenarios is {}".format(len(self.scenarios)))

    # dump config file
    def dump_config(self, scenario, _vu=None):
        pass

    def run(self):
        pass


class StressFactory(object):
    type_list = ["K6"]
    output_folder = "output/{}".format(get_now_str())

    @classmethod
    def gen_stress(
        cls,
        _type,
        folder,
        address,
        user,
        password,
        space,
        vid_type,
        scenarios,
        args,
        dry_run=None,
        **kwargs
    ):
        if _type.upper() not in cls.type_list:
            raise Exception("not impletment this test tool, tool is {}".format(_type))

        clazz = cls.get_all_stress_class().get("{}Stress".format(_type.upper()), None)
        if args is not None:
            args = args.strip()
        return clazz(
            folder,
            address,
            user,
            password,
            space,
            vid_type,
            cls.output_folder,
            scenarios,
            args,
            dry_run,
            **kwargs
        )

    @classmethod
    def get_all_stress_class(cls):
        r = {}
        current_module = sys.modules[__name__]
        for name, clazz in inspect.getmembers(current_module):
            if inspect.isclass(clazz) and issubclass(clazz, Stress):
                r[name] = clazz
        return r


class K6Stress(Stress):
    def dump_config(self, scenario, vu=None):
        if vu is None:
            vu = 50
        assert issubclass(scenario, BaseScenario)
        name = scenario.name
        kwargs = {
            "address": self.address,
            "user": self.user,
            "password": self.password,
            "space": self.space,
            "csv_path": "{}/{}".format(self.folder, scenario.csv_path),
            "output_path": self.get_output_file(scenario, vu),
            "nGQL": scenario.nGQL.replace('"', '\\"'),
            "value": scenario.value.replace('"', '\\"'),
            "vu": vu,
        }
        if scenario.is_insert_scenario:
            template_file = "k6_config_insert.js.j2"
        else:
            template_file = "k6_config.js.j2"

        logger.info(
            "begin dump stress config, config file is {}".format(
                "{}/{}.js".format(self.output_folder, name)
            )
        )
        jinja_dump(template_file, "{}/{}.js".format(self.output_folder, name), kwargs)

    def _get_params(self):
        """
        e.g.
        args:
            "-s 60s:0 -s 40s:30 -v"
        return:
            {
                "-s": ["60s:0", "40s:30"],
                "-v": None
            }
        """
        r = {}
        if self.args is None:
            return r

        key, value = None, None
        for item in self.args.split(" "):
            if item.startswith("-"):
                if key is not None and key not in r:
                    r[key] = None
                key = item
            elif item.strip() != "":
                value = item
                if key not in r:
                    r[key] = [value]
                else:
                    r[key].append(value)

        if key is not None and key not in r:
            r[key] = None
        return r

    def get_summary_file(self, scenario, vu):
        return "{}/result_{}_{}.json".format(self.output_folder, vu, scenario.name)

    def get_output_file(self, scenario, vu):
        return "{}/output{}_{}.csv".format(self.output_folder, vu, scenario.name)

    def run(self):
        logger.info("run stress test in k6")
        params = self._get_params()

        # cannot use both stage and vu
        run_with_stage = "-s" in params or "--stage" in params
        vu = None
        duration = self.DEFAULT_DURATION
        if "-u" in params:
            vu = params.pop("-u")[0]
        if "--vus" in params:
            vu = params.pop("--vus")[0]
        if "-vu" in params:
            vu = params.pop("-vu")[0]

        if "-d" in params:
            duration = params.pop("-d")[0]
        if "--duration" in params:
            duration = params.pop("--duration")[0]

        Path(self.output_folder).mkdir(exist_ok=True, parents=True)
        if "--summary-trend-stats" not in params:
            params["--summary-trend-stats"] = ["min,avg,med,max,p(90),p(95),p(99)"]
        if setting.INFLUXDB_URL is not None and "--out" not in params and "-o" not in params:
            params["--out"] = ["influxdb={}".format(setting.INFLUXDB_URL)]

        for scenario in self.scenarios:
            vus = []
            if vu is not None:
                vus = [vu]
            else:
                vus = scenario.vus
            self.run_scenario(scenario, params, vus, duration)

    def run_scenario(self, scenario, params, vus, duration):
        for _vu in vus:
            _params = copy.copy(params)
            self.dump_config(scenario, _vu)
            if "-s" in _params or "--stage" in _params:
                command = [
                    "scripts/k6",
                    "run",
                    "{}/{}.js".format(self.output_folder, scenario.name),
                ]
            else:
                command = [
                    "scripts/k6",
                    "run",
                    "{}/{}.js".format(self.output_folder, scenario.name),
                    "-u",
                    str(_vu),
                    "-d",
                    str(duration),
                ]

            if "--summary-export" not in _params:
                _params["--summary-export"] = [self.get_summary_file(scenario, _vu)]

            for param, values in _params.items():
                if values is None:
                    command.append(param)
                else:
                    for v in values:
                        command.append(param)
                        command.append(v)

            click.echo("run command as below:")
            click.echo(" ".join([x if "(" not in x else '"{}"'.format(x) for x in command]))
            if self.dry_run is not None and self.dry_run:
                continue
            run_process(command)
            # delete the output file if all results are passed
            self.delete_output_if_passed(scenario, _vu)

    def delete_output_if_passed(self, scenario, vu):
        summary_file = self.get_summary_file(scenario, vu)
        output_file = self.get_output_file(scenario, vu)
        if not os.path.exists(summary_file):
            return
        try:
            with open(summary_file, "r") as f:
                summary = json.loads(f.read())
                if summary["metrics"]["checks"]["fails"] == 0:
                    os.remove(output_file)
        except Exception as e:
            pass
