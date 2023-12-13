# -*- coding: utf-8 -*-
from pathlib import Path
import os
import json
from nebula_bench import parser
from nebula_bench import setting
from nebula_bench.utils import logger
from nebula_bench.common.base import BaseScenario
from nebula_bench import utils


class BaseController(object):
    def __init__(
        self,
        data_folder=None,
        space=None,
        user=None,
        password=None,
        address=None,
    ):
        self.workspace_path = setting.WORKSPACE_PATH
        self.data_folder = data_folder or setting.DATA_FOLDER
        self.data_folder = Path(self.data_folder)
        self.space = space or setting.NEBULA_SPACE
        self.user = user or setting.NEBULA_USER
        self.password = password or setting.NEBULA_PASSWORD
        self.address = address or setting.NEBULA_ADDRESS


class NebulaController(BaseController):
    def __init__(
        self,
        data_folder=None,
        space=None,
        user=None,
        password=None,
        address=None,
        vid_type=None,
        enable_prefix=None,
    ):
        super().__init__(
            data_folder=data_folder,
            space=space,
            user=user,
            password=password,
            address=address,
        )
        self.vid_type = vid_type or "int"
        self.enable_prefix = enable_prefix

    def import_space(self, dry_run=False):
        result_file = self.dump_nebula_importer()
        command = ["scripts/nebula-importer", "--config", result_file]
        if not dry_run:
            return utils.run_process(command)
        return 0

    def dump_nebula_importer(self):
        kwargs = {}
        if self.enable_prefix and self.vid_type == "int":
            raise Exception("must use prefix with vid type string")
        else:
            kwargs["enable_prefix"] = self.enable_prefix

        p = parser.Parser(parser.NebulaDumper, self.data_folder)
        dumper = p.parse()

        kwargs["space"] = self.space
        kwargs["user"] = self.user
        kwargs["password"] = self.password
        kwargs["address"] = self.address
        kwargs["vid_type"] = self.vid_type

        return dumper.dump(**kwargs)


class DumpController(object):
    def __init__(self):
        pass

    def export(self, folder, output, filetype):
        if filetype == "html":
            self._export_html(folder, output)
        elif filetype == "csv":
            self._export_csv(folder, output)
        else:
            raise Exception("not support filetype: %s" % filetype)

    def _export_html(self, folder, output):
        utils.jinja_dump("report.html.j2", output, {"data": self.get_data(folder)})

    def _export_csv(self, folder, output):
        utils.csv_dump(output, self.get_data(folder))

    def get_data(self, folder):
        # [
        #     {
        #         "case":{
        #             "name": "case1",
        #             "stmt": "stmt",
        #         },
        #         "k6":[
        #             {"vu": 200, "report":metric1},
        #             {"vu": 500, "report":metric2},
        #         ]
        #     }
        # ]
        data = list()
        if folder is None:
            return
        package_name = "nebula_bench.scenarios"
        scenarios = utils.load_class(package_name, load_all=True, base_class=BaseScenario)

        paths = sorted(Path(folder).iterdir(), key=os.path.getmtime)
        case = None
        for file in paths:
            if file.is_dir():
                continue
            n = file.name
            if not n.startswith("result") or not n.endswith(".json"):
                continue
            file_name = n.rstrip(".json")
            _, vu, case_name = file_name.split("_", 3)
            if case is not None and case["case"]["name"] != case_name:
                data.append(case)
                case = None
            if case is None:
                case = {}
                case["case"] = {}
                for s in scenarios:
                    if s.name == case_name:
                        case["case"]["stmt"] = s.nGQL
                        break
                case["case"]["name"] = case_name
                case["k6"] = list()

            file_path = Path(folder) / n
            with open(file_path, "r") as f:
                metric = json.load(f)

            k6 = {}
            k6["vu"] = int(vu)
            k6["report"] = metric
            case["k6"].append(k6)

        if case is not None:
            data.append(case)
        return data

    def serve(self, port=5000):
        import flask

        app = flask.Flask(__name__, template_folder=setting.WORKSPACE_PATH / "templates")

        @app.route("/", methods=["GET"])
        def index():
            current_output_name = flask.request.args.get("output", "")
            if current_output_name == "":
                latest = self.get_latest_output()
                if latest is None:
                    return "No output"
                current_output_name = Path(latest).name
            outputs_name = [Path(output).name for output in self.get_all_output()]

            return flask.render_template(
                "report.html.j2",
                data=self.get_data(
                    (setting.WORKSPACE_PATH / "output" / current_output_name).absolute()
                ),
                server=True,
                outputs=outputs_name,
                current_output=current_output_name,
            )

        app.run(host="0.0.0.0", port=port)

    def get_all_output(self):
        output_folder = setting.WORKSPACE_PATH / "output"
        if not output_folder.exists():
            return []
        paths = []
        folders = sorted(output_folder.iterdir(), key=os.path.getmtime)
        for folder in folders:
            if not folder.is_dir():
                continue
            paths.append(folder.absolute())
        return paths

    def get_latest_output(self):
        all = self.get_all_output()
        if len(all) == 0:
            return None
        return self.get_all_output()[-1]
