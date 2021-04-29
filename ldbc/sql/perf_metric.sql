drop database if exists perftest;

create database perftest;

use perftest1;
create table perf_metrics(
casename       varchar(50),
label          varchar(50),
nebula_version varchar(10),
starttime      timestamp,
endtime        timestamp,
count          int,
fail_count     int,
min            double,
max            double,
avg            double,
median         double,
p90            double,
p95            double,
p99            double,
throughput     double
);
