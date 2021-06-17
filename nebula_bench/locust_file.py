# -*- coding: utf-8 -*-
import importlib

from locust import events, LoadTestShape
from locust.argument_parser import parse_options


class StepLoadShape(LoadTestShape):
    stages = [
        {"duration": 6, "users": 10, "spawn_rate": 2},
        {"duration": 10, "users": 50, "spawn_rate": 10},
        {"duration": 20, "users": 100, "spawn_rate": 20},
        {"duration": 30, "users": 50, "spawn_rate": 10},
        # {"duration": 230, "users": 10, "spawn_rate": 10},
        # {"duration": 240, "users": 1, "spawn_rate": 1},
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

        return None


@events.init_command_line_parser.add_listener
def add_arguments(parser):
    group = parser.add_argument_group(
        "customize nebula arguments",
        "",
    )
    group.add_argument(
        "--nebula-scenario",
        type=str,
        help="stress test scenario name, e.g. match.MatchPerson",
        env_var="",
        default="",
    ),


p = parse_options()
scenario = p.__dict__["nebula_scenario"]

if scenario == "":
    print("need scenario")
    exit
else:
    print("run the scenario {}".format(scenario))
    print("\n")
    module, clazz = scenario.split(".")
    _module = importlib.import_module(".".join(["nebula_bench.scenarios", module]))
    User = getattr(_module, clazz)
    print("statement is {}".format(User.statement))
