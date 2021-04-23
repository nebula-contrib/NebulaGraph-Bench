
# 1、Download nebula-bench 
        https://github.com/vesoft-inc/nebula-bench.git
        Notes: This only supports nebula 2.0 version, if you want to test nebula 1.0 version, please download branch v1.0 of https://github.com/vesoft-inc/nebula-bench.git
   
# 2、 Mvn package  Download Jmeter and install python pkg
        cd  nebula-bench/ldbc/setup/
        sh setup.sh {jmeter_install_dir}  //for example: sh setup.sh /home/perf 
        Notes: Jmeter's url may be outdated, you can go https://jmeter.apache.org/download_jmeter.cgi to find jmeter.zip's url, and change it in setup.sh 
 
# 3、LDBC data prepare
##  A）Use ldbc_snb_datagen to generate dataset
        https://github.com/ldbc/ldbc_snb_datagen
   
##  B）Merge files： 
       After datagen，go to data path ldbc_snb_datagen/social_network/dynamic  and ldbc_snb_datagen/social_network/static 
       run ldbc/scripts/csv-merger.sh to merge distribute files 

##  C）Use nebula-imorter to import data to nebula:
###    Download and make build importer
         https://github.com/vesoft-inc/nebula-importer.git

###    Config ldbc configs:     
         vid int    : ldbc/import/ldbc_vid_int.yaml
         vid string : ldbc/import/ldbc_vid_string.yaml
         must config info：
         
         clientSettings:
           space: {ldbcspace}
           address: {ip1:port,ip2:port}
          
         commands:  
           CREATE SPACE IF NOT EXISTS {ldbcspace}(PARTITION_NUM = 24, REPLICA_FACTOR = 1, vid_type = fixed_string(20));
           USE {ldbcspace};
       
         files: 
           path:
             - path: {path}/ldbc_snb_datagen/social_network/dynamic/person.csv
             - path: {path}/ldbc_snb_datagen/social_network/static/place.csv
             - path: {path}/ldbc_snb_datagen/social_network/static/organisation.csv
             - path: {path}/ldbc_snb_datagen/social_network/dynamic/post.csv
             - path: {path}/ldbc_snb_datagen/social_network/dynamic/comment.csv
             - path: {path}/ldbc_snb_datagen/social_network/dynamic/forum.csv
             - path: {path}/ldbc_snb_datagen/social_network/static/tag.csv
             - path: {path}/ldbc_snb_datagen/social_network/static/tagclass.csv
             ...
           
###     Import ldbc data to ldbc:
        ./nebula-importer --config  ldbc_vid_int.yaml
 
#  4、Perf test
##     Config jmx file 
       path:
         nebula-bench/ldbc/jmx/go_step.jmx
       config jmx: 
         <stringProp name="ThreadGroup.duration">{duration}</stringProp>  // perftest duration time(unit:s)
        
         <stringProp name="Argument.name">hosts</stringProp>
         <stringProp name="Argument.value">{ip1:port,ip2:port,ip3:port}</stringProp>
         
         <stringProp name="Argument.name">maxconn</stringProp>
         <stringProp name="Argument.value">{max}</stringProp>  //  >= 1
        
         <stringProp name="Argument.name">user</stringProp>
         <stringProp name="Argument.value">{user}</stringProp>
              
         <stringProp name="Argument.name">pwd</stringProp>
         <stringProp name="Argument.value">{pwd}</stringProp>
               
         <stringProp name="Argument.name">space</stringProp>
         <stringProp name="Argument.value">{spacename}</stringProp>
         
         <stringProp name="Argument.name">nGQL</stringProp>
         <stringProp name="Argument.value">{GO 3 STEP FROM "replace" OVER knows}</stringProp>
    
##     Nebula perf test nGQL
       GO 1 STEP FROM replace OVER knows 
       GO 1 STEP FROM replace OVER knows YIELD knows.`time`, $$.person.first_name, $$.person.last_name, $$.person.birthday
       GO 2 STEP FROM replace OVER knows 
       GO 2 STEP FROM replace OVER knows YIELD knows.`time`, $$.person.first_name, $$.person.last_name, $$.person.birthday
       GO 3 STEP FROM replace OVER knows 
       GO 3 STEP FROM replace OVER knows YIELD knows.`time`, $$.person.first_name, $$.person.last_name, $$.person.birthday


##    Run Jmeter
        A: run perftest and store perf metrics in file
        sh run.sh -j {jmeterdir} -t {testdir}  //for example: sh run.sh -j /home/perf/apache-jmeter-5.4 -t /home/perf/test 

        B: run perftest and store perf metrics in file and store perf metrics in mysql
         //Notes: use ldbc/sql/perf_metric.sql to create db and table in mysql 
         sh run_3.sh -m {mysqconf} -v {nebula_version} -c {casename} -j {jmeterdir} -t {testdir} //sh run_3.sh -m  '{"ip":"127.0.0.1","port":3306,"user":"xxx","pwd":"xxx","db":"perftest"}' -v 2.0 -c case1 -j jmeter/apache-jmeter-5.4 -t test
       
   
       
