# -*- encoding: utf-8 -*-
import sys
import inspect
from pathlib import Path

import click

from nebula_bench.utils import load_class, jinja_dump, run_process
from nebula_bench.common.base import BaseScenario
from nebula_bench.utils import logger
from nebula_bench import setting


def load_scenarios(scenarios):
    if scenarios.strip().upper() == "ALL":
        r = load_class("nebula_bench.scenarios", True, BaseScenario)
    else:
        r = load_class("nebula_bench.scenarios", False, BaseScenario, scenarios)

    r = [x for x in r if x.abstract == False]
    return r


class Stress(object):
    def __init__(
        self,
        folder,
        address,
        user,
        password,
        space,
        vid_type,
        scenarios,
        vu,
        duration,
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
        self.output_folder = "output"
        self.vu = vu
        self.duration = duration
        self.dry_run = dry_run
        self.scenarios = load_scenarios(scenarios)
        logger.info("total stress test scenarios is {}".format(len(self.scenarios)))

    # dump config file
    def dump_config(self, scenario):
        pass

    def run(self):
        pass


class StressFactory(object):
    type_list = ["K6"]

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
        vu,
        duration,
        dry_run=None,
        **kwargs
    ):
        if _type.upper() not in cls.type_list:
            raise Exception("not impletment this test tool, tool is {}".format(_type))

        clazz = cls.get_all_stress_class().get("{}Stress".format(_type.upper()), None)
        return clazz(
            folder,
            address,
            user,
            password,
            space,
            vid_type,
            scenarios,
            vu,
            duration,
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
    def dump_config(self, scenario):
        assert issubclass(scenario, BaseScenario)
        name = scenario.name
        kwargs = {
            "address": self.address,
            "user": self.user,
            "password": self.password,
            "space": self.space,
            "csv_path": "{}/{}".format(self.folder, scenario.csv_path),
            "output_path": "{}/output_{}.csv".format(self.output_folder, name),
            "nGQL": scenario.nGQL,
        }

        kwargs["param"] = ",".join(["d[" + str(x) + "]" for x in scenario.csv_index])
        logger.info(
            "begin dump stress config, config file is {}".format(
                "{}/{}.js".format(self.output_folder, name)
            )
        )
        jinja_dump("k6_config.js.j2", "{}/{}.js".format(self.output_folder, name), kwargs)

    def run(self):
        logger.info("run stress test in k6")
        logger.info(
            "every scenario would run by {} vus and last {} secconds".format(self.vu, self.duration)
        )
        Path(self.output_folder).mkdir(exist_ok=True)
        for scenario in self.scenarios:

            self.dump_config(scenario)
            # run k6
            command = [
                "scripts/k6",
                "run",
                "{}/{}.js".format(self.output_folder, scenario.name),
                "-u",
                str(self.vu),
                "-d",
                "{}s".format(self.duration),
                "--summary-trend-stats",
                "min,avg,med,max,p(90),p(95),p(99)",
                "--out",
                "influxdb={}".format(setting.INFLUXDB_URL),
                "--summary-export",
                "{}/result_{}.json".format(self.output_folder, scenario.name),
            ]
            click.echo("run command as below:")
            click.echo(" ".join(command))
            if self.dry_run is not None and self.dry_run:
                continue
            run_process(command)
