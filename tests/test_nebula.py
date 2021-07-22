def test_nebula():
    from nebula2.gclient.net import ConnectionPool
    from nebula2.Config import Config

    # define a config
    config = Config()
    config.max_connection_pool_size = 200
    # init connection pool
    connection_pool = ConnectionPool()
    # if the given servers are ok, return true, else return false
    ok = connection_pool.init([("192.168.8.152", 9669)], config)
    l = []
    session = connection_pool.get_session("root", "nebula")
    r = session.execute("Use nba")
    print(r.is_succeeded())
    with open("/Users/harrischu/code/nebula-console/test.2", 'r') as fl:
        data = fl.read()

    r = session.execute(data)
    print(r.is_succeeded())
    print(r.error_msg())
