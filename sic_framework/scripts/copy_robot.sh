#!/bin/bash

###############################################
# Get hostname from arguments  #
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


###############################################
# Copy files to the robot                     #
###############################################

echo "Copying to robot on ip $host";

cd ../..; # cd to framework/

rsync -avzP --exclude sic_framework/services --exclude venv --exclude .git . nao@$host:~/framework;

