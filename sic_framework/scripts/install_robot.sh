#!/bin/bash


###############################################
# Get hostname from arguments  #
###############################################

unset -v host

while getopts h: opt; do
        case $opt in
                h) host=$OPTARG ;;
                *)
                        echo 'Error in command line parsing' >&2
                        exit 1
        esac
done

shift "$(( OPTIND - 1 ))"

: ${host:?Missing robot ip adress -h}


###############################################
# Copy files to the robot                     #
###############################################

./copy_robot.sh -h ${host}

###############################################
# Install libraries                           #
###############################################

ssh nao@$host << EOF
  cd ~/framework/lib/redis;
  pip install --user redis-3.5.3-py2.py3-none-any.whl;

  cd ../libtubojpeg/PyTurboJPEG-master;
  pip install  --user . ;

  cd ../../..;
  pip install --user -e .;

EOF
