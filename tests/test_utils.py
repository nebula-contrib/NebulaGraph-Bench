# -*- encoding: utf-8 -*-
from nebula_bench.utils import load_class
from nebula_bench.common.base import BaseScenario


def test_load_class():
    clazzes = load_class("nebula_bench.scenarios", True, BaseScenario)
    print(len(clazzes))
    for c in clazzes:
        print(c)
