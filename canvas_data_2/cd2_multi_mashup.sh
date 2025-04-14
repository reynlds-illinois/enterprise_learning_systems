#!/bin/bash
#
export TMPDIR='/var/lib/canvas-mgmt/tmp'

# Validate arguments
if [[ $# -ne 3 ]]; then
    echo '' >&2
    echo '  >>> Too many/few arguments, expecting three: THREADS, ACTION, and LOG_LEVEL' >&2
    echo '' >&2
    exit 1
fi

# Validate THREADS argument
if ! [[ $1 =~ ^[1-20]$|^10$ ]]; then
    echo '' >&2
    echo '  >>> A valid number of THREADS is required:  1 to 20' >&2
    echo '' >&2
    exit 1
fi
THREADS=$1

# Validate ACTION argument
if ! [[ $2 =~ ^(dropdb|initdb|syncdb)$ ]]; then
    echo '' >&2
    echo '  >>> A valid ACTION is required: "dropdb", "initdb", or "syncdb"' >&2
    echo '' >&2
    exit 1
fi
ACTION=$2

# Validate LOG_LEVEL argument
if ! [[ $3 =~ ^(info|warning|error|debug)$ ]]; then
    echo '' >&2
    echo '  >>> A valid LOG_LEVEL is required: "info", "warning", "error", or "debug"' >&2
    echo '' >&2
    exit 1
fi
LOG_LEVEL=$3

echo $"=== $(date)"

# Activate Python virtual environment and set up database connection
source /var/lib/canvas-mgmt/python312-venv/bin/activate
DEV_DB_CONN=$(grep "cd2.pg.db.dev" < /var/lib/canvas-mgmt/config/environment_dot.conf)
DEV_DB_CONN="$(cut -d'=' -f2 <<< $DEV_DB_CONN)"
today=$(date +%F)
cd2LogLocation="/var/lib/canvas-mgmt/logs/cd2/"
now=$today" "$(date +%T)

# Define the CD2 function
CD2() {
    local part_array_name="$1"  # Get the name of the array
    eval "local part_array=(\"\${${part_array_name}[@]}\")"  # Dereference the array
    for item in "${part_array[@]}"; do
        now=$(date +%F" "%T)
        cd2LogFile="${cd2LogLocation}${today}_${item}_syncdb.log"
        cd2ErrorFile="${cd2LogLocation}${today}_${item}_syncdb_error.log"
        echo "$now - Processing table: $item" | tee -a "$cd2LogFile"
        dap --loglevel "$LOG_LEVEL" "$ACTION" --connection-string "$DEV_DB_CONN" --namespace canvas --table "$item" >> "$cd2LogFile" 2>> "$cd2ErrorFile"
    done
}

# Fetch the list of tables
TABLES=$(dap list --namespace canvas)
TABLES=($TABLES)  # Convert to an array

# Calculate the number of tables and distribute them across threads
TOTAL_TABLES=${#TABLES[@]}
TABLES_PER_THREAD=$((TOTAL_TABLES / THREADS))
REMAINDER=$((TOTAL_TABLES % THREADS))

# Create thread-specific arrays
for ((i = 0; i < THREADS; i++)); do
    start_index=$((i * TABLES_PER_THREAD))
    end_index=$((start_index + TABLES_PER_THREAD - 1))
    if [[ $i -lt $REMAINDER ]]; then
        end_index=$((end_index + 1))  # Distribute remainder tables
    fi
    eval "THREAD_$i=(\"\${TABLES[@]:start_index:end_index-start_index+1}\")"
done

# Run threads in parallel
for ((i = 0; i < THREADS; i++)); do
    CD2 "THREAD_$i" &
done

wait  # Wait for all threads to complete

echo $"=== $(date)"
