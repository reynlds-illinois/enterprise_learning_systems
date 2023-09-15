###################################
# cron entry:  /var/lib/canvas-mgmt/bin/cd2_syncdb_cron.sh >> "/var/lib/canvas-mgmt/logs/cd2/`date +\%F`.log" 2>&1
###################################
#!/bin/bash
today=$(date +%F)
now=$today" "$(date +%T)
source /var/lib/canvas-mgmt/python39-venv/bin/activate
TABLE_NAMES=$(dap --base-url "https://api-gateway.instructure.com/" --client-id "MY_DAP_CLIENT_ID" --client-secret "MY_DAP_CLIENT_SECRET" list)
#echo $TABLE_NAMES
#echo "Starting table sync..."
for TABLE in $TABLE_NAMES
do
        #date
        #echo "Starting sync:  $TABLE"
        dap --base-url "https://api-gateway.instructure.com/" --client-id "MY_DAP_CLIENT_ID" --client-secret "MY_DAP_CLIENT_SECRET" syncdb --table "$TABLE" --connection-string "postgresql://PG_USER:PG_PASS@PG_FQDN:5432/PG_DB"
        #echo "Sync complete:  $TABLE"
        #date
done
deactivate
