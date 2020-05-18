package util

import (
    "time"
    "log"
    "sync"
    "database/sql"
)

const (
    kMaxLatency         = 1000000000        // Microseconds
    kBucketWidth        = 100               // Microseconds
    kBucketNum          = kMaxLatency/kBucketWidth + 1
    kInterval           = 10               // Seconds
)

type Metric struct {
    id                  int64
    ts                  int64
    samples             int64
    qps                 int64
    avg                 int64
    p999                int64
    p99                 int64
    p95                 int64
}

type Histogram struct {
    buckets             []uint32
    num                 int64
    start               time.Time
}

type Stats struct {
    name                string
    done                chan bool
    ticker             *time.Ticker
    hist                Histogram
    trends              []*Metric
    lock                sync.Mutex
    lastid              int64
}

func NewStats(name string) *Stats {
    stats := &Stats{}
    stats.hist = newHist()
    stats.name = name
    stats.done = make(chan bool)
    stats.lastid = 0
    stats.ticker = time.NewTicker(kInterval * time.Second)
    go stats.tick()
    return stats
}

func newHist() Histogram {
    var hist Histogram
    hist.buckets = make([]uint32, kBucketNum)
    hist.start = time.Now()
    hist.num = 0
    return hist
}

func (this *Stats) Add(us int) {
    idx := us / kBucketWidth;
    if idx >= kBucketNum {
        idx = kBucketNum - 1
    }
    this.lock.Lock()
    this.hist.buckets[idx]++
    this.hist.num++
    this.lock.Unlock()
}

func (this *Stats) collect(hist Histogram) {
    if hist.num == 0 {
        return
    }
    duration := time.Since(hist.start)
    ms := duration.Milliseconds()
    // Ignore this interval if too short
    if ms == 0 {
        return
    }
    metric := &Metric{}
    metric.qps = hist.num * 1000 / ms
    metric.id = this.lastid
    this.lastid++
    metric.samples = hist.num
    metric.ts = time.Now().Unix()
    var total_us int64 = 0
    var p999_limit int64 = hist.num / 1000
    var p999_count int64 = 0
    var p999 int64 = 0
    var p99_limit int64 = hist.num / 100
    var p99_count int64 = 0
    var p99 int64 = 0
    var p95_limit int64 = hist.num * 5 / 100
    var p95_count int64 = 0
    var p95 int64 = 0
    for i := kBucketNum - 1; i >= 0; i-- {
        total_us += kBucketWidth * int64(hist.buckets[i]) * int64(i)
        if p999_count < p999_limit {
            p999_count += int64(hist.buckets[i])
            p999 = int64(i * kBucketWidth)
        }
        if p99_count < p99_limit {
            p99_count += int64(hist.buckets[i])
            p99 = int64(i * kBucketWidth)
        }
        if p95_count < p95_limit {
            p95_count += int64(hist.buckets[i])
            p95 = int64(i * kBucketWidth)
        }
    }
    metric.avg = total_us / hist.num
    metric.p999 = p999
    metric.p99 = p99
    metric.p95 = p95
    log.Printf("[%s] %+v\n", this.name, *metric)
    this.trends = append(this.trends, metric)
}

func (this *Stats) tick() {
Loop:
    for {
        select {
        case <-this.done:
            this.collect(this.hist)
            break Loop
        case <-this.ticker.C:
            this.lock.Lock()
            cur := this.hist
            this.hist = newHist()
            this.lock.Unlock()
            this.collect(cur)
        }
    }
    this.done <- true
}

func (this *Stats) Done() {
    this.ticker.Stop()
    this.done <- true
    <-this.done
}

func (this *Stats) WriteToDB(db *sql.DB, test_id int64) {
    for _,m := range this.trends {
        if _,e := db.Exec(`INSERT INTO latency(type, timestamp,samples,qps,average,p95,p99,p999,test)
        VALUES(?,?,?,?,?,?,?,?,?)`, this.name, m.ts, m.samples, m.qps, m.avg, m.p95, m.p99, m.p999, test_id); e != nil {
            log.Fatal(e)
        }
    }
}
