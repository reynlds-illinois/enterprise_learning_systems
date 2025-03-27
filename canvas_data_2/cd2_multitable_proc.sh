#!/bin/bash
#
# REQUIRE 3 ARGUMENTS AND PROMPT IF NOT PROVIDED
echo ""
if [[ $1 -eq 0 ]]
then
        read -p "Enter number of threads to use (2, 5 or 10): " threads
        echo ""
        case $threads in
                2|5|10)
                        ;;
                *)
                        echo '' >&2
                        echo '  >>> A valid THREAD count is required:  "2", "5" or "10"' >&2
                        echo ''
                        exit 1
        esac
else
        threads=$1
fi
# PROMPT FOR DAP ACTION IF NOT PROVIDED
if [[ -z "$2" ]]
then
        read -p "Enter the DAP action to use (syncdb, initdb, dropdb): " dapAction
        echo ""
        case $dapAction in
                dropdb|initdb|syncdb)
                        ;;
                *)
                        echo '' >&2
                        echo '  >>> A valid ACTION is Required:  "dropdb", "initdb" or "syncdb"' >&2
                        echo '' >&2
                        exit 1
        esac
else
        dapAction=$2
fi
# PROMPT FOR LOG LEVEL IF NOT PROVIDED
if [[ -z $3 ]]
then
        read -p "Enter the logging level to use (info, warning, error or debug): " logLevel
        echo ""
        case $logLevel in
                info|warning|error|debug)
                        ;;
                *)
                        echo '' >&2
                        echo '  >>> A valid LOG_LEVEL is Required:  "info", "warning", "error" or "debug"' >&2
                        echo '' >&2
                        exit 1
        esac
else
        logLevel=$3
