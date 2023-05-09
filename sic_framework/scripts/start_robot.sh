#!/bin/bash

###############################################
# Get hostname and robot name from arguments  #
###############################################

unset -v host
unset -v name
unset -v redis_host

while getopts h:n:b: opt; do
        case $opt in
                h) host=$OPTARG ;;
                n) name=$OPTARG ;;
                b) redis_host=$OPTARG ;;
                *)
                        echo 'Error in command line parsing' >&2
                        exit 1
        esac
done

shift "$(( OPTIND - 1 ))"

: ${host:?Missing robot ip adress -h}
: ${name:?Missing robot name -n}
: ${redis_host:?Missing redis db ip -b}
# TODO redis_host=$(hostname -I) as it is always localhost

###############################################
# Start SIC!                                  #
###############################################

ssh nao@$host " \
    export DB_IP=${redis_host}; \
    export DB_PASS=changemeplease; \
    export PYTHONPATH=/opt/aldebaran/lib/python2.7/site-packages; \
    export LD_LIBRARY_PATH=/opt/aldebaran/lib/naoqi; \
    cd ~/sic/sic_framework/devices; \
    echo 'Starting robot (due to a bug output may or may not be produced until you connect a SICApplication)';\
    python2 nao.py --robot_name ${name}; \
"

echo "Done!"
