#! /usr/bin/pwsh

###############################################
# Get hostname and robot name from arguments  #
###############################################

$host_name = $args[0]
$name = $args[1]
$redis_host = $args[2]

###############################################
# Start SIC!                                  #
###############################################

ssh nao@$host_name " \
    export DB_IP=${redis_host}; \
    export DB_PASS=changemeplease; \
    export PYTHONPATH=/opt/aldebaran/lib/python2.7/site-packages; \
    export LD_LIBRARY_PATH=/opt/aldebaran/lib/naoqi; \
    cd ~/sic/sic_framework/devices; \
    echo 'Starting robot (due to a bug output may or may not be produced until you connect a SICApplication)';\
    python2 nao.py --robot_name ${name}; \
"

