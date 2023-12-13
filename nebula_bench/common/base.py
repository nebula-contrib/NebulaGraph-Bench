# -*- encoding: utf-8 -*-


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
    nGQL: str = ""
    value: str = ""
    stage: dict
    csv_path: str
    name: str
    vus = [50, 100, 200, 300, 500]
    rank: int = 0
