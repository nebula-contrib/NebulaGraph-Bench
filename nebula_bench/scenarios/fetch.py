# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class FetchTag(BaseScenario):
    abstract = False
    nGQL = "FETCH PROP ON Person {0} YIELD Person.firstName, Person.lastName, Person.gender, Person.birthday, Person.creationDate, Person.locationIP, Person.browserUsed"
    csv_path = "social_network/dynamic/person.csv"


class FetchEdge(BaseScenario):
    abstract = False
    nGQL = "FETCH PROP ON KNOWS {0} -> {1} YIELD KNOWS.creationDate"
    csv_path = "social_network/dynamic/person_knows_person.csv"
