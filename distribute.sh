#!/bin/bash

cplc_files="cplc/*"
data_files="data/*"
experiments_files="experiments/*"
tester_files="tester/applet/ tester/ext/ tester/reader/ tester/build.xml tester/README.md tester/requirements.txt"
poc_files="poc/applet/ poc/ext/ poc/attack/*.py poc/attack/params.json poc/collect/*.py poc/target/*.c poc/target/*.cpp poc/target/*.java poc/target/Makefile poc/build.xml poc/README.md poc/requirements.txt"
all_files="README.md"

zip -r cplc.zip $cplc_files
zip -r poc.zip $poc_files
zip -r tester.zip $tester_files
zip -r all.zip $all_files $cplc_files $poc_files $tester_files

tar -czvf cplc.tar.gz $cplc_files
tar -czvf poc.tar.gz $poc_files
tar -czvf tester.tar.gz $tester_files
tar -czvf all.tar.gz $all_files $cplc_files $poc_files $tester_files

#gpg -b -a cplc.zip
#gpg -b -a poc.zip
#gpg -b -a tester.zip
#gpg -b -a all.zip
#gpg -b -a cplc.tar.gz
#gpg -b -a poc.tar.gz
#gpg -b -a tester.tar.gz
#gpg -b -a all.tar.gz