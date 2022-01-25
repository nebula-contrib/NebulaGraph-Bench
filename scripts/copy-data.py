import getopt
import os
import sys

_csv_dir = "../target/data/test_data/social_network/"
_all_csv_files = []

if __name__ == "__main__":
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "i:j:", [])
    except getopt.GetoptError:
        print('copy-data.py -i <inputpath>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-i":
            _csv_dir = arg
    all_dir_list = os.listdir(_csv_dir)
    for dir in all_dir_list:
        if os.path.isdir(_csv_dir+'/'+dir):
            dir_list = os.listdir(_csv_dir+'/'+dir)
            for file in dir_list:
                if file.endswith('.csv'):
                    _all_csv_files.append(dir+'/'+file)
    for dir in _all_csv_files:
        os.remove(_csv_dir+dir)
        os.rename(_csv_dir+dir+'.copy', _csv_dir+dir)
