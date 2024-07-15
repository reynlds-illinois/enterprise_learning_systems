#!/bin/bash
# set LARGE temp location
export TMPDIR='/var/lib/canvas-mgmt/tmp'
# define targets
today=$(date +%F)
logLocation="/var/lib/canvas-mgmt/logs/"
cd2LogLocation="/var/lib/canvas-mgmt/logs/cd2/"
logFile=$logLocation$today".log"
cd2LogFile=$cd2LogLocation$today"_syncdb.log"
cd2ErrorFile=$cd2LogLocation$today"_syncdb_error.log"
#echo "LOG: $cd2LogFile"
now=$today" "$(date +%T)
echo "$now | canvas-mgmt | cd2_dbsync.sh" >> $logFile
# activate python virtual env
source /var/lib/canvas-mgmt/python39-venv/bin/activate
# grab table listing
TABLE_NAMES=$(dap list --namespace canvas)
echo $TABLE_NAMES | tee -a $cd2LogFile
sleep 2
# loop through tables to sync them one at a time
for TABLE in $TABLE_NAMES
do
    echo "=== Processing table: $TABLE" | tee -a $cd2LogFile
    now=$today" "$(date +%T)
    echo "    = $now" | tee -a $cd2LogFile
    echo "    = Starting syncdb:  $TABLE" | tee -a $cd2LogFile
    echo "    = Command used: dap --loglevel debug --logfile $cd2LogFile syncdb --namespace canvas --table $TABLE" | tee -a $cd2LogFile
    dap --loglevel debug --logfile "$cd2LogFile" syncdb --namespace canvas --table "$TABLE"
    sleep 2
    echo "==================================================" | tee -a $cd2LogFile
done
# disable python virtual env
deactivate
# look for any errors and notify
grep 'Error\|ERROR' $cd2LogFile >> $cd2ErrorFile
if [ -s "$cd2ErrorFile" ]; then
    subjectLine=$today"_CD2_SYNCDB_ERRORS"
    cat $cd2ErrorFile | mail -s $subjectLine MyUser@MyDomain.edu
else
    subjectLine=$today"_CD2_SYNCDB_PASS"
    echo $subjectLine | mail -s $subjectLine MyUser@MyDomain.edu
fi
