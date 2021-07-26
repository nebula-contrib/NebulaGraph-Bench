# nebula-bench

[中文文档](README_cn.md)

`Nebula-Bench` is a tool to test the nebula-graph benchmark by using [LDBC](https://ldbc.github.io/) dataset.

Currently, we use ldbc_snb_datagen [v0.3.3](https://github.com/ldbc/ldbc_snb_datagen_spark/tree/v0.3.3).
It only support nebula graph 2.0+ release.

The main features:

* Generate the LDBC dataset and then import into nebula-graph.
* nebula-graph benchmark. (WIP)

## How to use

### prepare

```bash
sudo yum install -y git \
                    make \
                    file \
                    libev \
                    libev-devel \
                    gcc \
                    wget \
                    python3 \
                    python3-devel \
                    java-1.8.0-openjdk \
                    maven 

```

```bash
git clone https://github.com/vesoft-inc/nebula-bench.git 
cd nebula-bench
pip3 install --user -r requirements.txt
python3 run.py --help
```

prepare nebula tools.

* [nebula-importer](https://github.com/vesoft-inc/nebula-importer)
* [xk6-nebula](https://github.com/HarrisChu/xk6-nebula)

```bash
sh scripts/setup.sh
```

After compilation, it would put binaries in `scripts` folder.

### generate ldbc data

```bash
python3 run.py data 
```

It would download the Hadoop automaticly, build the datagen jar, and then generate ldbc data.

To import the data more easier, split the file header to a `header.csv` file.
The result files in `${PWD}/target/data/test_data/`

More information

```bash
# generate sf10 ldbc data
python3 run.py data  -s 10

# change hadoop options
export HADOOP_CLIENT_OPTS="-Xmx8G"
python3 run.py data -s 100

# only generate, do not split the data
python3 run.py data -og

# split data, no need generate again.
python3 run.py data -os
```

### import data into nebula-graph

```bash
python3 run.py nebula importer
```

Render the import config file according to the header files, and then run nebula-importer.

```bash
# after prepare the data, you could import the data to any nebula graph as you want.
# space is mytest, graph address is 127.0.0.1:9669
python3 run.py nebula importer -s mytest -a 127.0.0.1:9669

# or using dotenv
cp env .env
# vi .env
python3 run.py nebula importer

# dry run, just create the import config file, and you can modify any configuration.
# by default, PARTITION_NUM is 24,REPLICA_FACTOR is 3.
python3 run.py nebula importer --dry-run
```

### nebula benchmark

Use [k6](https://github.com/k6io/k6) with [xk6-nebula](https://github.com/HarrisChu/xk6-nebula) extension.

Scenarios are in `nebula_bench/scenarios/`.

```bash
# show help
python3 run.py stress run --help

# run all scenarios with 100 virtual users, every scenario lasts 60 seconds.
python3 run.py stress run 

# run all scenarios with 10 virtual users, every scenario lasts 3 seconds.
python3 run.py stress run -vu 10 -d 3

# list all stress test scenarios
python3 run.py stress scenarios

# run go.Go1Step scenarios with 10 virtual users, every scenario lasts 3 seconds.
python3 run.py stress run -vu 10 -d 3 -scenario go.Go1Step
```

k6 config file, summary result and outputs are in `output` folder. e.g.

```bash
# you should install jq to parse json.
# how many checks
jq .metrics.checks output/result_Go1Step.json

# summary latency
jq .metrics.latency output/result_Go1Step.json

# summary error message 
awk -F ',' 'NR>1{print $NF}' output/output_Go1Step.csv |sort|uniq -c
```

or, just review the sumary result in stdout. e.g.

```bash
     ✓ IsSucceed

     █ setup

     █ teardown

     checks...............: 100.00% ✓ 113778      ✗ 0
     data_received........: 0 B     0 B/s
     data_sent............: 0 B     0 B/s
     iteration_duration...: min=747.84µs avg=52.76ms      med=40.77ms max=1.17s   p(90)=98.68ms p(95)=147.15ms  p(99)=263.03ms
     iterations...........: 113778  1861.550127/s
     latency..............: min=462      avg=49182.770298 med=37245   max=1160358 p(90)=93377   p(95)=142304.15 p(99)=258465.89
     responseTime.........: min=662      avg=52636.793537 med=40659   max=1177651 p(90)=98556.5 p(95)=147036.15 p(99)=262869.63
     vus..................: 100     min=0         max=100
     vus_max..............: 100     min=100       max=100
```

As one iteration has one check, it means run `113778` queries.

The unit of latency is `us`.

## and more

* The file with `aaa_xxYY_bbb` format, like `comment_hasTag_tag`, should be an edge, and the edge name shoud be `XX_YY`. Keep the same format with [ldbc_snb_interactive](https://github.com/ldbc/ldbc_snb_interactive/blob/main/cypher/queries/interactive-complex-1.cypher)
* Otherwise it should be a vertex tag.
* Different entity types might have same ID (e.g. Forum and Post).
