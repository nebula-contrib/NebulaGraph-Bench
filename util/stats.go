package util

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"strconv"
	"sync"
	"time"
)

const (
	kMaxLatency  = 1000000000 // Microseconds
	kBucketWidth = 100        // Microseconds
	kBucketNum   = kMaxLatency/kBucketWidth + 1
	kInterval    = 10 // Seconds
)

type Metric struct {
	id      int64
	ts      int64
	samples int64
	qps     int64
	avg     int64
	p999    int64
	p99     int64
	p95     int64
}

type Histogram struct {
	buckets []uint32
	num     int64
	start   time.Time
}

type Stats struct {
	name    string
	done    chan bool
	ticker  *time.Ticker
	current *Histogram
	overall *Histogram
	trends  []*Metric
	lock    sync.Mutex
	lastid  int64
}

func NewStats(name string) *Stats {
	stats := &Stats{}
	stats.current = newHist()
	stats.overall = newHist()
	stats.name = name
	stats.done = make(chan bool)
	stats.lastid = 0
	stats.ticker = time.NewTicker(kInterval * time.Second)
	go stats.tick()
	return stats
}

func newHist() *Histogram {
	hist := &Histogram{}
	hist.buckets = make([]uint32, kBucketNum)
	hist.start = time.Now()
	hist.num = 0
	return hist
}

func (this *Stats) Add(us int) {
	idx := us / kBucketWidth
	if idx >= kBucketNum {
		idx = kBucketNum - 1
	}
	this.lock.Lock()
	this.current.buckets[idx]++
	this.current.num++
	this.overall.buckets[idx]++
	this.overall.num++
	this.lock.Unlock()
}

func (this *Stats) collect(hist *Histogram) *Metric {
	metric := &Metric{}
	if hist.num == 0 {
		return metric
	}
	duration := time.Since(hist.start)
	ms := duration.Milliseconds()
	// Ignore this interval if too short
	if ms == 0 {
		return metric
	}
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
	return metric
}

func (this *Stats) tick() {
	var metric *Metric
Loop:
	for {
		select {
		case <-this.done:
			metric = this.collect(this.current)
			this.trends = append(this.trends, metric)
			log.Printf("[%s] %+v\n", this.name, *metric)
			break Loop
		case <-this.ticker.C:
			this.lock.Lock()
			cur := this.current
			this.current = newHist()
			this.lock.Unlock()
			metric = this.collect(cur)
			this.trends = append(this.trends, metric)
			log.Printf("[%s] %+v\n", this.name, *metric)
		}
	}
	this.done <- true
}

func (this *Stats) Done() {
	this.ticker.Stop()
	this.done <- true
	<-this.done
}

func (this *Stats) PlotTrends(file string) error {
	return nil
}

func (this *Stats) WriteTrendsToCSV(file string) error {
	var writer *csv.Writer
	if f, e := os.Create(file); e != nil {
		return e
	} else {
		defer f.Close()
		writer = csv.NewWriter(f)
		defer writer.Flush()
	}
	writer.Comma = []rune("\t")[0]

	var rows [][]string
	rows = append(rows, []string{"id", "ts", "qps", "avg", "P99", "p95", "P999", "samples"})
	for _, m := range this.trends {
		var row []string
		row = append(row, strconv.FormatInt(m.id, 10))
		row = append(row, strconv.FormatInt(m.ts, 10))
		row = append(row, strconv.FormatInt(m.qps, 10))
		row = append(row, strconv.FormatInt(m.avg, 10))
		row = append(row, strconv.FormatInt(m.p99, 10))
		row = append(row, strconv.FormatInt(m.p95, 10))
		row = append(row, strconv.FormatInt(m.p999, 10))
		row = append(row, strconv.FormatInt(m.samples, 10))
		rows = append(rows, row)
	}
	writer.WriteAll(rows)

	return nil
}

func (this *Stats) WriteHistToCSV(file string) error {
	var writer *csv.Writer
	if f, e := os.Create(file); e != nil {
		return e
	} else {
		defer f.Close()
		writer = csv.NewWriter(f)
		defer writer.Flush()
	}
	writer.Comma = []rune("\t")[0]

	var rows [][]string
	rows = append(rows, []string{"ms", "samples"})
	var maxBucket int = kBucketNum
	for i := kBucketNum - 1; i > 0; i-- {
		if this.overall.buckets[i] != 0 {
			maxBucket = i
			break
		}
	}
	step := 1000 / kBucketWidth
	for i := 0; i < maxBucket; i += step {
		var row []string
		ms := int64(i / step)
		var sum int64 = 0
		for j := i; j < i+step; j++ {
			sum += int64(this.overall.buckets[j])
		}
		row = append(row, strconv.FormatInt(ms, 10))
		row = append(row, strconv.FormatInt(sum, 10))
		rows = append(rows, row)
	}
	writer.WriteAll(rows)

	return nil
}

func (this *Stats) OverallMetric() string {
	return fmt.Sprintf("[%s][overall] %+v", this.name, *this.collect(this.overall))
}

func (this *Stats) WriteToDB(db *sql.DB, test_id int64) {
	for _, m := range this.trends {
		if _, e := db.Exec(`INSERT INTO latency(type, timestamp,samples,qps,average,p95,p99,p999,test)
        VALUES(?,?,?,?,?,?,?,?,?)`, this.name, m.ts, m.samples, m.qps, m.avg, m.p95, m.p99, m.p999, test_id); e != nil {
			log.Fatal(e)
		}
	}
}
