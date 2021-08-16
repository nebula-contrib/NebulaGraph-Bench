# -*- coding: utf-8 -*-
from pathlib import Path

from nebula_bench import parser
from nebula_bench import setting
from nebula_bench.utils import logger
from nebula_bench.common.base import BaseScenario
from nebula_bench import utils


class BaseController(object):
    def __init__(self, data_folder=None, space=None, user=None, password=None, address=None):
        self.workspace_path = setting.WORKSPACE_PATH
        self.data_folder = data_folder or setting.DATA_FOLDER
        self.data_folder = Path(self.data_folder)
        self.space = space or setting.NEBULA_SPACE
        self.user = user or setting.NEBULA_USER
        self.password = password or setting.NEBULA_PASSWORD
        self.address = address or setting.NEBULA_ADDRESS


class NebulaController(BaseController):
    def __init__(
        self, data_folder=None, space=None, user=None, password=None, address=None, vid_type=None
    ):
        super().__init__(
            data_folder=data_folder,
            space=space,
            user=user,
            password=password,
            address=address,
        )
        self.vid_type = vid_type or "int"

    def import_space(self, dry_run=False):
        result_file = self.dump_nebula_importer()
        command = ["scripts/nebula-importer", "--config", result_file]
        if not dry_run:
            return utils.run_process(command)
        return 0

    def dump_nebula_importer(self):
        _type = "int64" if self.vid_type == "int" else "fixed_string(20)"
        p = parser.Parser(parser.NebulaDumper, self.data_folder)
        dumper = p.parse()
        kwargs = {}
        kwargs["space"] = self.space
        kwargs["user"] = self.user
        kwargs["password"] = self.password
        kwargs["address"] = self.address
        kwargs["vid_type"] = self.vid_type

        return dumper.dump(**kwargs)


class StressController(BaseController):
    def __init__(
        self,
        data_folder=None,
        space=None,
        user=None,
        password=None,
        address=None,
        vid_type=None,
    ):
        BaseController.__init__(
            self,
            data_folder=data_folder,
            space=space,
            user=user,
            password=password,
            address=address,
        )
        self.vid_type = vid_type or "int"
        self.record = None
        self.class_list = []

    def load_scenarios(self, scenario):
        package_name = "nebula_bench.scenarios"
        if scenario.lower() != "all":
            return utils.load_class(
                package_name,
                load_all=False,
                base_class=BaseScenario,
                class_name=scenario,
            )
        else:
            return utils.load_class(package_name, load_all=True, base_class=BaseScenario)

    def run(self, nebula_scenario):
        result_folder = "target/result"
        p = self.workspace_path / result_folder
        p.mkdir(exist_ok=True, parents=True)

        for _class in self.load_scenarios(nebula_scenario):
            module_name = _class.__module__.split(".")[-1]
            scenario = "{}.{}".format(module_name, _class.__name__)
            command = [
                "locust",
                "-f",
                "nebula_bench/locust_file.py",
                "--headless",
                "--nebula-scenario",
                scenario,
                "--csv",
                "{}/{}.csv".format(result_folder, _class.result_file_name),
                "--logfile",
                "{}/{}.log".format(result_folder, _class.result_file_name),
                "--html",
                "{}/{}.html".format(result_folder, _class.result_file_name),
            ]
            utils.run_process(command)
