import getopt
import os
import re
import sys
import threading
import pandas as pd

_csv_dir = "../target/data/test_data/social_network/"
_thread_count = 10
_all_csv_files = []
lock = threading.Lock()


def handler_data_once():
    lock.acquire()
    file = _all_csv_files.pop()
    lock.release()
    print('%s handler %s.' % (threading.current_thread().name, file))
    if(os.path.isfile(_csv_dir+file[:-4]+'_header.csv')):
        pd_header_csv = pd.read_csv(_csv_dir+file[:-4]+'_header.csv', sep='|')
        df_header = pd.DataFrame(pd_header_csv)
        if os.path.exists(_csv_dir+file+'.copy'):
            os.remove(_csv_dir+file+'.copy')
        pd_csv = pd.read_csv(_csv_dir+file, sep='|',
                             header=None, chunksize=100000)
        # handler header csv
        name_map = {}
        date_list = []
        for i in range(len(df_header.columns)):
            if df_header.columns[i].endswith('.id'):
                name_map[i] = df_header.columns[i][:-3].lower()
            elif df_header.columns[i].endswith('.id.1'):
                name_map[i] = df_header.columns[i][:-5].lower()
            elif df_header.columns[i] == 'id':
                name_map[i] = os.path.splitext(file)[0].split('/')[-1]
            elif df_header.columns[i].endswith('Date'):
                date_list.append(i)

        for key in name_map:
            df_header[df_header.columns[key]
                      ] = df_header[df_header.columns[key]].astype(str)
            df_header[df_header.columns[key]] = df_header[df_header.columns[key]].apply(
                lambda x: name_map[key]+'-'+x)
        for key in date_list:
            df_header[df_header.columns[key]] = df_header[df_header.columns[key]].apply(
                lambda x: x[:-5])
        df_header.to_csv(_csv_dir+file[:-4] +
                         '_header.csv.copy', index=False, sep='|')
        # handler data csv in chunk
        for df in pd_csv:
            for key in name_map:
                df[key] = df[key].astype(str)
                df[key] = df[key].apply(lambda x: name_map[key]+'-'+x)
            for key in date_list:
                df[key] = df[key].apply(lambda x: x[:-5])
            df.to_csv(_csv_dir+file+'.copy', index=False,
                      sep='|', header=None, mode='a')


def handler_data():
    while len(_all_csv_files) > 0:
        lock.acquire()
        if len(_all_csv_files) <= 0:
            break
        lock.release()
        handler_data_once()


def back_handler():
    print('start back handler')
    target_need_fix_title = ['static/place_isPartOf_place_header.csv.copy',
                             'dynamic/person_knows_person_header.csv.copy',
                             'dynamic/comment_replyOf_comment_header.csv.copy',
                             'static/tagclass_isSubclassOf_tagclass_header.csv.copy']
    # remove duplicate columns .1
    for dir in target_need_fix_title:
        with open(_csv_dir+dir, "r+") as fr:
            with open(_csv_dir+dir+'1', "w") as fw:
                fw.writelines(re.sub('id\.1', 'id', fr.readline()))
                fw.writelines(fr.readlines())
                os.remove(_csv_dir+dir)
                os.rename(_csv_dir+dir+'1', _csv_dir+dir)
    # split place
    place_header_csv = pd.read_csv(
        _csv_dir+'static/place_header.csv.copy', sep='|')
    place_csv = pd.read_csv(_csv_dir+'static/place.csv.copy', sep='|',
                            header=None, names=place_header_csv.columns)
    df = pd.DataFrame(place_csv)
    grouped = df.groupby('type')
    for name, group in grouped:
        group[0:9].to_csv(_csv_dir+'static/'+name +
                          '_header.csv.copy', sep='|', index=False)
        group.to_csv(_csv_dir+'static/'+name+'.csv.copy', index=False,
                     sep='|', header=None, mode='a')
    os.remove(_csv_dir+'static/place.csv.copy')
    os.remove(_csv_dir+'static/place_header.csv.copy')


if __name__ == "__main__":
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "i:j:", [])
    except getopt.GetoptError:
        print('clean-data.py -i <inputpath> -j <parallel-count>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-i":
            _csv_dir = arg
        elif opt == "-j":
            _thread_count = int(arg)
    all_dir_list = os.listdir(_csv_dir)
    for dir in all_dir_list:
        if os.path.isdir(_csv_dir+'/'+dir):
            dir_list = os.listdir(_csv_dir+'/'+dir)
            for file in dir_list:
                if file.endswith('.csv') and not file.endswith('header.csv'):
                    _all_csv_files.append(dir+'/'+file)
    thread_group = []
    n = 0
    while n < _thread_count:
        n = n+1
        t = threading.Thread(target=handler_data,
                             name='handler-Thread-'+str(n))
        t.start()
        thread_group.append(t)
    for th in thread_group:
        th.join()
    back_handler()
    print('all task done! please run copy-data.py to recover csv file')
