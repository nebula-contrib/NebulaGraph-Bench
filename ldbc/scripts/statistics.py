import sys
import pandas as pd
import numpy as np
import pymysql
import datetime
from optparse import OptionParser
import json

def insert_mertrics(sql,conf):
    conn = pymysql.connect(host=conf['ip'], port=conf['port'], user=conf['user'], passwd=conf['pwd'], db=conf['db'])
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    conn.close()

def df_throughput(df):
    df['finish'] = df['timeStamp'] +  df['elapsed']/1000

    start_time=df['timeStamp'].min()
    end_time=df['finish'].max()
    count=len(df)
    throughput=count/((end_time-start_time)/1000)
    print("throughput:",throughput)
    dic_throughput={}
    dic_throughput['start_time'] = datetime.datetime.fromtimestamp(int(start_time/1000)).strftime('%Y-%m-%d %H:%M:%S')
    dic_throughput['end_time'] = datetime.datetime.fromtimestamp(int(end_time/1000)).strftime('%Y-%m-%d %H:%M:%S')
    dic_throughput['throughput']=throughput
    return dic_throughput

def df_statistics(df,label,column_name):
    df_sort=df.sort_values(by=column_name,ascending=True).reset_index(drop = True)
    count=df_sort.agg({column_name:['count']})[column_name].values[0]
    fail_count=df[df['success']==False].count()['success']

    p90=int(len(df_sort)*0.90)
    p95=int(len(df_sort)*0.95)
    p99=int(len(df_sort)*0.99)
    if p90 >= count:
        p90=count-1
    if p90 >= count:
        p95=count-1
    if p90 >= count:
        p99=count-1
    if column_name == 'elapsed':
        p90_value=df_sort.loc[p90,[column_name]][column_name]/1000
        p95_value=df_sort.loc[p95,[column_name]][column_name]/1000
        p99_value=df_sort.loc[p99,[column_name]][column_name]/1000
        min_value=df_sort.agg({column_name:['min']})[column_name].values[0]/1000
        max_value=df_sort.agg({column_name:['max']})[column_name].values[0]/1000
        avg=df_sort.agg({column_name:['mean']})[column_name].values[0]/1000
        median=df_sort.agg({column_name:['median']})[column_name].values[0]/1000
    elif column_name == 'Latency':
        p90_value=df_sort.loc[p90,[column_name]][column_name]/1000
        p95_value=df_sort.loc[p95,[column_name]][column_name]/1000
        p99_value=df_sort.loc[p99,[column_name]][column_name]/1000
        min_value=df_sort.agg({column_name:['min']})[column_name].values[0]/1000
        max_value=df_sort.agg({column_name:['max']})[column_name].values[0]/1000
        avg=df_sort.agg({column_name:['mean']})[column_name].values[0]/1000
        median=df_sort.agg({column_name:['median']})[column_name].values[0]/1000

  #  sql='insert perf_statisticss(casename,label,nebula_version,starttime,endtime,count,fail_count,min,max,avg,median,p90,p95,p99,throughput) \
   #      values (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',{},{},{},{},{},{},{},{},{},{})\
    #     .format(casename,lable,nebula_version,);
    print("statistics:",column_name,"label:",label,'count:',count,'fail_count:',fail_count,'min:',min_value,'max_value:',max_value,'avg:',avg,'median',median,'p90:',p90_value,'p95:',p95_value,'p99:',p99_value)
    dic_statistics={}
    dic_statistics['column_name']=column_name
    dic_statistics['label']=label
    dic_statistics['count']=count
    dic_statistics['fail_count']=fail_count
    dic_statistics['min']=min_value
    dic_statistics['max']=max_value
    dic_statistics['avg']=avg
    dic_statistics['median']=median
    dic_statistics['p90']=p90_value
    dic_statistics['p95']=p95_value
    dic_statistics['p99']=p99_value
    return dic_statistics

