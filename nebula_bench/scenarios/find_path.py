# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class FindShortestPath(BaseScenario):
    abstract = False
    nGQL = "FIND SHORTEST PATH FROM {0} TO {1} OVER * YIELD path as p"
    csv_path = "social_network/dynamic/person_knows_person.csv"
    rank = 100
