import sys
import pandas as pd
import numpy as np

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
        p90_value=df_sort.loc[p90,[column_name]][column_name]
        p95_value=df_sort.loc[p95,[column_name]][column_name]
        p99_value=df_sort.loc[p99,[column_name]][column_name]
        min_value=df_sort.agg({column_name:['min']})[column_name].values[0]
        max_value=df_sort.agg({column_name:['max']})[column_name].values[0]
        avg=df_sort.agg({column_name:['mean']})[column_name].values[0]
        median=df_sort.agg({column_name:['median']})[column_name].values[0]
    elif column_name == 'Latency':
        p90_value=df_sort.loc[p90,[column_name]][column_name]/1000
        p95_value=df_sort.loc[p95,[column_name]][column_name]/1000
        p99_value=df_sort.loc[p99,[column_name]][column_name]/1000
        min_value=df_sort.agg({column_name:['min']})[column_name].values[0]/1000
        max_value=df_sort.agg({column_name:['max']})[column_name].values[0]/1000
        avg=df_sort.agg({column_name:['mean']})[column_name].values[0]/1000
        median=df_sort.agg({column_name:['median']})[column_name].values[0]/1000


    print("statistics:",column_name,"label:",label,'count:',count,'fail_count:',fail_count,'min:',min_value,'max_value:',max_value,'avg:',avg,'median',median,'p90:',p90_value,'p95:',p95_value,'p99:',p99_value)

if __name__ == '__main__':
    if(len(sys.argv)<2):
        print("please input csv filename")
        sys.exit(1)
    #read file
    try:
        filename=sys.argv[1]
        print(filename)
        df=pd.read_csv(filename,header=0,sep=',')
    except:
        print("read csv file failed")
        sys.exit(1)
    else:
        print("read csv to df success")


    if(len(df) == 0):
        print("there is no data to statistics")
        sys.exit(0)

    #statistics elapsed
    try:
        df_statistics(df,'total','elapsed')
        for label,group in df.groupby(['label']):
            df_statistics(group, label,'elapsed')
    except:
        print("statistics elapsed failed , please check the data in file")
        sys.exit(1)
    else:
        print("statistics elapsed finished!")

    #statistics latency
    try:
        df_statistics(df,'total','Latency')
        for label,group in df.groupby(['label']):
            df_statistics(group, label,'Latency')
    except:
        print("statistics Latency failed , please check the data in file")
        sys.exit(1)
    else:
        print("statistics Latency finished!")
