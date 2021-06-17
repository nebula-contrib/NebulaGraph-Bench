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
                    gcc \
                    wget \
                    python3 \
                    python3-devel \
                    java-1.8.0-openjdk \
                    maven 

# install python dependencies
sudo pip3 install -r requirements.txt
```

```bash
git clone https://github.com/vesoft-inc/nebula-bench.git 
cd nebula-bench
pip3 install --user -r requirement.txt
python3 run.py --help
```

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

Be careful, the default `nebula-import` in scripts folder is built in Linux, if you want to
run the tool in Mac OS, please build the nebula-import by yourself.

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

Work in progress.

## and more

* The file with `aaa_xxYY_bbb` format, like `comment_hasTag_tag`, should be an edge, and the edge name shoud be `XX_YY`. Keep the same format with [ldbc_snb_interactive](https://github.com/ldbc/ldbc_snb_interactive/blob/main/cypher/queries/interactive-complex-1.cypher)
* Otherwise it should be a vertex tag.
* Different entity types might have same ID (e.g. Forum and Post).
