# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class BaseLookupScenario(BaseScenario):
    abstract = True
    nGQL = "GO 1 STEP FROM {0} OVER KNOWS yield KNOWS.creationDate"
    csv_path = "social_network/dynamic/person.csv"


class LookUp(BaseLookupScenario):
    abstract = False
    nGQL = 'LOOKUP ON Person WHERE Person.firstName == "{1}" YIELD Person.firstName, Person.lastName, Person.gender, Person.birthday, Person.creationDate, Person.locationIP, Person.browserUsed'
