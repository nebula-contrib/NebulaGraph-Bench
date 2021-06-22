# -*- coding: utf-8 -*-
import time
from pathlib import Path
from datetime import datetime

from nebula_bench import parser
from nebula_bench import setting
from nebula_bench.utils import logger
from nebula_bench.common.base import BaseScenario, BaseQuery, NebulaClient
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

        self.nebula_client = NebulaClient(max_connection=5, address=self.address)
        self.nebula_session = self.nebula_client.connection_pool.get_session(
            self.user, self.password
        )
        self.nebula_session.execute("USE {}".format(self.space))

    def release(self):
        self.nebula_session.release()
        self.nebula_client.release()

    def update_config(self, module, config):
        assert module.upper() in ["GRAPH", "STORAGE", "META"]
        self.nebula_session.execute("UPDATE CONFIGS {}:{}".format(module.upper(), config))

    def submit_job(self, statement, timeout=1800, retry=5):
        job_id = job_status = None
        submit_succeeded = False
        for i in range(retry):
            r = self.nebula_session.execute(statement)
            if r.is_succeeded():
                row = next(r._data_set_wrapper)
                job_id = row.get_value(0).as_int()

                show_r = self.nebula_session.execute("SHOW JOB {}".format(job_id))
                assert show_r.is_succeeded()
                row = next(show_r._data_set_wrapper)
                job_status = row.get_value(2).as_string()
                if job_status != "FAILED":
                    submit_succeeded = True
                    break

            else:
                logger.warning("submit job failed, error message is {}".format(r.error_msg()))
            time.sleep(10)
        assert submit_succeeded, "this job does not submit successfully, job is <{}>".format(
            statement
        )
        logger.info("succeeded job <{}>, job id is <{}>".format(statement, job_id))
        timeout_time = time.time() + timeout
        while time.time() < timeout_time:
            show_r = self.nebula_session.execute("SHOW JOB {}".format(job_id))
            assert show_r.is_succeeded()
            row = next(show_r._data_set_wrapper)
            job_status = row.get_value(2).as_string()
            if job_status == "FINISHED":
                # job_id, command, start_time, stop_time,
                return (
                    row.get_value(0).as_int(),
                    row.get_value(1).as_string(),
                    row.get_value(3).as_datetime(),
                    row.get_value(4).as_datetime(),
                )
            elif job_status == "FAILED":
                logger.error("running job failed, job id is <{}>".format(job_id))
                raise Exception("job <{}> failed".format(job_id))

            time.sleep(2)

        raise Exception("timeout")

    def compact(self, timeout=3600):
        """
        TODO should move to another controller to test multiple import scenarios.
        :param timeout:
        :return:
        """
        self.nebula_session.execute("USE {}".format(self.space))
        return self.submit_job("SUBMIT JOB COMPACT", timeout)


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
        self.update_config("graph", "heartbeat_interval_secs=1")
        self.update_config("storage", "heartbeat_interval_secs=1")
        result_file = self.dump_nebula_importer()
        command = ["scripts/nebula-importer", "--config", result_file]
        if not dry_run:
            return utils.run_process(command)
        return 0

    def init_space(self):
        """
        create index and then rebuild
        :return:
        """
        self.update_config("graph", "heartbeat_interval_secs=1")
        self.update_config("storage", "heartbeat_interval_secs=1")
        r = self.nebula_session.execute(
            "CREATE TAG INDEX IF NOT EXISTS idx_person on Person(firstName(20))"
        )
        assert r.is_succeeded()
        self.submit_job("REBUILD TAG INDEX idx_person")

    def dump_nebula_importer(self):
        _type = "int64" if self.vid_type == "int" else "fixed_string(20)"
        statment = "CREATE SPACE IF NOT EXISTS {}(PARTITION_NUM = 24, REPLICA_FACTOR = 3, vid_type ={} );".format(
            self.space, _type
        )
        self.nebula_session.execute(statment)
        p = parser.Parser(parser.NebulaDumper, self.data_folder)
        dumper = p.parse()
        kwargs = {}
        kwargs["space"] = self.space
        kwargs["user"] = self.user
        kwargs["password"] = self.password
        kwargs["address"] = self.address
        kwargs["vid_type"] = self.vid_type

        return dumper.dump(**kwargs)

    def clean_spaces(self, keep=None):
        """
        delete the spaces
        """
        if keep is None:
            keep_spaces = []
        else:
            keep_spaces = [item.strip() for item in keep.split(",")]

        result = self.nebula_session.execute("show spaces;")

        for r in result:
            name = r.get_value(0).as_string()
            if name in keep_spaces:
                continue
            self.nebula_session.execute("drop space {}; ".format(name))


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


class QueryController(BaseController):
    def __init__(
        self,
        alert_class=None,
        report_class=None,
        space=None,
        user=None,
        password=None,
        address=None,
    ):
        BaseController.__init__(self, space=space, user=user, password=password, address=address)
        self.queries = []
        self.alert_class = alert_class
        self.report_class = report_class
        self.alert = []

    def load_queries(self):
        package_name = "nebula_bench.queries"
        query_classes = utils.load_class(package_name, load_all=True, base_class=BaseQuery)
        for _class in query_classes:
            for q in _class.queries:
                self.queries.append(q)

    def run(self):
        # balance leader
        self.nebula_session.execute("balance leader")
        time.sleep(10)

        # prevent leader change error, run some queries to update storage client.
        for _ in range(10):
            self.nebula_session.execute("GO 2 STEPS FROM 2608 OVER KNOWS")

        self.load_queries()
        for query in self.queries:
            self.run_statement(query.name, query.stmt)

        self.release()
        self.record.end_at = datetime.now()
        self.record.save()
        report_file = self.generate_report()
        utils.dingding_msg(
            "Finish query test, report html is http://{}/{}".format(
                self.record.execute_machine, report_file
            )
        )

        self.send_alert()

    def run_statement(self, name, stmt):
        logger.info("execute the statement <{}>, stmt is <{}>".format(name, stmt))
        count = 10
        latency_results = []
        response_results = []
        rows_counts = []
        succeeded = True
        latency = response_time = rows_count = 0
        for _ in range(count):
            now = time.monotonic()
            r = self.nebula_session.execute(stmt)
            if r.is_succeeded():
                # us
                response_results.append((time.monotonic() - now) * 1000 * 1000)
                latency_results.append(r.latency())
                rows_counts.append(r.row_size())
            else:
                logger.warning("execution is not succeeded, the err is <{}>".format(r.error_msg()))
                succeeded = False

        latency_results.sort()
        response_results.sort()
        if succeeded:
            # pop minimum and maximum value
            latency_results.pop(0)
            latency_results.pop(1)
            response_results.pop(0)
            response_results.pop(1)
            latency = sum(latency_results) / len(latency_results)
            response_time = sum(response_results) / len(latency_results)
            rows_count = sum(rows_counts) / len(rows_counts)
        self.save_statement_result(name, stmt, latency, response_time, rows_count, succeeded)

    def add_alert(self, stmt, latency, baseline_latency):
        self.alert.append((stmt, latency, baseline_latency))

    def send_alert(self, alter_class=None):
        pass

    def generate_report(self):
        if self.report_class is not None:
            return self.report_class(self).report()
