package util

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"regexp"
	"strconv"
)

const (
	PT_LITERAL  = "literal"
	PT_TEMPLATE = "template"
	PT_UNIQUE   = "unique"
	PT_JOINED   = "joined"
)

type Address struct {
	Host string `json:"host"`
	Port uint16 `json:"port"`
}

type WorkloadConfig struct {
	File          string           `json:"file"`
	Type          string           `json:"type"`
	Repeatable    bool             `json:"repeatable"`
	Batch         int              `json:"batch-count"`
	Limit         int64            `json:"limit"`
	CsvSkipHeader int              `json:"csv-skip-header"`
	CsvSeparator  string           `json:"csv-separator"`
	StmtTemplate  string           `json:"stmt-template"`
	Stmt          string           `json:"stmt"`
	List          []WorkloadConfig `json:"list"`
}

type BenchConfig struct {
	Name         string         `json:"test-name"`
	GraphDaemons []Address      `json:"graph-daemons"`
	User         string         `json:"user"`
	Pass         string         `json:"pass"`
	Space        string         `json:"space"`
	Rate         int            `json:"rate"`
	Concurrent   int            `json:"concurrent"`
	Workload     WorkloadConfig `json:"workload"`
	MysqlDSN     string         `json:"mysql-dsn"`
}

func (cfg *BenchConfig) ParseFromJson(content []byte) error {
	// Remove comments
	re := regexp.MustCompile(`(?sm)//.*?$|/\*.*?\*/`)
	content = []byte(re.ReplaceAllLiteralString(string(content), ""))
	// Parse and do variable substitution
	re = regexp.MustCompile(`var\s+(\w+?)\s*=\s*(\S+)`)
	vars := re.FindAllStringSubmatch(string(content), -1)
	content = []byte(re.ReplaceAllLiteralString(string(content), ""))
	if len(vars) != 0 {
		for _, vs := range vars {
			vname := vs[1]
			vvalue := vs[2]
			vre := regexp.MustCompile(fmt.Sprintf("\\$\\{%s\\}", vname))
			content = []byte(vre.ReplaceAllLiteralString(string(content), vvalue))
		}
	}
	return json.Unmarshal(content, cfg)
}

func (cfg *BenchConfig) ParseFromJsonFile(file string) error {
	if fd, err := os.Open(file); err == nil {
		defer fd.Close()
		var content []byte
		content, err = ioutil.ReadAll(fd)
		return cfg.ParseFromJson(content)
	} else {
		return err
	}
}

func (addr *Address) String() string {
	return string(addr.Host) + ":" + strconv.Itoa(int(addr.Port))
}

func (cfg BenchConfig) String() string {
	bytes, _ := json.MarshalIndent(cfg, "", "    ")
	return string(bytes)
}
