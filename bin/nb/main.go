package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/signal"
	"runtime/pprof"
	"strconv"
	"sync"
	"syscall"

	"github.com/vesoft-inc/nebula-bench/driver"
	"github.com/vesoft-inc/nebula-bench/util"
)

type BenchContext struct {
	http    *http.Server
	current *driver.Driver
	wg      *sync.WaitGroup
}

var bctx *BenchContext = nil

// Command line flags
var flagBenchFile string
var flagHttpPort int
var cpuProfile string

func initFlags() {
	flag.StringVar(&flagBenchFile, "bench-config", "", "Path to the configuration file for the local mode")
	flag.IntVar(&flagHttpPort, "port", 3728, "Port to listen on for the server mode")
	flag.StringVar(&cpuProfile, "cpu-profile", "", "Turn on CPU profiling if this is a non-empty filename")
}

func startWithServerMode() error {
	server := &http.Server{Addr: ":" + strconv.Itoa(flagHttpPort)}
	http.HandleFunc("/start", startTaskHandler)
	bctx.wg.Add(1)
	bctx.http = server
	go func() {
		e := bctx.http.ListenAndServe()
		if e != http.ErrServerClosed {
			log.Fatal(e)
		}
		bctx.wg.Done()
	}()
	return nil
}

func startWithLocalMode() error {
	config := &util.BenchConfig{}
	if e := config.ParseFromJsonFile(flagBenchFile); e != nil {
		return e
	}

	fmt.Printf("bench-config: %v\n", config)

	if d, e := driver.NewDriver(config); e != nil {
		return e
	} else {
		bctx.current = d
	}
	bctx.current.Start()
	bctx.wg.Add(1)
	go func() {
		<-bctx.current.Done()
		bctx.wg.Done()
		bctx.current = nil
	}()

	return nil
}

func main() {
	bctx = &BenchContext{wg: &sync.WaitGroup{}}
	initFlags()
	flag.Parse()
	log.SetFlags(log.LstdFlags | log.Lshortfile)

	if cpuProfile != "" {
		if f, e := os.Create(cpuProfile); e != nil {
			log.Fatal(e)
		} else {
			pprof.StartCPUProfile(f)
			defer pprof.StopCPUProfile()
		}
	}

	if flagBenchFile != "" {
		if e := startWithLocalMode(); e != nil {
			log.Fatal(e)
		}
	} else {
		if e := startWithServerMode(); e != nil {
			log.Fatal(e)
		}
	}

	sigchan := make(chan os.Signal, 1)
	signal.Notify(sigchan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigchan
		log.Println("Stopping")
		if bctx.http != nil {
			ctx, cancel := context.WithCancel(context.Background())
			bctx.http.Shutdown(ctx)
			cancel()
		}
		if bctx.current != nil {
			bctx.current.Stop()
		}
	}()

	bctx.wg.Wait()
}

func startTaskHandler(w http.ResponseWriter, r *http.Request) {
	if bctx.current != nil {
		io.WriteString(w, "Already running")
		return
	}

	switch r.Method {
	case http.MethodGet:
		io.WriteString(w, "Please POST a bench config in json format")
	case http.MethodPost:
		config := &util.BenchConfig{}
		body, _ := ioutil.ReadAll(r.Body)
		if e := config.ParseFromJson(body); e != nil {
			io.WriteString(w, "Illegal json")
			break
		}
		if d, e := driver.NewDriver(config); e != nil {
			io.WriteString(w, "Create Driver failed")
			break
		} else {
			bctx.current = d
		}

		bctx.current.Start()

		bctx.wg.Add(1)
		go func() {
			<-bctx.current.Done()
			bctx.current = nil
			bctx.wg.Done()
		}()
	default:
		io.WriteString(w, "Method not supported")
	}
}
