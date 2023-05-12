#!/bin/bash

###############################################
# Get hostname and robot name from arguments  #
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
# Start SIC!                                  #
###############################################

ssh nao@$host << EOF
  pkill -f "python2 nao.py --robot_name"
EOF

echo "Done!"