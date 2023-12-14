# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class BaseFindShortestPath(BaseScenario):
    abstract = True
    nGQL = "FIND SHORTEST PATH FROM {0} TO {1} OVER * YIELD path as p"
    csv_path = "social_network/dynamic/person_knows_person.csv"
    rank = 100


class FindShortestPath(BaseFindShortestPath):
    abstract = False
    nGQL = "FIND SHORTEST PATH FROM {0} TO {1} OVER * YIELD path as p"


class FindShortestNoVidPath(BaseFindShortestPath):
    abstract = False
    nGQL = "FIND SHORTEST PATH FROM {0} TO -1 OVER * YIELD path as p"
