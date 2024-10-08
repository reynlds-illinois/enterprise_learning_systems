#!/bin/bash
#
export TMPDIR='/var/lib/canvas-mgmt/tmp'
today=$(date +%F)
cd2LogLocation="/var/lib/canvas-mgmt/logs/cd2/"
now=$today" "$(date +%T)
#
source /var/lib/canvas-mgmt/python312-venv/bin/activate
TABLES='' && PART0='' && PART1='' && PART2='' && PART3='' && PART4='' && PART5='' && PART6='' && PART7='' && PART8='' && PART9=''
TABLES=$(dap list --namespace canvas)
TABLES=($TABLES)
#
for item in {0..9}; do PART0="${PART0}${TABLES[item]} "; done && PART0=($PART0)
for item in {10..19}; do PART1="${PART1}${TABLES[item]} "; done && PART1=($PART1)
for item in {20..29}; do PART2="${PART2}${TABLES[item]} "; done && PART2=($PART2)
for item in {30..39}; do PART3="${PART3}${TABLES[item]} "; done && PART3=($PART3)
for item in {40..49}; do PART4="${PART4}${TABLES[item]} "; done && PART4=($PART4)
for item in {50..59}; do PART5="${PART5}${TABLES[item]} "; done && PART5=($PART5)
for item in {60..69}; do PART6="${PART6}${TABLES[item]} "; done && PART6=($PART6)
for item in {70..79}; do PART7="${PART7}${TABLES[item]} "; done && PART7=($PART7)
for item in {80..89}; do PART8="${PART8}${TABLES[item]} "; done && PART8=($PART8)
for item in {90..99}; do PART9="${PART9}${TABLES[item]} "; done && PART9=($PART9)
#
CD2 () { for part in "$1"'[@]'; do
             now=$today" "$(date +%T)
             cd2LogFile=$cd2LogLocation$today"_"$1"_syncdb.log"
             #cd2LogFile=$cd2LogLocation$today"_"$1"_drop_initdb.log"
             cd2ErrorFile=$cd2LogLocation$today"_"$1"_syncdb_error.log"
             for item in "${!part}"; do
                 now=$today" "$(date +%T)
                 echo "$now - $part - $item" | tee -a cd2LogFile;
                 echo "    = Starting syncdb $part - $item" | tee -a cd2LogFile
                 dap --loglevel error syncdb --logfile "$cd2LogFile" --namespace canvas --table $item; done
                 #dap --loglevel error dropdb --namespace canvas --table "$item"
                 #sleep 2
                 #dap --loglevel error initdb --logfile "$cd2LogFile" --namespace canvas --table "$item"; done
             done;
         done
}
#
CD2 PART0 & CD2 PART1 & CD2 PART2 & CD2 PART3 & CD2 PART4 & CD2 PART5 & CD2 PART6 & CD2 PART7 & CD2 PART8 & CD2 PART9
