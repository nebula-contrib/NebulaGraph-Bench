# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class BaseMatchScenario(BaseScenario):
    abstract = True
    csv_path = "social_network/dynamic/person.csv"


class Match1Hop(BaseMatchScenario):
    nGQL = "MATCH (v1:Person)-[e:KNOWS]->(v2:Person) WHERE id(v1) == {0} RETURN v2"
