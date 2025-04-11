#!/bin/bash -l

# Set the TMPDIR location so you don't overwhelm the non-user space
export TMPDIR='/var/lib/canvas-mgmt/tmp'

# Check that arguments are provided and are correct...prompt and exit if not
if [[ $# -ne 2 ]]; then
    echo '' >&2
    echo '  >>> Too many/few arguments, expecting two:  ACTION and LOG_LEVEL' >&2
    echo '' >&2
    exit 1
fi
case $1 in
        dropdb|initdb|syncdb)
                ;;
        *)
                echo '' >&2
                echo '  >>> A valid ACTION is Required:  "dropdb", "initdb" or "syncdb"' >&2
                echo '' >&2
                exit 1
esac
case $2 in
        error|debug)
                ;;
        *)
                echo '' >&2
                echo '  >>> A valid LOG_LEVEL is Required:  "error" or "debug"' >&2
                echo '' >&2
                exit 1
esac

# Set arguments to variables
CD2_ACTION=$1
CD2_LOG_LEVEL=$2

# Configure other stuff (which may become arguments at some point)
today=$(date +%F)
now=$(date +%Y-%m-%d"_"%H:%M:%S)

# These paths are specific to the host
logLocation="/var/lib/canvas-mgmt/logs/"
cd2LogLocation="/var/lib/canvas-mgmt/logs/cd2/"
logFile=$logLocation$now".log"
cd2LogFile=$cd2LogLocation$now"_"$CD2_ACTION".log"

echo "$now | canvas-mgmt | cd2_$CD2_ACTION.sh" >> $logFile

# Enable the Python Virtual Environment
source /var/lib/canvas-mgmt/python312-venv/bin/activate

# Grab the current table names
mapfile -t TABLE_NAMES < <(dap list --namespace canvas)
echo "${TABLE_NAMES[@]}" | tee -a $cd2LogFile
sleep 2

# Now go do that voodoo that you do so well!!!
for TABLE in "${TABLE_NAMES[@]}"
do
    echo "=== Processing table: $TABLE" | tee -a $cd2LogFile
    now=$(date +%Y-%m-%d" "%T)
    echo "    = $now" | tee -a $cd2LogFile
    echo "    = Starting $CD2_ACTION:  $TABLE" | tee -a $cd2LogFile
    echo "    = Command used: dap --loglevel $CD2_LOG_LEVEL --logfile $cd2LogFile $CD2_ACTION --namespace canvas --table $TABLE" | tee -a $cd2LogFile
    dap --loglevel "$CD2_LOG_LEVEL" --logfile "$cd2LogFile" "$CD2_ACTION" --namespace canvas --table "$TABLE"
    sleep 2
    echo "==================================================" | tee -a $cd2LogFile
done

# Disable the Python Virtual Environment
deactivate

# Send results
if grep -q 'Error\|ERROR' "$cd2LogFile"; then
    grep 'Error\|ERROR' "$cd2LogFile" | mail -s "${today}_CD2_${CD2_ACTION}_ERRORS" reynlds@illinois.edu
else
    echo "${today}_CD2_${CD2_ACTION}_PASS" | mail -s "${today}_CD2_${CD2_ACTION}_PASS" reynlds@illinois.edu
fi
