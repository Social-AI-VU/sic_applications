#! /usr/bin/pwsh

###############################################
# Get hostname and robot name from arguments  #
###############################################

$host_name = $args[0]
$redis_host = $args[1]

###############################################
# Start SIC!                                  #
###############################################

ssh nao@$host_name " \
    export DB_IP=${redis_host}; \
    export PYTHONPATH=/opt/aldebaran/lib/python2.7/site-packages; \
    export LD_LIBRARY_PATH=/opt/aldebaran/lib/naoqi; \
    cd ~/framework/sic_framework/devices; \
    echo 'Starting robot (due to a bug output may or may not be produced until you connect a SICApplication)';\
    python2 nao.py --redis_ip=${redis_host}; \
"

