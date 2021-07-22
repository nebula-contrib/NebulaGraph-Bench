import sys, inspect


def test_temp():
    module = sys.modules[__name__]
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            print(name)
            print(obj)


class Harris(object):
    pass
