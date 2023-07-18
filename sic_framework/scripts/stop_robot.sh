#!/bin/bash

###############################################
# Get hostname and robot name from arguments  #
###############################################

unset -v host

while getopts t:h: opt; do
        case $opt in
                t) robot_type=$OPTARG ;;
                h) host=$OPTARG ;;
                *)
                        echo 'Error in command line parsing' >&2
                        exit 1
        esac
done

shift "$(( OPTIND - 1 ))"

: ${host:?Missing robot ip adress -h}
: ${robot_type:?Missing robot type -t (nao or pepper)}

###############################################
# Start SIC!                                  #
###############################################

ssh nao@$host << EOF
  pkill -f "python2 ${robot_type}.py"
EOF

echo "Done!"




