# 1、Download nebula-bench 
   git clone git@github.com:vesoft-inc/nebula-bench.git
 
# 2、Download Jmeter
   cd nebula-bench &&  wget https://mirror.bit.edu.cn/apache//jmeter/binaries/apache-jmeter-5.4.zip  &&  unzip apache-jmeter-5.4.zip 
  
# 3、ldbc data prepare
##  A）use ldbc_snb_datagen to generate dataset
       details in  https://github.com/ldbc/ldbc_snb_datagen
   
##  B）merge files： 
       After datagen，go to data path ldbc_snb_datagen/social_network/dynamic  and ldbc_snb_datagen/social_network/static 
       run ldbc/scripts/csv-merger.sh to merge distribute files 

##  c）use nebula-imorter to import data to nebula:
###    download and make build importer
       git@github.com:vesoft-inc/nebula-importer.git
###    config ldbc configs:     
       vid int    : ldbc/import/ldbc_vid_int.yaml
       vid string : ldbc/import/ldbc_vid_string.yaml
       must config info：
       version: v2
description: ldbc
removeTempFiles: false
clientSettings:
  retry: 3
  concurrency: 30 # number of graph clients
  channelBufferSize: 1
  space: ldbc_snb_sf100_vid_string
  connection:
    user: root
    password: nebula
    address:
  postStart:
    commands: |
      CREATE SPACE IF NOT EXISTS ldbc_snb_sf100_vid_string(PARTITION_NUM = 24, REPLICA_FACTOR = 1, vid_type = fixed_string(20));
      USE ldbc_snb_sf100_vid_string;
      CREATE TAG IF NOT EXISTS person(first_name string, last_name string, gender string, birthday string, ip string, browser string);
      CREATE TAG IF NOT EXISTS place(name string, type string, url string);
      CREATE TAG IF NOT EXISTS organization(name string, type string, url string);
      CREATE TAG IF NOT EXISTS post(`time` string, image string, ip string, browser string, language string, content string, length int);
      CREATE TAG IF NOT EXISTS comment(`time` string, ip string, browser st
   
       
     
   
