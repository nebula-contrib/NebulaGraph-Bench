# -*- encoding: utf-8 -*-
from nebula_bench.common.base import BaseScenario


class BatchInsertVertexScenario(BaseScenario):
    is_insert_scenario = True
    nGQL = "INSERT VERTEX Person(firstName, lastName, gender, birthday, creationDate, locationIP, browserUsed) VALUES "
    value = '{0}:("{1}", "{2}", "{3}", "{4}", datetime("{5}"), "{6}", "{7}")'
    abstract = False
    csv_path = "social_network/dynamic/person.csv"
    rank = 9999


class InsertVertexScenario(BaseScenario):
    is_insert_scenario = False
    nGQL = (
        "INSERT VERTEX Person(firstName, lastName, gender, birthday, creationDate, locationIP, browserUsed) VALUES "
        '{0}:("{1}", "{2}", "{3}", "{4}", datetime("{5}"), "{6}", "{7}")'
    )
    abstract = False
    csv_path = "social_network/dynamic/person.csv"
    rank = 9999


class BatchInsertEdgeScenario(BaseScenario):
    is_insert_scenario = True
    nGQL = "INSERT EDGE LIKES (creationDate) VALUES "
    value = '{0}->{1}:(datetime("{2}"))'
    abstract = False
    csv_path = "social_network/dynamic/person_likes_comment.csv"
    rank = 9999


class InsertEdgeScenario(BaseScenario):
    is_insert_scenario = False
    nGQL = 'INSERT EDGE LIKES (creationDate) VALUES {0}->{1}:(datetime("{2}"))'
    abstract = False
    csv_path = "social_network/dynamic/person_likes_comment.csv"
    rank = 9999
