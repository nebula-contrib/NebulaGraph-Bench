package driver

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log"
	"runtime"
	"sync"
	"time"

	_ "github.com/go-sql-driver/mysql"
	"github.com/vesoft-inc/nebula-bench/util"
	nebula "github.com/vesoft-inc/nebula-go"
	graph "github.com/vesoft-inc/nebula-go/nebula/graph"
	"golang.org/x/time/rate"
)

var LatencySchema string

type Driver struct {
	counter      uint64
	lock         sync.Mutex
	config       *util.BenchConfig
	limiters     []*rate.Limiter
	clients      []*nebula.GraphClient
	cancellers   []context.CancelFunc
	workload     util.QueryWorkload
	sstats       *util.Stats
	cstats       *util.Stats
	wg           *sync.WaitGroup
	db           *sql.DB
	test_id      int64
	done         chan int
	outputDBOnce bool
}

func connectGraph(cfg *util.BenchConfig, retry uint) (client *nebula.GraphClient, err error) {
	var i uint
	for i <= retry {
		i++
		client, err = nebula.NewClient(cfg.GraphDaemons[0].String(), nebula.WithTimeout(0))
		if err != nil {
			time.Sleep(2)
			log.Println("failed to create the nebula client, we will try again.", err.Error())
			continue
		} else if err = client.Connect(cfg.User, cfg.Pass); err != nil {
			time.Sleep(2)
			log.Println("failed to connect the nebula server, we will try again.", err.Error())
			continue
		} else if _, err := client.Execute("USE " + cfg.Space); err != nil {
			client.Disconnect()
		}
		break
	}
	return
}

func NewDriver(cfg *util.BenchConfig, outputDBOnce bool) (*Driver, error) {
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
		c, e := connectGraph(cfg, 2)
		if e != nil {
			return nil, e
		}
		driver.clients = append(driver.clients, c)
	}

	for i := 0; i < cfg.Concurrent; i++ {
		limiter := rate.NewLimiter(rate.Limit(cfg.Rate/cfg.Concurrent), 16)
		driver.limiters = append(driver.limiters, limiter)
	}

	if p, e := util.NewWorkload(&cfg.Workload); e != nil {
		return nil, e
	} else {
		driver.workload = p
	}

	for cfg.MysqlDSN != "" {
		if db, e := sql.Open("mysql", cfg.MysqlDSN); e != nil {
			return nil, e
		} else if e := db.Ping(); e != nil {
			log.Println(e)
			return nil, e
		} else if res, e := db.Exec(LatencySchema); e != nil {
			log.Println(e)
			return nil, e
		} else {
			driver.db = db
			driver.test_id, _ = res.LastInsertId()
		}
		break
	}

	driver.config = cfg
	driver.sstats = util.NewStats("server-side", cfg.Name, cfg.MysqlTableName)
	driver.cstats = util.NewStats("client-side", cfg.Name, cfg.MysqlTableName)
	driver.outputDBOnce = outputDBOnce

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
			if resp, e := this.clients[idx].Execute(s); e != nil {
				log.Println(e)
				this.clients[idx].Disconnect()
				this.clients[idx], e = connectGraph(this.config, 4)
				this.sstats.AddErr()
				this.cstats.AddErr()
				if e != nil {
					log.Println(e)
					break Loop
				}
			} else if resp.GetErrorCode() != graph.ErrorCode_SUCCEEDED {
				log.Printf("Statement: %s, ErrorCode: %v, ErrorMsg: %s",
					s, resp.GetErrorCode(), resp.GetErrorMsg())
				this.sstats.AddErr()
				this.cstats.AddErr()
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
		ctx, canceller := context.WithCancel(context.Background())
		this.cancellers = append(this.cancellers, canceller)
		go this.send(i, ctx)
	}
	go func() {
		this.wg.Wait()
		this.sstats.Done()
		this.cstats.Done()
		if this.db != nil {
			this.sstats.WriteToDB(this.db, this.test_id, this.outputDBOnce)
			this.cstats.WriteToDB(this.db, this.test_id, this.outputDBOnce)
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
