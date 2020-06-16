#!/bin/bash

cplc_files="cplc/*"
data_files="data/*"
experiments_files="experiments/*"
tester_files="tester/applet/ tester/ext/ tester/reader/ tester/build.xml tester/README.md tester/requirements.txt"
poc_files="poc/applet/ poc/ext/ poc/attack/*.py poc/attack/params.json poc/collect/*.py poc/target/*.c poc/target/*.cpp poc/target/*.java poc/target/Makefile poc/build.xml poc/README.md poc/requirements.txt"
all_files="README.md"

echo "[ ] Producing zips."
zip -r dist/data.zip $data_files
zip -r dist/cplc.zip $cplc_files
zip -r dist/poc.zip $poc_files
zip -r dist/tester.zip $tester_files
zip -r dist/all.zip $all_files $data_files $cplc_files $poc_files $tester_files
echo "[*] Zips done."

echo "[ ] Producing tars."
tar -czvf dist/data.tar.gz $data_files
tar -czvf dist/cplc.tar.gz $cplc_files
tar -czvf dist/poc.tar.gz $poc_files
tar -czvf dist/tester.tar.gz $tester_files
tar -czvf dist/all.tar.gz $all_files $data_files $cplc_files $poc_files $tester_files
echo "[*] Tars done."

if [ "$#" -eq 1 ] && [ "$1" = "sign" ]; then
  echo "[ ] Signing."
  gpg -b -a dist/data.zip
  gpg -b -a dist/cplc.zip
  gpg -b -a dist/poc.zip
  gpg -b -a dist/tester.zip
  gpg -b -a dist/all.zip
  gpg -b -a dist/data.tar.gz
  gpg -b -a dist/cplc.tar.gz
  gpg -b -a dist/poc.tar.gz
  gpg -b -a dist/tester.tar.gz
  gpg -b -a dist/all.tar.gz
fi
echo "[*] Done."