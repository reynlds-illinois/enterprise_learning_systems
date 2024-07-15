export TMPDIR='/var/lib/canvas-mgmt/tmp'
# set targets
today=$(date +%F)
logLocation="/var/lib/canvas-mgmt/logs/"
cd2LogLocation="/var/lib/canvas-mgmt/logs/cd2/"
logFile=$logLocation$today".log"
cd2LogFile=$cd2LogLocation$today"_drop_initdb.log"
cd2ErrorFile=$cd2LogLocation$today"_drop_initdb_error.log"
now=$today" "$(date +%T)
echo "$now | canvas-mgmt | cd2_drop_initdb.sh" >> $logFile
# set python virtual env
source /var/lib/canvas-mgmt/python39-venv/bin/activate
# grab table names
TABLE_NAMES=$(dap list --namespace canvas)
echo $TABLE_NAMES | tee -a $cd2LogFile
sleep 2
# loop through tables to drop and then init them one at a time
for TABLE in $TABLE_NAMES
do
    echo "=== Processing table: $TABLE" | tee -a $cd2LogFile
    now=$today" "$(date +%T)
    echo "    = $now" | tee -a $cd2LogFile
    echo "    = Starting dropdb:  $TABLE" | tee -a $cd2LogFile
    echo "    = Command used: dap --loglevel error --logfile $cd2LogFile dropdb --namespace canvas --table $TABLE" | tee -a $cd2LogFile
    dap --loglevel error --logfile "$cd2LogFile" dropdb --namespace canvas --table "$TABLE"
    sleep 2
    #read -n 1 -p "<ENTER> to continue..." "mainmenuinput"
    echo "    = Starting initdb:  $TABLE" | tee -a $cd2LogFile
    echo "    = Command used: dap --loglevel error --logfile $cd2LogFile initdb --namespace canvas --table $TABLE" | tee -a $cd2LogFile
    dap --loglevel error --logfile "$cd2LogFile" initdb --namespace canvas --table "$TABLE"
    sleep 2
    #read -n 1 -p "    = <ENTER> to continue..." "mainmenuinput"
    echo "==================================================" | tee -a $cd2LogFile
done
# disable python virtual env
deactivate
# look for errors and notify
grep 'ERROR\|Error' $cd2LogFile >> $cd2ErrorFile
if [ -s "$cd2ErrorFile" ]; then
    subjectLine=$today"_CD2_DROP_INITDB_ERRORS"
    cat $cd2ErrorFile | mail -s $subjectLine MyUser@MyDomain.edu
else
    subjectLine=$today"_CD2_DROP_INITDB_PASS"
    echo $subjectLine | mail -s $subjectLine MyUser@MyDomain.edu
fi
