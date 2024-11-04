#!/bin/bash

# Redis Close Script

# This script closes the Redis connection if running. Script should
# be run on the local machine. The script will do this as followed:

# 1. **Gracefully terminate** Initially, it will try to kill the process gracefully.
# 2. **Forcefully terminate** If it cannot gracefully terminate, it will kill the process forcefully. 

# Instructions:
# 1. Make the script executable by running:
#    chmod +x redis_close.sh

# 2. Execute the script by running:
#    ./redis_close.sh

PORT=6379

response=$(lsof -i tcp:$PORT | grep LISTEN | awk '{print $2, $9, $5}')

if ! command -v lsof &> /dev/null; then
    echo "lsof command not found."
    exit 1
elif [ -z "$response" ]; then
    echo "Redis not found with TCP port $PORT."
    exit 1
fi

echo "$response" | while read pid ip ipv; do
    kill -15 $pid
    if [ $? -eq 0 ]; then
        echo "Gracefully stopped redis with PID: $pid, IP-Address: $ip, IP-Version: $ipv (Port: $PORT)"
    else
        echo "Failed to gracefully stop redis with PID: $pid, IP-Address: $ip, IP-Version: $ipv (Port: $PORT). Attempting forced kill."
        kill -9 "$pid"
        if [ $? -eq 0 ]; then
            echo "Successfully forced termination of redis with PID: $pid, IP-Address: $ip, IP-Version: $ipv (Port: $PORT)"
        else
            echo "Failed to stop redis with PID: $pid, IP-Address: $ip, IP-Version: $ipv (Port: $PORT)"
        fi
    fi
done