if __name__ == '__main__':
    opt_parser = OptionParser()
    opt_parser.add_option('-f','--filename',
                          dest='filename',
                          default='',
                          help='case1.jtl')
    opt_parser.add_option('-c','--casename',
                          dest='casename',
                          default='',
                          help='2.1')
    opt_parser.add_option('-v','--vesion',
                          dest='nebula_version',
                          default='',
                          help='version')
    opt_parser.add_option('-m','--mysqlconf',
                          dest='mysqlconf',
                          default='',
                          help='{"ip":"127.0.0.1","port":3306,"user":"root","pwd":"xxx","db":"xxx"}')
    options, args = opt_parser.parse_args()

    if (options.filename==''):
        print("please input csv filename")
        sys.exit(1)

    if (options.mysqlconf != ''):
        try:
            print(options.mysqlconf)
            mysql_conf_json=json.loads(options.mysqlconf)
        except:
            print("mysqlconf is invalid, please check!")
            sys.exit(1)

        if (options.casename==''):
            print("please input casename")
            sys.exit(1)

        if (options.nebula_version==''):
            print("please input nebula_version")
            sys.exit(1)

    #read file
    try:
        df=pd.read_csv(options.filename,header=0,sep=',')
    except:
        print("read csv file failed")
        sys.exit(1)
    else:
        print("read csv to df success")


    if(len(df) == 0):
        print("there is no data to statistics")
        sys.exit(0)
        
    #delete somedata
    df.drop(df.head((int)(len(df)*0.1)).index,inplace=True)
    df.drop(df.tail((int)(len(df)*0.1)).index,inplace=True)

    #statistics client time
    try:
        dic_elapsed_statistics=df_statistics(df,'total','elapsed')
        for label,group in df.groupby(['label']):
            df_statistics(group, label,'elapsed')
    except:
        print("statistics elapsed failed , please check the data in file")
        sys.exit(1)
    else:
        print("statistics elapsed finished!")

    #statistics server time
    try:
        dic_latency_statistics=df_statistics(df,'total','Latency')
        for label,group in df.groupby(['label']):
            df_statistics(group, label,'Latency')
    except:
        print("statistics Latency failed , please check the data in file")
        sys.exit(1)
    else:
        print("statistics Latency finished!")

    try:
        dic_throughput=df_throughput(df)
    except:
        print("statistics throughput failed , please check the data in file")
        sys.exit(1)
    else:
        print("statistics throughput finished!")


    if (options.mysqlconf != ''):
        client_metrics_sql='insert perf_metrics(casename,label,nebula_version,starttime,endtime,count,fail_count,min,max,avg,median,p90,p95,p99,throughput) \
            values (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',{},{},{},{},{},{},{},{},{},{})'\
            .format(options.casename,"client_time",options.nebula_version,dic_throughput["start_time"],dic_throughput["end_time"],dic_elapsed_statistics["count"],dic_elapsed_statistics["fail_count"],\
            dic_elapsed_statistics["min"],dic_elapsed_statistics["max"],dic_elapsed_statistics["avg"],dic_elapsed_statistics["median"], \
            dic_elapsed_statistics["p90"],dic_elapsed_statistics["p95"],dic_elapsed_statistics["p99"],dic_throughput["throughput"])

        server_metrics_sql='insert perf_metrics(casename,label,nebula_version,starttime,endtime,count,fail_count,min,max,avg,median,p90,p95,p99,throughput) \
            values (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',{},{},{},{},{},{},{},{},{},{})'\
            .format(options.casename,"server_time",options.nebula_version,dic_throughput["start_time"],dic_throughput["end_time"],dic_latency_statistics["count"],dic_latency_statistics["fail_count"],\
            dic_latency_statistics["min"],dic_latency_statistics["max"],dic_latency_statistics["avg"],dic_latency_statistics["median"], \
            dic_latency_statistics["p90"],dic_latency_statistics["p95"],dic_latency_statistics["p99"],dic_throughput["throughput"])

        try:
            insert_mertrics(client_metrics_sql,mysql_conf_json)
        except:
            print("insert client metrics to mysql failed!")
            sys.exit(1)
        else:
            print("insert client metrics  to mysql finished!")

        try:
            insert_mertrics(server_metrics_sql,mysql_conf_json)
        except:
            print("insert server metrics to mysql failed!")
            sys.exit(1)
        else:
            print("insert server metrics to mysql finished!")
