#!/bin/bash

# Redis Connection Verifier Script (only for macOS or Linux for now)
# For Windows users, you can ask a friend with a Mac or Linux to run this script to test if your redis server allows inbound connections.

# This script verifies the connection to your Redis server. It can be run
# from either your local machine or a remote machine/robot to check the
# following:

# 1. **Connection Status**: Checks if the specified server IP address is reachable
# 2. **Local Reachability**: Tests if the Redis server is running and reachable from your local machine.
# 3. **Remote Reachability**: Tests if the Redis server is running and reachable from a remote machine/robot.
# Note: for testing 3. Remote Reachability, this file should be executed on the remote machine/robot to check connectivity

# Instructions:
# 1. If you want to test local reachability, you don't need to change REDIS_HOST.
# If you want to test remote reachability, change REDIS_HOST to the IP address of the Redis server.

# 2. Make the script executable by running:
#    chmod +x redis_connection_verifier.sh

# 3. Execute the script by running:
#    ./redis_connection_verifier.sh

REDIS_HOST="localhost" # Change this to where your Redis server is running
REDIS_PORT="6379"
REDIS_PASSWORD="changemeplease"  # <- DO NOT CHANGE THIS

# Set the timeout duration (in seconds)
TIMEOUT_DURATION=10

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected MacOS"
    if ! command -v gtimeout &> /dev/null; then
        echo "gtimeout not found, installing coreutils for MacOS"
	if ! brew install coreutils; then
            echo "Failed to install coreutils"
            exit 1
        else
	    echo -e "\nSuccesfully installed coreutils for MacOS, trying to connect to redis-server\n"
	fi
    fi
    TIMEOUT_CMD="gtimeout $TIMEOUT_DURATION"
elif [[ "$OSTYPE" == "linux"* ]]; then
    echo "Detected Linux"
    TIMEOUT_CMD="timeout $TIMEOUT_DURATION"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Check if the Redis host is even reachable
if ! ping -c 1 -W 2 $REDIS_HOST > /dev/null 2>&1; then
    echo "The IP address $REDIS_HOST is not reachable. Please check the address or your network connection."
    exit 1
fi

# Ping the redis server with password and a timeout
response=$($TIMEOUT_CMD redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping 2>/dev/null)

if [ $? -eq 124 ]; then
    echo "Connection to Redis server at $REDIS_HOST:$REDIS_PORT timed out after $TIMEOUT_DURATION seconds. Possible reasons: your firewall or vpn is on."
elif [ "$response" == "PONG" ]; then
    echo "Successfully connected to Redis server at $REDIS_HOST:$REDIS_PORT"
else
    echo "Failed to connect to Redis server at $REDIS_HOST:$REDIS_PORT. Are you sure the redis server is running?"
fi
