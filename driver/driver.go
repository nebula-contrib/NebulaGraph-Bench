package driver

import (
    "log"
    "fmt"
    "time"
    "context"
    "sync"
    "errors"
    "runtime"
    "database/sql"
    "golang.org/x/time/rate"
    _ "github.com/go-sql-driver/mysql"
    "github.com/dutor/nebula-bench/util"
    nebula "github.com/vesoft-inc/nebula-go"
    graph "github.com/vesoft-inc/nebula-go/nebula/graph"
)

type Driver struct {
    counter         uint64
    lock            sync.Mutex
    config         *util.BenchConfig
    limiters     []*rate.Limiter
    clients      []*nebula.GraphClient
    cancellers    []context.CancelFunc
    workload        util.QueryWorkload
    sstats         *util.Stats
    cstats         *util.Stats
    wg             *sync.WaitGroup
    db             *sql.DB
    test_id         int64
    done            chan int
}

func NewDriver(cfg *util.BenchConfig) (*Driver, error) {
    if cfg == nil {
        return nil, errors.New("BenchConfig is nil")
    }
    if len(cfg.GraphDaemons) == 0 {
        return nil, errors.New("graph-daemons must be specified")
    }
    if cfg.Concurrent <= 0 {
        cfg.Concurrent = runtime.NumCPU()
        log.Printf("Use number of CPU as `concurrent': %v", cfg.Concurrent)
    }

    driver := &Driver{}
    for i := 0; i < cfg.Concurrent; i++ {
        if c,e := nebula.NewClient(cfg.GraphDaemons[0].String(), nebula.WithTimeout(0)); e != nil {
            return nil, e
        } else if e = c.Connect(cfg.User, cfg.Pass); e != nil {
            return nil, e
        } else if _,e := c.Execute("USE " + cfg.Space); e != nil {
            return nil, e
        } else {
            driver.clients = append(driver.clients, c)
        }
    }

    for i := 0; i < cfg.Concurrent; i++ {
        limiter := rate.NewLimiter(rate.Limit(cfg.Rate / cfg.Concurrent), 16)
        driver.limiters = append(driver.limiters, limiter)
    }

    if p,e := util.NewWorkload(&cfg.Workload); e != nil {
        return nil,e
    } else {
        driver.workload = p
    }

    for ; cfg.MysqlDSN != ""; {
        if db,e := sql.Open("mysql", cfg.MysqlDSN); e != nil {
            return nil, e
        } else if e := db.Ping(); e != nil {
            log.Println(e)
            break
        } else if res,e := db.Exec(`INSERT INTO tests(name) VALUES(?)`, cfg.Name); e != nil {
            log.Println(e)
            break
        } else {
            driver.db = db
            driver.test_id,_ = res.LastInsertId()
        }
        break
    }

    driver.config = cfg
    driver.sstats = util.NewStats("server-side")
    driver.cstats = util.NewStats("client-side")

    return driver, nil
}

func (this *Driver) send(idx int, ctx context.Context) {
    defer this.wg.Done()
    c := this.workload.Stream()
Loop:
    for {
        select {
        case <-ctx.Done():
            break Loop
        default:
            this.limiters[idx].Wait(ctx)
            s, ok := <-c
            if !ok {
                break Loop
            }
            start := time.Now()
            if resp,e := this.clients[idx].Execute(s); e != nil {
                log.Println(e)
            } else if resp.GetErrorCode() != graph.ErrorCode_SUCCEEDED {
                log.Printf("Statement: %s, ErrorCode: %v, ErrorMsg: %s",
                           s, resp.GetErrorCode(), resp.GetErrorMsg())
            } else {
                this.sstats.Add(int(resp.LatencyInUs))
                this.cstats.Add(int(time.Since(start).Microseconds()))
            }
        }
    }
}

func (this *Driver) Start() {
    n := this.config.Concurrent
    this.wg = &sync.WaitGroup{}
    this.wg.Add(n)
    this.done = make(chan int)
    for i := 0; i < n; i++ {
        ctx,canceller := context.WithCancel(context.Background())
        this.cancellers = append(this.cancellers, canceller)
        go this.send(i, ctx)
    }
    go func() {
        this.wg.Wait()
        this.sstats.Done()
        this.cstats.Done()
        if this.db != nil {
            this.sstats.WriteToDB(this.db, this.test_id)
            this.cstats.WriteToDB(this.db, this.test_id)
        }
        this.sstats.WriteTrendsToCSV("server-side-qps-latency-trends.csv")
        this.sstats.WriteHistToCSV("server-side-latency-hist.csv")
        fmt.Println(this.sstats.OverallMetric())
        fmt.Println(this.cstats.OverallMetric())
        this.done <- 0
    }()
}

func (this *Driver) Stop() {
    for _, canceller := range this.cancellers {
        canceller()
    }
}

func (this *Driver) Done() <-chan int {
    return this.done
}
