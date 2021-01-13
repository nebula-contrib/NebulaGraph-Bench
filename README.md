#1、Download nebula-bench 
   git clone git@github.com:vesoft-inc/nebula-bench.git
 
#2、Download Jmeter
   cd nebula-bench &&  wget https://mirror.bit.edu.cn/apache//jmeter/binaries/apache-jmeter-5.4.zip 
   unzip apache-jmeter-5.4.zip 
  
#3、ldbc data prepare
   ##A）use ldbc_snb_datagen to generate dataset,details in  https://github.com/ldbc/ldbc_snb_datagen
   
   ##B）merge files： 
   After datagen，go to data path ldbc_snb_datagen/social_network/dynamic  and ldbc_snb_datagen/social_network/static 
   run ldbc/scripts/csv-merger.sh to merge distribute files 
   
   ##c）use nebula-imorter to import data to nebula:
      import tool:   git@github.com:vesoft-inc/nebula-importer.git
      git clone and make build
      ldbc config files in  ldbc/import:
      vid int    : ldbc_vid_int.yaml
      vid string :   ldbc_vid_string.yaml
      must config info：
      
     
   
