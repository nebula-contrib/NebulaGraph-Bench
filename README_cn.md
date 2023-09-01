# NebulaGraph Bench

`NebulaGraph Bench` 用于测试 NebulaGraph 的基线性能数据，使用 LDBC v0.3.3 的标准数据集。

当前只适用于 NebulaGraph v2.0 以上版本。

主要功能:

* 生产 LDBC 数据集并导入 NebulaGraph。
* 用 k6 进行压测。

## 工具依赖

|   NebulaGraph Bench    |     NebuaGraph     | NebulaGraph Importer |   K6 Plugin  |   ldbc_snb_datagen  |   NebulaGraph go    |
|:-----------------:|:-------------:|:---------------:|:------------:|:-------------------:|:--------------:|
|       [v0.2](https://github.com/vesoft-inc/nebula-bench/releases/tag/v0.2)        |    [v2.0.1](https://github.com/vesoft-inc/nebula-graph/releases/tag/v2.0.1)     |     [v2.0.0-ga](https://github.com/vesoft-inc/nebula-importer/releases/tag/v2.0.0-ga)   |    [v0.0.6](https://github.com/vesoft-inc/k6-plugin/releases/tag/v0.0.6)    |       [v0.3.3](https://github.com/ldbc/ldbc_snb_datagen_spark/tree/v0.3.3)        |     [v2.0.0-ga](https://github.com/vesoft-inc/nebula-go/releases/tag/v2.0.0-ga)  |
|       [v1.0.0](https://github.com/vesoft-inc/nebula-bench/releases/tag/v1.0.0)      |    [v2.5.0](https://github.com/vesoft-inc/nebula-graph/releases/tag/v2.5.0) / [v2.5.1](https://github.com/vesoft-inc/nebula-graph/releases/tag/v2.5.1)    |     [v2.5.1](https://github.com/vesoft-inc/nebula-importer/releases/tag/v2.5.1)      |    [v0.0.7](https://github.com/vesoft-inc/k6-plugin/releases/tag/v0.0.7)    |       [v0.3.3](https://github.com/ldbc/ldbc_snb_datagen_spark/tree/v0.3.3)         |     [v2.5.1](https://github.com/vesoft-inc/nebula-go/releases/tag/v2.5.1)     |
|       [v1.0.0](https://github.com/vesoft-inc/nebula-bench/releases/tag/v1.0.0)      |    [v2.6.0](https://github.com/vesoft-inc/nebula/releases/tag/v2.6.0) / [v2.6.1](https://github.com/vesoft-inc/nebula/releases/tag/v2.6.1) / [v2.6.2](https://github.com/vesoft-inc/nebula/releases/tag/v2.6.2)    |     [v2.6.0](https://github.com/vesoft-inc/nebula-importer/releases/tag/v2.6.0)      |    [v0.0.8](https://github.com/vesoft-inc/k6-plugin/releases/tag/v0.0.8)    |      [v0.3.3](https://github.com/ldbc/ldbc_snb_datagen_spark/tree/v0.3.3)         |     [v2.6.0](https://github.com/vesoft-inc/nebula-go/releases/tag/v2.6.0)     |
|       [v1.1.0](https://github.com/vesoft-inc/nebula-bench/releases/tag/v1.1.0)      |    [v3.0.0](https://github.com/vesoft-inc/nebula/releases/tag/v3.0.0) /  [v3.0.1](https://github.com/vesoft-inc/nebula/releases/tag/v3.0.1) |     [v3.0.0](https://github.com/vesoft-inc/nebula-importer/releases/tag/v3.0.0)      |    [v0.0.9](https://github.com/vesoft-inc/k6-plugin/releases/tag/v0.0.9)    |        [v0.3.3](https://github.com/ldbc/ldbc_snb_datagen_spark/tree/v0.3.3)        |     [v3.0.0](https://github.com/vesoft-inc/nebula-go/releases/tag/v3.0.0)     |
|       [v1.2.0](https://github.com/vesoft-inc/nebula-bench/releases/tag/v1.2.0)      |    [v3.1.0](https://github.com/vesoft-inc/nebula/releases/tag/v3.1.0)     |     [v3.1.0](https://github.com/vesoft-inc/nebula-importer/releases/tag/v3.1.0)      |    [v1.0.0](https://github.com/vesoft-inc/k6-plugin/releases/tag/v1.0.0)    |        [v0.3.3](https://github.com/ldbc/ldbc_snb_datagen_spark/tree/v0.3.3)        |     NONE       |
|       master      |    nightly    |     [v3.2.0](https://github.com/vesoft-inc/nebula/releases/tag/v3.2.0)      |    [v1.0.1](https://github.com/vesoft-inc/k6-plugin/releases/tag/v1.0.1)    |     [v0.3.3](https://github.com/ldbc/ldbc_snb_datagen_spark/tree/v0.3.3)      |     NONE       |
## 使用说明

### 安装准备

#### Centos7

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

#### Ubuntu

```bash
sudo apt-get install -y \
     git \
     wget \
     python3-pip \
     python \
     openjdk-8-jdk \
     maven 

export JAVA_HOME=/usr/lib/jvm/default-java/
```

```bash
git clone https://github.com/vesoft-inc/nebula-bench.git 
cd nebula-bench
pip3 install --user -r requirements.txt
python3 run.py --help
```

准备 NebulaGraph 的工具。

安装 golang，然后编译相关工具。

* [nebula-importer](https://github.com/vesoft-inc/nebula-importer)
* [xk6-nebula](https://github.com/vesoft-inc/k6-plugin)

```bash
/bin/bash scripts/setup.sh
```

如果 go get 的包下载不下来，需要设置 golang 代理。

```bash
export GOPROXY=https://goproxy.cn
```

编译后，二进制包在 `scripts` 文件夹中。

### 生成 LDBC 数据

```bash
python3 run.py data 
```

会自动下载 Hadoop，然后使用 [ldbc_snb_datagen](https://github.com/ldbc/ldbc_snb_datagen_spark) 生成数据。
为了方便 importer 导入，将生成后的文件拆分了一个带头的 header 文件，再去掉原有文件第一行。
默认生成的文件在 `${PWD}/target/data/test_data/`。

更多命令

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

### 导入数据到 NebulaGraph

```bash
python3 run.py nebula importer
```

会根据 header 文件，自动生成 importer 的配置文件，然后运行 importer 导入。

```bash
# after prepare the data, you could import the data to any NebulaGraph as you want.
# space is mytest, graph address is 127.0.0.1:9669
python3 run.py nebula importer -s mytest -a 127.0.0.1:9669

# or using dotenv
cp env .env
# vi .env
python3 run.py nebula importer

# dry run, just create the import config file, and you can modify any configuration。
# by default, PARTITION_NUM is 24, REPLICA_FACTOR is 3.
python3 run.py nebula importer --dry-run
```

### nebula benchmark

使用带有 [xk6-nebula](https://github.com/HarrisChu/xk6-nebula) 插件的 [K6](https://github.com/k6io/k6) 来进行压测。

自动化的场景，在 `nebula_bench/scenarios/` 中。

```bash
# show help
python3 run.py stress run --help

# run all scenarios with 100 virtual users, every scenario lasts 60 seconds.
python3 run.py stress run 

# run all scenarios with 10 virtual users, every scenario lasts 3 seconds.
python3 run.py stress run --args='-u 10 -d 3s'

# list all stress test scenarios
python3 run.py stress scenarios

# run go.Go1StepEdge scenarios with 10 virtual users, every scenario lasts 3 seconds.
python3 run.py stress run -scenario go.Go1StepEdge --args='-u 10 -d 3s'

# run go.Go1StepEdge scenarios with special test stage.
# ramping up from 0 to 10 vus in first 10 seconds, then run 10 vus in 30 seconds, 
# then ramping up from 10 to 50 vus in 10 seconds.
python3 run.py stress run -scenario go.Go1StepEdge --args='-s 10s:10 -s 30s:10 -s 10s:50'

# use csv output
python3 run.py stress run -scenario go.Go1StepEdge --args='-s 10s:10 -s 30s:10 -s 10s:50 -o csv=test.csv'
```

更多 k6 参数，请参考。

```bash
scripts/k6 run --help
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

或者从标准输出看测试的结果。

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
     rowSize..............: min=0        avg=9.212424    med=3      max=243   p(90)=25     p(95)=40      p(99)=70
     vus..................: 100     min=0         max=100
     vus_max..............: 100     min=100       max=100
```

* `checks`，每次执行有一个检查点，默认是检查服务端返回的 `isSucceed`。
* `data_received` 和 `data_sent`，是 k6 工具自带的，对 NebulaGraph 用处不大。
* `iteration_duration`，每次执行的总时间。
* `latency`，服务端耗时，单位：微秒(us)。
* `responseTime`，客户端耗时, 单位：微秒(us)。
* `rowSize`，请求返回行数。
* `vus`，并发的用户数

大体来说

iteration_duration = responseTime + (客户端从 csv 读数据的耗时)

responseTime = latency + (网络传输的耗时) + (客户端解码的耗时)

因为一个查询有一个检查点，所以上面代表执行了 113778 个 query，所有都成功了。

latency 的单位是 `us`。

### 报告

```bash
# generate the `report.html` with summary json file in `output/20221109140449` folder.
python3 run.py report export -f output/20221109140449

# export to a new file.
python3 run.py report export -f output/20221109140449 -o new_report.html

# launch a http server with port 5050, and could browser all result in `output` folder.
python3 run.py report serve -p 5050
```

![report](doc/img/report.png)

## 更多

* 生成的数据文件，如果是 `aaa_xxYY_bbb` 格式，比如 `comment_hasTag_tag`，会认为是一个边类型，然后边的格式是 `XX_YY`。和 ldbc 保持一致 [ldbc_snb_interactive](https://github.com/ldbc/ldbc_snb_interactive/blob/main/cypher/queries/interactive-complex-1.cypher)
* 否则是一个 Tag 类型。
* 不同的 Tag，有可能 Vertex ID 是一样的，比如 Forum 和 Post。暂时没有特殊处理。


LDBC schema

```bash
CREATE TAG IF NOT EXISTS `Post`(`imageFile` string,`creationDate` datetime,`locationIP` string,`browserUsed` string,`language` string,`content` string,`length` int);
CREATE TAG IF NOT EXISTS `Tag`(`name` string,`url` string);
CREATE TAG IF NOT EXISTS `Tagclass`(`name` string,`url` string);
CREATE TAG IF NOT EXISTS `Organisation`(`type` string,`name` string,`url` string);
CREATE TAG IF NOT EXISTS `Place`(`name` string,`url` string,`type` string);
CREATE TAG IF NOT EXISTS `Person`(`firstName` string,`lastName` string,`gender` string,`birthday` string,`creationDate` datetime,`locationIP` string,`browserUsed` string);
CREATE TAG IF NOT EXISTS `Forum`(`title` string,`creationDate` datetime);
CREATE TAG IF NOT EXISTS `Comment`(`creationDate` datetime,`locationIP` string,`browserUsed` string,`content` string,`length` int);
CREATE EDGE IF NOT EXISTS `HAS_CREATOR`();
CREATE EDGE IF NOT EXISTS `REPLY_OF`();
CREATE EDGE IF NOT EXISTS `STUDY_AT`(`classYear` int);
CREATE EDGE IF NOT EXISTS `WORK_AT`(`workFrom` int);
CREATE EDGE IF NOT EXISTS `HAS_MODERATOR`();
CREATE EDGE IF NOT EXISTS `LIKES`(`creationDate` datetime);
CREATE EDGE IF NOT EXISTS `HAS_MEMBER`(`joinDate` datetime);
CREATE EDGE IF NOT EXISTS `IS_PART_OF`();
CREATE EDGE IF NOT EXISTS `CONTAINER_OF`();
CREATE EDGE IF NOT EXISTS `HAS_INTEREST`();
CREATE EDGE IF NOT EXISTS `IS_SUBCLASS_OF`();
CREATE EDGE IF NOT EXISTS `HAS_TAG`();
CREATE EDGE IF NOT EXISTS `IS_LOCATED_IN`();
CREATE EDGE IF NOT EXISTS `HAS_TYPE`();
CREATE EDGE IF NOT EXISTS `KNOWS`(`creationDate` datetime);
CREATE TAG INDEX IF NOT EXISTS `person_first_name_idx` on `Person`(firstName(10));
CREATE EDGE INDEX IF NOT EXISTS `like_creationDate_idx` on `LIKES`(creationDate);
```
