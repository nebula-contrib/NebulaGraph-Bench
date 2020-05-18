# nebula-bench
Collection of benchmark services and tools for Nebula Graph

## Build

Note that you need to setup your Golang environment before build.

```shell
$ git clone https://github.com/dutor/nebula-bench.git
$ cd nebula-bench
$ go build ./bin/nb
```

## Usage

```shell
$ ./nb --bench-config=/path/to/the/config.json
```

### Benchmark Configuration
`nb` uses a json file, as its configuration, with some extensions like variable substitution and comments.

```json
// Variable definitions
var base = /path/to/base/dir/of/workload/file
{
    // General configurations
    ...
    "workload": {
        "file": "${base}/wordload.csv"
        ...
    }
}
```

#### General Configurations
  * `test-name`, name of this test.
  * `graph-daemons`, list of IP and port of **Nebula Graph** daemons
  * `user`, username.
  * `pass`, password.
  * `rate`, upper bound of QPS.
  * `concurrent`, number of synchronous connections.
  * `mysql-dsn`, DSN of MySQL, used to store the result of the benchmark, the format is as `user:pass@ip:port/database`.
  * `workload`, configrations for some type of workload, see following sections for details.

#### Workload Type
The type of workload specifies how the wordload data are generated. Common configurations for workload are:
  * `type`, type name of the workload. Options are: `"literal"`, `"template"`, `"unique"` and `"joined"`.

##### Literal Statement Workload
  * `file`, file that holds the raw nGQL queries, one query per line.
  * `repeatable`, load statement from the file repeatedly.

Example:
```json
{
    ...
	"workload": {
		"type": "literal",
		"file": "./go-3-hops.nGQL",
	}
}
```
##### Templated Statement Workload
  * `file`, CSV file that holds records to generate the statements.
  * `stmt-template`, statement template, see below for details.
  * `batch-count`, number of records to generate a single statement.
  * `csv-separator`, the separator used as delimiter between record fields.
  * `csv-skip-header`, number of records to skip as CSV header.

In the templated statement workload, you use placeholders in a templated statement to reference the fields from a CSV file. The placeholder is a non-negative number surrounded by a pair of `$` symbol. For example, `$2$` refers to the second field.
Besides, in order to generate a single statement from multiple records(specified by `batch-count`), you could enclose a segment of the template with `$LOOP$` and `$END$`.

Example:
```json
{
    ...
	"workload": {
		"type": "template",
		"file": "${base_dir}/dynamic/person_knows_person.csv",
		"batch-count": 40,
		"csv-separator": "|",
		"csv-skip-header": 1,
		"stmt-template": "INSERT EDGE knows() VALUES $LOOP$ $2$ -> $3$:()$END$"
	}
}
```

##### Uniuqe Statement Workload
  * `limit`, number of statements a unique query repeats.
  * `stmt`, the unique statement.

Example:
```json
{
    ...
	"workload": {
		"type": "unique",
        "limit": 10000,
		"stmt": "SHOW SPACES"
	}
}
```

##### Joined Statement Workload
  * `list`, list of other type of workload.

Example:
```json
{
    ...
	"workload": {
		"type": "joined",
        "list": [
            {
                "type": "literal"
                "file": "..."
                ...
            }, {
                "type": "tempalte"
                "file": "..."
                ...
            }, {
                "type": "tempalte"
                "file": "..."
                ...
            },
            ...
        ]
	}
}
```

## The LDBC SNB Workload

### Datagen
To be added.

### Schema
```
CREATE SPACE IF NOT EXISTS ldbc_snb(PARTITION_NUM = 1024)

USE ldbc_snb

CREATE TAG IF NOT EXISTS person(first_name string, last_name string, gender string, ip string, browser string)
CREATE TAG IF NOT EXISTS place(name string, type string, url string)
CREATE TAG IF NOT EXISTS organization(name string, type string, url string)
CREATE TAG IF NOT EXISTS post(time string, image string, ip string, browser string, language string, content string, length int)
CREATE TAG IF NOT EXISTS comment(time string, ip string, browser string, content string, length int)
CREATE TAG IF NOT EXISTS forum(time string, title string, type string)

CREATE EDGE IF NOT EXISTS knows()
CREATE EDGE IF NOT EXISTS is_part_of()
CREATE EDGE IF NOT EXISTS is_located_in()
CREATE EDGE IF NOT EXISTS study_at(year string)
CREATE EDGE IF NOT EXISTS work_at(year string)
CREATE EDGE IF NOT EXISTS has_post(time string)
CREATE EDGE IF NOT EXISTS has_comment(time string)
CREATE EDGE IF NOT EXISTS likes_post(time string)
CREATE EDGE IF NOT EXISTS likes_comment(time string)
CREATE EDGE IF NOT EXISTS is_reply_of_post(time string)
CREATE EDGE IF NOT EXISTS is_reply_of_comment(time string)
CREATE EDGE IF NOT EXISTS has_member(time string, type string)
```

### Import
```shell
$ ./nb --bench-config=ldbc/import/all.json
```

### Query Benchmark
```shell
$ ./nb --bench-config=ldbc/query/3-hop-knows.json
```
