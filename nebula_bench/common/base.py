# -*- encoding: utf-8 -*-
import re
import time
from collections import deque
import csv
from pathlib import Path
from collections import namedtuple

from nebula2.gclient.net import ConnectionPool
from nebula2.Config import Config
from nebula2.data.ResultSet import ResultSet

from nebula_bench import setting
from nebula_bench.utils import logger


class CSVReader(object):
    def __init__(self, file):
        try:
            file = open(file)
        except TypeError:
            # "file" was already a pre-opened file-like object
            pass
        self.file = file
        self.reader = csv.reader(file)

    def __next__(self):
        try:
            return next(self.reader)
        except StopIteration:
            # reuse file on EOF
            self.file.seek(0, 0)
            return next(self.reader)


class NebulaClient(object):
    def __init__(
        self,
        max_connection=None,
        user=None,
        password=None,
        address=None,
        space=None,
        timeout=None,
    ):
        self.user = user or setting.NEBULA_USER
        self.password = password or setting.NEBULA_PASSWORD
        self.space = space or setting.NEBULA_SPACE
        self.config = Config()
        self.config.max_connection_pool_size = max_connection or setting.NEBULA_MAX_CONNECTION

        if timeout is not None:
            self.config.timeout = timeout

        address = address or setting.NEBULA_ADDRESS
        address_list = address.split(",")
        self.address = [(item.split(":")[0], int(item.split(":")[1])) for item in address_list]

        self.deque = deque(maxlen=self.config.max_connection_pool_size)

        # init connection pool
        self.connection_pool = ConnectionPool()
        # if the given servers are ok, return true, else return false
        ok = self.connection_pool.init(self.address, self.config)
        assert ok, "cannot connect the server, address is {}".format(address)

    def add_session(self):
        _session = self.connection_pool.get_session(self.user, self.password)
        _session.execute("USE {}".format(self.space))
        self.deque.append(_session)

    def release_session(self):
        _session = None
        try:
            _session = self.deque.pop()
        except:
            pass
        if _session is not None:
            _session.release()

    def execute(self, stmt):
        if len(self.deque) == 0:
            self.add_session()
        _session = self.deque.popleft()
        try:
            r = _session.execute(stmt)
        except Exception as e:
            logger.error("execute stmt error, e is {}".format(e))
            r = None
        finally:
            self.deque.append(_session)
        return r

    def release(self):
        for _session in self.deque:
            _session.release()
        self.connection_pool.close()


re_pattern = r"\$\{\}"


class StmtGenerator(object):
    def __init__(self, stmt_template, parameters, data_folder):
        """

        :param stmt_template: statement template
        :param parameters:  ((csv_file, index),)
        """
        self.csv_reader_list = []
        self.index_list = []
        self.stmt_template = stmt_template
        self.data_folder = Path(data_folder)

        for p in parameters:
            csv_file, index = p
            csv_path = str((self.data_folder / csv_file).absolute())
            csv_reader = CSVReader(csv_path)
            self.csv_reader_list.append(csv_reader)
            self.index_list.append(index)

    def __next__(self):
        _stmt = self.stmt_template
        for _index, csv_reader in enumerate(self.csv_reader_list):
            index = self.index_list[_index]

            line = ",".join(next(csv_reader))
            value = line.split("|")[index]

            _stmt = re.sub(re_pattern, value, _stmt, count=1)

        return _stmt


class ScenarioMeta(type):
    def __new__(cls, name, bases, attrs, *args, **kwargs):
        # super(ScenarioMeta, cls).__new__(cls, name, bases, attrs, *args, **kwargs)
        if name == "BaseScenario":
            return type.__new__(cls, name, bases, attrs)
        if attrs.get("name", None) is None:
            attrs["name"] = name

        return type.__new__(cls, name, bases, attrs)


class BaseScenario(metaclass=ScenarioMeta):
    abstract = True
    is_insert_scenario = False
    nGQL: str
    stage: dict
    csv_path: str
    csv_index: list
    name: str


class BaseQuery(object):
    queries: tuple


class BaseImport(object):
    pass
