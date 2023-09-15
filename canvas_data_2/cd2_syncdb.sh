#!/bin/bash
today=$(date +%F)
cd2LogLocation="/var/lib/canvas-mgmt/logs/cd2/"
cd2LogFile="$cd2LogLocation$today.log"
echo "LOG: $cd2LogFile"
now=$today" "$(date +%T)
echo "$now | canvas-mgmt | cd2_dbsync.sh" >> $logFile
# SYNC PRIMARY TABLES
echo "======================== CD2 Canvas STARTING $now ========================" >> $cd2LogFile
# python virtual env activation to enable the Instructure DAP client
source /var/lib/canvas-mgmt/python39-venv/bin/activate
TABLE_NAMES=$(dap list --namespace canvas)
for TABLE in $TABLE_NAMES
do
    echo "Starting sync:  $TABLE"
    dap syncdb --namespace canvas --table "$TABLE"
    echo "Sync complete:  $TABLE"
done
now=$today" "$(date +%T)
echo "======================== CD2 Canvas COMPLETE $now ========================" >> $cd2LogFile
# SYNC WEB LOG TABLE
now=$today" "$(date +%T)
echo "======================== CD2 Web Logs STARTING $now ========================" >> $cd2LogFile
dap syncdb --namespace canvas_logs --table web_logs
now=$today" "$(date +%T)
echo "======================== CD2 Web Logs COMPLETE $now ========================" >> $cd2LogFile
# deactivate python virtual env
deactivate
