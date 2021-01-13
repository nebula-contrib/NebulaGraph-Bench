# 1、Download nebula-bench 
    
       https://github.com/vesoft-inc/nebula-bench.git
 
# 2、Download Jmeter
     cd nebula-bench &&  wget https://mirror.bit.edu.cn/apache//jmeter/binaries/apache-jmeter-5.4.zip  &&  unzip apache-jmeter-5.4.zip 
  
# 3、ldbc data prepare
##  A）use ldbc_snb_datagen to generate dataset
        https://github.com/ldbc/ldbc_snb_datagen
   
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
           
###     import ldbc data to ldbc:
        ./nebula-importer --config  ldbc_vid_int.yaml
 
#   4、perf test
##    mvn package
      cd util/ldbc_go_step/ && mvn package
      
      
##    put  jar and jmx file to Jmeter 
      ldbc_go_step-2-jar-with-dependencies.jar : put to  apache-jmeter-5.4/lib/ext
      nebula-bench/ldbc/jmx/go_step.jmx : put to apache-jmeter-5.4/
      config jmx: 
         <stringProp name="LoopController.loops">{loops}</stringProp> 
         <stringProp name="ThreadGroup.num_threads">{nums}</stringProp> 
        
         <stringProp name="Argument.name">hosts</stringProp>
         <stringProp name="Argument.value">{ip1:port,ip2:port,ip3:port}</stringProp>
         
         <stringProp name="Argument.name">maxconn</stringProp>
         <stringProp name="Argument.value">{max}</stringProp>
        
         <stringProp name="Argument.name">user</stringProp>
         <stringProp name="Argument.value">{user}</stringProp>
              
         <stringProp name="Argument.name">pwd</stringProp>
         <stringProp name="Argument.value">{pwd}</stringProp>
               
         <stringProp name="Argument.name">space</stringProp>
         <stringProp name="Argument.value">{spacename}</stringProp>
         
         <stringProp name="Argument.name">nGQL</stringProp>
         <stringProp name="Argument.value">{GO 3 STEP FROM "replace" OVER knows}</stringProp>
    
##     run Jmeter
       cd apache-jmeter-5.4 
       perf test:
        ./bin/jmeter.sh -n -t go_step.jmx  -l go_step.jtl -j go_step.log
       report
        ./bin/jmeter.sh -g go_step.jtl  -o go_step
       
      
       

       
   
       
