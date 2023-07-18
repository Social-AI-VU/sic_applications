param (
    [string]$robot_type = "",
    [string]$host = ""
)

###############################################
# Get hostname and robot name from arguments  #
###############################################

if (-not $host) {
    Write-Host "Missing robot ip address -h"
    exit 1
}

if (-not $robot_type) {
    Write-Host "Missing robot type -t (nao or pepper)"
    exit 1
}

###############################################
# Start SIC!                                  #
###############################################

ssh nao@$host "
    pkill -f 'python2 ${robot_type}.py';
    "

Write-Host "Done!"