#!/bin/bash

# Script to automatically kill old SIC processes on a Nao/Pepper robot
# Usage: ./kill_old_sic.sh <robot_ip> [username] [password]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if IP address is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Robot IP address is required${NC}"
    echo "Usage: $0 <robot_ip> [username] [password]"
    echo "Example: $0 192.168.1.100"
    echo "Example: $0 192.168.1.100 nao pepper"
    exit 1
fi

ROBOT_IP="$1"
USERNAME="${2:-nao}"  # Default to 'nao' if not provided
PASSWORD="${3:-nao}"  # Default to 'nao' if not provided

echo -e "${YELLOW}Connecting to robot at ${ROBOT_IP}...${NC}"

# Check if sshpass is available for password authentication
USE_SSHPASS=false
if command -v sshpass &> /dev/null; then
    USE_SSHPASS=true
else
    echo -e "${YELLOW}Note: sshpass not found. You will be prompted for password once.${NC}"
    echo -e "${YELLOW}Install sshpass for fully automatic password handling: brew install sshpass (macOS) or apt-get install sshpass (Linux)${NC}"
fi

# SSH options: disable strict host key checking and auto-accept fingerprints
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10"

# Execute all commands in a single SSH session to avoid multiple password prompts
# This uses a here-document to send all commands at once
echo -e "${YELLOW}Searching for running SIC processes...${NC}"

if [ "$USE_SSHPASS" = true ]; then
    OUTPUT=$(sshpass -p "${PASSWORD}" ssh ${SSH_OPTS} "${USERNAME}@${ROBOT_IP}" bash << 'REMOTE_SCRIPT'
        set +e  # Don't exit on error, we'll handle it
        
        # Find running SIC processes
        PIDS=$(ps aux | grep python | grep sic_framework | grep -v grep | awk '{print $2}' 2>/dev/null || true)
        
        if [ -z "$PIDS" ]; then
            echo "NO_PROCESSES"
            exit 0
        fi
        
        # Display found processes
        echo "FOUND_PROCESSES"
        ps aux | grep python | grep sic_framework | grep -v grep
        
        # Extract PIDs (handle multiple PIDs on multiple lines)
        PID_LIST=$(echo "$PIDS" | tr '\n' ' ' | xargs)
        
        if [ -z "$PID_LIST" ]; then
            echo "NO_PIDS"
            exit 0
        fi
        
        echo "KILLING:${PID_LIST}"
        
        # Kill the processes
        kill -9 ${PID_LIST} 2>/dev/null
        
        # Wait a moment for processes to terminate
        sleep 1
        
        # Verify processes are gone
        REMAINING_PIDS=$(ps aux | grep python | grep sic_framework | grep -v grep | awk '{print $2}' 2>/dev/null || true)
        
        if [ -z "$REMAINING_PIDS" ]; then
            echo "SUCCESS"
            exit 0
        else
            echo "REMAINING"
            ps aux | grep python | grep sic_framework | grep -v grep
            exit 1
        fi
REMOTE_SCRIPT
    )
    EXIT_CODE=$?
else
    # Without sshpass, use regular SSH (will prompt for password once)
    OUTPUT=$(ssh ${SSH_OPTS} "${USERNAME}@${ROBOT_IP}" bash << 'REMOTE_SCRIPT'
        set +e  # Don't exit on error, we'll handle it
        
        # Find running SIC processes
        PIDS=$(ps aux | grep python | grep sic_framework | grep -v grep | awk '{print $2}' 2>/dev/null || true)
        
        if [ -z "$PIDS" ]; then
            echo "NO_PROCESSES"
            exit 0
        fi
        
        # Display found processes
        echo "FOUND_PROCESSES"
        ps aux | grep python | grep sic_framework | grep -v grep
        
        # Extract PIDs (handle multiple PIDs on multiple lines)
        PID_LIST=$(echo "$PIDS" | tr '\n' ' ' | xargs)
        
        if [ -z "$PID_LIST" ]; then
            echo "NO_PIDS"
            exit 0
        fi
        
        echo "KILLING:${PID_LIST}"
        
        # Kill the processes
        kill -9 ${PID_LIST} 2>/dev/null
        
        # Wait a moment for processes to terminate
        sleep 1
        
        # Verify processes are gone
        REMAINING_PIDS=$(ps aux | grep python | grep sic_framework | grep -v grep | awk '{print $2}' 2>/dev/null || true)
        
        if [ -z "$REMAINING_PIDS" ]; then
            echo "SUCCESS"
            exit 0
        else
            echo "REMAINING"
            ps aux | grep python | grep sic_framework | grep -v grep
            exit 1
        fi
REMOTE_SCRIPT
    )
    EXIT_CODE=$?
fi

# Parse the output and provide colored feedback
if echo "$OUTPUT" | grep -q "NO_PROCESSES"; then
    echo -e "${GREEN}No SIC processes found running.${NC}"
    exit 0
elif echo "$OUTPUT" | grep -q "FOUND_PROCESSES"; then
    echo -e "${YELLOW}Found SIC processes:${NC}"
    echo "$OUTPUT" | sed -n '/FOUND_PROCESSES/,/KILLING:/p' | sed '1d;$d'
    
    if echo "$OUTPUT" | grep -q "KILLING:"; then
        PIDS_TO_KILL=$(echo "$OUTPUT" | grep "KILLING:" | sed 's/KILLING://')
        echo -e "${YELLOW}Killing SIC processes (PIDs: ${PIDS_TO_KILL})...${NC}"
    fi
    
    if echo "$OUTPUT" | grep -q "SUCCESS"; then
        echo -e "${GREEN}✓ All SIC processes have been successfully terminated.${NC}"
        exit 0
    elif echo "$OUTPUT" | grep -q "REMAINING"; then
        echo -e "${RED}Warning: Some processes may still be running:${NC}"
        echo "$OUTPUT" | sed -n '/REMAINING/,$p' | sed '1d'
        exit 1
    fi
fi

# Fallback: if we got here, check exit code
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Operation completed successfully.${NC}"
    exit 0
else
    echo -e "${RED}Error: Operation failed.${NC}"
    echo "$OUTPUT"
    exit 1
fi
