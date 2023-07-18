#! /usr/bin/pwsh

###############################################
# Get hostname from arguments  #
###############################################

$host_name = $args[0]


###############################################
# Copy files to the robot                     #
###############################################

Write-Host "Installing robot on ip $host_name";

cd ../..; # cd to docker/sic/

scp -r . nao@${host_name}:~/framework;

