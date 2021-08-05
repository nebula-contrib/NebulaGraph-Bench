# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class InsertPersonScenario(BaseScenario):
    is_insert_scenario = True
    nGQL = "INSERT VERTEX Person(firstName, lastName, gender, birthday, creationDate, locationIP, browserUsed) VALUES "
    abstract = False
    csv_path = "social_network/dynamic/person.csv"
    csv_index = [1, 2, 3, 4, 5, 6, 7]
