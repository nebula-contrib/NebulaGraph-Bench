# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class FindShortestPath(BaseScenario):
    abstract = False
    nGQL = "FIND SHORTEST PATH FROM {} TO {} OVER *"
    csv_path = "social_network/dynamic/person_knows_person.csv"
    csv_index = [0, 1]
