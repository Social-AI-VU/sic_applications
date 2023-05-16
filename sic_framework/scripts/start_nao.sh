#!/bin/bash

###############################################
# Get hostname and robot name from arguments  #
###############################################

unset -v host

while getopts r: opt; do
        case $opt in
                r) host=$OPTARG ;;
                *)
                        echo 'Error in command line parsing' >&2
                        exit 1
        esac
done

shift "$(( OPTIND - 1 ))"

: ${host:?Missing robot ip adress -r}

# Redis should be running on this device
unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     redis_host=$(hostname -I | cut -d' ' -f1);;
    Darwin*)    redis_host=$(ipconfig getifaddr en0);;
esac

echo "Connecting to redis at ip $redis_host (should be the ip of your laptop/desktop)"

###############################################
# Start SIC!                                  #
###############################################

ssh nao@$host " \
    export PYTHONPATH=/opt/aldebaran/lib/python2.7/site-packages; \
    export LD_LIBRARY_PATH=/opt/aldebaran/lib/naoqi; \
    cd ~/framework/sic_framework/devices; \
    echo 'Starting robot (due to a bug output may or may not be produced until you start your program)';\
    python2 nao.py --redis_ip=${redis_host}; \
"

echo "Done!"
