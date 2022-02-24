# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class BaseGoScenario(BaseScenario):
    abstract = True
    nGQL = "GO 1 STEP FROM {} OVER KNOWS yield KNOWS.creationDate"
    csv_path = "social_network/dynamic/person.csv"
    csv_index = [0]


class Go1Step(BaseGoScenario):
    abstract = False
    nGQL = "GO 1 STEP FROM {} OVER KNOWS yield KNOWS.creationDate"


class Go2Step(BaseGoScenario):
    abstract = False
    nGQL = "GO 2 STEP FROM {} OVER KNOWS yield KNOWS.creationDate"


class Go3Step(BaseGoScenario):
    abstract = False
    nGQL = "GO 3 STEP FROM {} OVER KNOWS yield KNOWS.creationDate"
