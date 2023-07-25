#! /usr/bin/pwsh

###############################################
# Get hostname from arguments  #
###############################################

$host_name = $args[0]


###############################################
# Copy files to the robot                     #
###############################################

Write-Host "Installing robot on ip $host_name";

# Copy framework folder (without sic_framework as we cannot exclude sub dirs)
robocopy ../.. framework_tmp /xd venv /xd .git /xd sic_framework /s; 

# Copy sic_framework folder
robocopy .. framework_tmp\sic_framework /xd services /xd scripts /s; 

scp -r framework_tmp/. nao@10.15.2.168:framework/;

# detelete framework_tmp
Remove-Item -Path framework_tmp -Recurse -Force;
