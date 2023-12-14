# -*- coding: utf-8 -*-
import abc
from pathlib import Path
import enum
import datetime

from nebula_bench import setting
from nebula_bench.utils import jinja_dump

prefix_map = {
    "comment": "c-",
    "forum": "f-",
    "organisation": "o-",
    "person": "p-",
    "place": "l-",
    "post": "s-",
    "tag": "t-",
    "tagclass": "g-",
    "emailaddress": "e-",
    "language": "u-",
}


class PropTypeEnum(enum.Enum):
    INT = "int"
    DateTime = "datetime"
    String = "string"
    Timestamp = "timestamp"


class Base(object):
    def __init__(self, name=None, index=None):
        self.name = name
        self.index = index

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if other.__class__ != self.__class__:
            return False
        if self.name != other.name:
            return False

        return True


class Prop(Base):
    def __init__(self, name=None, index=None):
        Base.__init__(self, name, index)
        self.type = None


class Vertex(Base):
    def __init__(self, name=None, index=None):
        Base.__init__(self, name, index)
        self.path = None
        self.prop_list = []
        self.prefix = None


class Edge(Base):
    def __init__(self, name=None, index=None):
        Base.__init__(self, name, index)
        self.src_index = self.dst_index = None
        self.src_name = self.dst_name = None
        self.src_prefix = self.dst_prefix = None
        self.prop_list = []


class Parser(object):
    except_csv_file = [
        "person_email_emailaddress.csv",
        "person_speaks_language.csv",
    ]
    delimiter = "|"

    def __init__(self, dump_class, data_path):
        self.data_path = data_path
        self.dump_class = dump_class
        self.vertex_list = []
        self.edge_list = []

        # importer cannot use duplicate schema
        self.vertex_set = {}
        self.edge_set = {}

    def file_is_vertex(self, file_path):
        s = file_path.name.split("_")
        return len(s) == 1

    def guess_data_tpye(self, data):
        assert isinstance(data, str)
        if data.isnumeric():
            return PropTypeEnum.INT.value
        else:
            try:
                datetime_format = "%Y-%m-%dT%H:%M:%S.%f"
                datetime.datetime.strptime(data, datetime_format)
                return PropTypeEnum.DateTime.value
            except Exception as e:
                # not a valid date
                # print("warning: cannot parse the datetime, using string, exception: "+str(e))
                pass
            return PropTypeEnum.String.value

    def parse_vertex(self, file_path):
        file_name, _ = file_path.name.lower().rsplit(".csv", 1)
        name = file_name.capitalize()

        vertex = Vertex(name)
        vertex.path = str(file_path.absolute())
        vertex.prefix = prefix_map.get(name.lower(), "")

        header_path = Path(file_path.parent / (file_name + "_header.csv"))
        with open(str(header_path.absolute()), "r") as fl:
            header = fl.readline().strip()
            data = fl.readline().strip()

        header_list = header.split(self.delimiter)
        data_list = data.split(self.delimiter)

        assert len(header_list) == len(
            data_list
        ), "header length should be equle to data length, error file is {}".format(file_path)

        for index, h in enumerate(header_list):
            if h.strip().lower() == "id":
                vertex.index = index
            else:
                p = Prop()
                p.name = h
                p.index = index
                _type = self.guess_data_tpye(data_list[index])
                p.type = _type
                vertex.prop_list.append(p)

        self.vertex_list.append(vertex)
        self.vertex_set = set(self.vertex_list)

    def parse_edge(self, file_path):
        file_name, _ = file_path.name.rsplit(".csv", 1)
        src_vertex, name, dst_vertex = file_name.split("_", 2)
        char_list = []
        for c in name:
            if c.isupper():
                char_list.append("_{}".format(c))
            else:
                char_list.append(c.upper())

        char_list[0] = char_list[0].upper()
        changed_name = "".join(char_list)
        edge = Edge(changed_name)
        edge.path = str(file_path.absolute())

        header_path = Path(file_path.parent / (file_name + "_header.csv"))

        with open(str(header_path.absolute()), "r") as fl:
            header = fl.readline().strip()
            data = fl.readline().strip()

        header_list = header.split(self.delimiter)
        data_list = data.split(self.delimiter)

        assert len(header_list) == len(
            data_list
        ), "header length should be equle to data length, error file is {}".format(file_path)

        flag = True
        for index, h in enumerate(header_list):
            if h.lower() == src_vertex.lower() + ".id" and flag:
                # if the src and dst are same vertex, first is src and second is dst
                flag = not flag
                name = h.rsplit(".id", 1)[0].lower()
                edge.src_name, edge.src_index = name, index
                edge.src_prefix = prefix_map.get(name, "")
            elif h.lower() == dst_vertex.lower() + ".id":
                name = h.rsplit(".id", 1)[0].lower()
                edge.dst_name, edge.dst_index = name, index
                edge.dst_prefix = prefix_map.get(name, "")

            else:
                p = Prop()
                p.name = h
                p.index = index
                _type = self.guess_data_tpye(data_list[index])
                p.type = _type
                edge.prop_list.append(p)

        self.edge_list.append(edge)
        self.edge_set = set(self.edge_list)

    def parse_file(self, file_path):
        if self.file_is_vertex(file_path):
            self.parse_vertex(file_path)
        else:
            self.parse_edge(file_path)

    def parse(self, *args, **kwargs):
        for folder in ["dynamic", "static"]:
            folder_path = self.data_path / "social_network" / folder
            for file in folder_path.iterdir():
                assert isinstance(file, Path)
                if (
                    not file.is_file()
                    or not file.name.endswith("csv")
                    or file.name in self.except_csv_file
                    or file.name.endswith("_header.csv")
                ):
                    continue
                self.parse_file(file)

        return self.dump_class(self, *args, **kwargs)


class NebulaParser(Parser):
    pass


class Dumper(object):
    def __init__(self, parser):
        self._parser = parser
        self.workspace_path = setting.WORKSPACE_PATH

    @abc.abstractmethod
    def dump(self, *args, **kwargs):
        pass


class NebulaDumper(Dumper):
    def __init__(self, parser, result_file=None, template_file=None):
        Dumper.__init__(self, parser)
        self.space = self.root = self.password = self.address = None

        self.template_file = template_file
        self.result_file = result_file or "importer_config.yaml"

    def dump(self, *args, **kwargs):
        vid_type = kwargs.pop("vid_type", "int")
        enable_prefix = kwargs.pop("enable_prefix", False)
        if vid_type == "int":
            self.template_file = self.template_file or "nebula-import-vid-int.yaml.j2"
        elif vid_type == "string":
            self.template_file = self.template_file or "nebula-import-vid-string.yaml.j2"

        kwargs["vertex_list"] = self._parser.vertex_list
        kwargs["edge_list"] = self._parser.edge_list
        kwargs["vertex_set"] = self._parser.vertex_set
        kwargs["edge_set"] = self._parser.edge_set
        kwargs["enable_prefix"] = enable_prefix

        jinja_dump(self.template_file, self.result_file, kwargs)
        return self.result_file
