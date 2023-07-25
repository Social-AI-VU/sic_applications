$robot_type = $args[0]
$host_name = $args[1]

###############################################
# Get hostname and robot name from arguments  #
###############################################

if (-not $robot_type -or -not $host) {
    Write-Host "Missing robot type (nao or pepper) or robot ip address"
    Write-Host "Usage example: ./stop_robot.ps1 nao 192.168.0.123"
    exit 1
}

###############################################
# Start SIC!                                  #
###############################################

ssh nao@$host_name "
    pkill -f 'python2 ${robot_type}.py';
    "

Write-Host "Done!"