fi
#
# SET TEMP LOCATION AND VARIABLES
echo "=========== SUMMARY ==========="
echo "| = Number of Threads: $threads"
echo "| = Action to process: $dapAction"
echo "| = Logging Level      $logLevel"
echo "==============================="
echo ""
read -p "Press <ENTER> to continue, CTRL-C to exit..."
#
# SET TEMP LOCATION AND VARS
echo $"=== "`date`
export TMPDIR='/var/lib/canvas-mgmt/tmp'
today=$(date +%F)
cd2LogLocation="/var/lib/canvas-mgmt/logs/cd2/"
now=$today" "$(date +%T)
#
# PROCESS BASED ON ARGUMENTS
if [ $threads -eq 2 ]; then
    source /var/lib/canvas-mgmt/python312-venv/bin/activate
    #
    # BRING IN DATABASE CONNECTION FROM VAULT
    DB_CONN="$(grep 'cd2.pg.db.dev' < /var/lib/canvas-mgmt/config/environment_dot.conf)"
    DB_CONN="$(cut -d'=' -f2 <<< $DB_CONN)"
    #
    # CREATE ARRAYS BASED ON TABLE NAMES
    unset TABLES && unset PART0 && unset PART1
    TABLES=$(dap list --namespace canvas)
    TABLES=($TABLES)
    #
    # EXPLODE AND LOOP
    for item in {0..49}; do PART0="${PART0}${TABLES[item]} "; done && PART0=($PART0)
    part0LogFile=$cd2LogLocation$today"_dev_multi_PART0_$1.log"
    CD2_PART0 () { for str in ${PART0[@]}; do echo "Applying $dapAction action on PART0: $str"; dap --loglevel "$logLevel" --logfile "$part0LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {50..99}; do PART1="${PART1}${TABLES[item]} "; done && PART1=($PART1)
    part1LogFile=$cd2LogLocation$today"_dev_multi_PART1_$1.log"
    CD2_PART1 () { for str in ${PART1[@]}; do echo "Applying $dapAction action on PART1: $str"; dap --loglevel "$logLevel" --logfile "$part1LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    # CONCURRENT PROCESSING OF PARTS
    CD2_PART0 $dapAction & CD2_PART1 $dapAction
    #
    # WAIT FOR EVERYTHING TO COMPLETE
    wait
elif [ $threads -eq 5 ]; then
    source /var/lib/canvas-mgmt/python312-venv/bin/activate
    #
    # BRING IN DATABASE CONNECTION FROM VAULT
    DB_CONN="$(grep 'cd2.pg.db.dev' < /var/lib/canvas-mgmt/config/environment_dot.conf)"
    DB_CONN="$(cut -d'=' -f2 <<< $DB_CONN)"
    #
    # CREATE ARRAYS BASED ON TABLE NAMES
    unset TABLES && unset PART0 && unset PART1 && unset PART2 && unset PART3 && unset PART4
    TABLES=$(dap list --namespace canvas)
    TABLES=($TABLES)
    #
    # EXPLODE AND LOOP
    for item in {0..19}; do PART0="${PART0}${TABLES[item]} "; done && PART0=($PART0)
    part0LogFile=$cd2LogLocation$today"_dev_multi_PART0_$1.log"
    CD2_PART0 () { for str in ${PART0[@]}; do echo "Applying $dapAction action on PART0: $str"; dap --loglevel "$logLevel" --logfile "$part0LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {20..39}; do PART1="${PART1}${TABLES[item]} "; done && PART1=($PART1)
    part1LogFile=$cd2LogLocation$today"_dev_multi_PART1_$1.log"
    CD2_PART1 () { for str in ${PART1[@]}; do echo "Applying $dapAction action on PART1: $str"; dap --loglevel "$logLevel" --logfile "$part1LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {40..59}; do PART2="${PART2}${TABLES[item]} "; done && PART2=($PART2)
    part2LogFile=$cd2LogLocation$today"_dev_multi_PART2_$1.log"
    CD2_PART2 () { for str in ${PART2[@]}; do echo "Applying $dapAction action on PART2: $str"; dap --loglevel "$logLevel" --logfile "$part2LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {60..79}; do PART3="${PART3}${TABLES[item]} "; done && PART3=($PART3)
    part3LogFile=$cd2LogLocation$today"_dev_multi_PART3_$1.log"
    CD2_PART3 () { for str in ${PART3[@]}; do echo "Applying $dapAction action on PART3: $str"; dap --loglevel "$logLevel" --logfile "$part3LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {80..99}; do PART4="${PART4}${TABLES[item]} "; done && PART4=($PART4)
    part4LogFile=$cd2LogLocation$today"_dev_multi_PART4_$1.log"
    CD2_PART4 () { for str in ${PART4[@]}; do echo "Applying $dapAction action on PART4: $str"; dap --loglevel "$logLevel" --logfile "$part4LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    # CONCURRENT PROCESSING OF PARTS
    CD2_PART0 $dapAction & CD2_PART1 $dapAction & CD2_PART2 $dapAction & CD2_PART3 $dapAction & CD2_PART4 $dapAction
    #
    # WAIT FOR EVERYTHING TO COMPLETE
    wait
else
    source /var/lib/canvas-mgmt/python312-venv/bin/activate
    #
    # BRING IN DATABASE CONNECTION FROM VAULT
    DB_CONN="$(grep 'cd2.pg.db.dev' < /var/lib/canvas-mgmt/config/environment_dot.conf)"
    DB_CONN="$(cut -d'=' -f2 <<< $DB_CONN)"
    #
    # CREATE ARRAYS BASED ON TABLE NAMES
    unset TABLES && unset PART0 && unset PART1 && unset PART2 && unset PART3 && unset PART4 && unset PART5 && unset PART6 && unset PART7 && unset PART8 && unset PART9
    TABLES=$(dap list --namespace canvas)
    TABLES=($TABLES)
    #
    # EXPLODE AND LOOP
    for item in {0..9}; do PART0="${PART0}${TABLES[item]} "; done && PART0=($PART0)
    part0LogFile=$cd2LogLocation$today"_dev_multi_PART0_$1.log"
    CD2_PART0 () { for str in ${PART0[@]}; do echo "Applying $dapAction action on PART0: $str"; dap --loglevel "$logLevel" --logfile "$part0LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {10..19}; do PART1="${PART1}${TABLES[item]} "; done && PART1=($PART1)
    part1LogFile=$cd2LogLocation$today"_dev_multi_PART1_$1.log"
    CD2_PART1 () { for str in ${PART1[@]}; do echo "Applying $dapAction action on PART1: $str"; dap --loglevel "$logLevel" --logfile "$part1LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {20..29}; do PART2="${PART2}${TABLES[item]} "; done && PART2=($PART2)
    part2LogFile=$cd2LogLocation$today"_dev_multi_PART2_$1.log"
    CD2_PART2 () { for str in ${PART2[@]}; do echo "Applying $dapAction action on PART2: $str"; dap --loglevel "$logLevel" --logfile "$part2LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {30..39}; do PART3="${PART3}${TABLES[item]} "; done && PART3=($PART3)
    part3LogFile=$cd2LogLocation$today"_dev_multi_PART3_$1.log"
    CD2_PART3 () { for str in ${PART3[@]}; do echo "Applying $dapAction action on PART3: $str"; dap --loglevel "$logLevel" --logfile "$part3LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {40..49}; do PART4="${PART4}${TABLES[item]} "; done && PART4=($PART4)
    part4LogFile=$cd2LogLocation$today"_dev_multi_PART4_$1.log"
    CD2_PART4 () { for str in ${PART4[@]}; do echo "Applying $dapAction action on PART4: $str"; dap --loglevel "$logLevel" --logfile "$part4LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {50..59}; do PART5="${PART5}${TABLES[item]} "; done && PART5=($PART5)
    part5LogFile=$cd2LogLocation$today"_dev_multi_PART5_$1.log"
    CD2_PART5 () { for str in ${PART5[@]}; do echo "Applying $dapAction action on PART5: $str"; dap --loglevel "$logLevel" --logfile "$part5LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {60..69}; do PART6="${PART6}${TABLES[item]} "; done && PART6=($PART6)
    part6LogFile=$cd2LogLocation$today"_dev_multi_PART6_$1.log"
    CD2_PART6 () { for str in ${PART6[@]}; do echo "Applying $dapAction action on PART6: $str"; dap --loglevel "$logLevel" --logfile "$part6LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {70..79}; do PART7="${PART7}${TABLES[item]} "; done && PART7=($PART7)
    part7LogFile=$cd2LogLocation$today"_dev_multi_PART7_$1.log"
    CD2_PART7 () { for str in ${PART7[@]}; do echo "Applying $dapAction action on PART7: $str"; dap --loglevel "$logLevel" --logfile "$part7LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {80..89}; do PART8="${PART8}${TABLES[item]} "; done && PART8=($PART8)
    part8LogFile=$cd2LogLocation$today"_dev_multi_PART8_$1.log"
    CD2_PART8 () { for str in ${PART8[@]}; do echo "Applying $dapAction action on PART8: $str"; dap --loglevel "$logLevel" --logfile "$part8LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    sleep 2; for item in {90..99}; do PART9="${PART9}${TABLES[item]} "; done && PART9=($PART9)
    part9LogFile=$cd2LogLocation$today"_dev_multi_PART9_$1.log"
    CD2_PART9 () { for str in ${PART9[@]}; do echo "Applying $dapAction action on PART9: $str"; dap --loglevel "$logLevel" --logfile "$part9LogFile" $1 --connection-string "$DB_CONN" --namespace canvas --table "$str"; done; }
    #
    # CONCURRENT PROCESSING OF PARTS
    CD2_PART0 $dapAction & CD2_PART1 $dapAction & CD2_PART2 $dapAction & CD2_PART3 $dapAction & CD2_PART4 $dapAction & CD2_PART5 $dapAction & CD2_PART6 $dapAction & CD2_PART7 $dapAction & CD2_PART8 $dapAction & CD2_PART9 $dapAction
    #
    # WAIT FOR EVERYTHING TO COMPLETE
    wait
fi
echo ""
echo $"=== "`date`
echo ""
