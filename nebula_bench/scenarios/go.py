# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class BaseGoScenario(BaseScenario):
    abstract = True
    nGQL = "GO 1 STEP FROM {0} OVER KNOWS yield KNOWS.creationDate"
    csv_path = "social_network/dynamic/person.csv"


class Go1StepEdge(BaseGoScenario):
    abstract = False
    nGQL = "GO 1 STEP FROM {0} OVER KNOWS yield KNOWS.creationDate"


class Go2StepEdge(BaseGoScenario):
    abstract = False
    nGQL = "GO 2 STEP FROM {0} OVER KNOWS yield KNOWS.creationDate"


class Go3StepEdge(BaseGoScenario):
    abstract = False
    nGQL = "GO 3 STEP FROM {0} OVER KNOWS yield KNOWS.creationDate"


class Go1StepDst(BaseGoScenario):
    abstract = False
    nGQL = "GO 1 STEP FROM {0} OVER KNOWS yield $$.Person.firstName"


class Go2StepDst(BaseGoScenario):
    abstract = False
    nGQL = "GO 2 STEP FROM {0} OVER KNOWS yield $$.Person.firstName"


class Go3StepDst(BaseGoScenario):
    abstract = False
    nGQL = "GO 3 STEP FROM {0} OVER KNOWS yield $$.Person.firstName"
