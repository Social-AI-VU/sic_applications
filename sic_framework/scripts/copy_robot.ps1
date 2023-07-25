#! /usr/bin/pwsh

###############################################
# Get hostname from arguments  #
###############################################

$host_name = $args[0]


###############################################
# Copy files to the robot                     #
###############################################

Write-Host "Installing robot on ip $host_name";

cd ../..; # cd to framework/

robocopy . framework_tmp /xd sic_framework\services /xd venv /xd .git;

scp -r framework_tmp nao@${host_name}:~/framework/;

# detelete framework_tmp
Remove-Item -Path framework_tmp -Recurse -Force;


