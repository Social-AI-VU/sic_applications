#!/usr/bin/expect -f


set timeout 10

set hosts [list 192.168.0.237 192.168.0.236 192.168.0.209 192.168.0.238 192.168.0.121 192.168.0.135 192.168.0.191 192.168.0.106 192.168.0.183 192.168.0.226]
#set hosts [list 10.15.2.117 10.15.2.200]


foreach host $hosts {
  spawn ./stop_robot.sh -h "$host"
  sleep .2
 # Wait for the SSH command to prompt for a password
  expect {
      # If the SSH command asks for a password, send it
      "Password:" {
          send "nao\r"
          exp_continue
      }

      "password:" {
          send "nao\r"
          exp_continue
      }

      # If the SSH command prompts for a fingerprint verification, accept it
      "Are you sure you want to continue connecting (yes/no" {
          send "yes\r"
          exp_continue
      }

      # If the SSH command has already established a connection, exit the loop and close the SSH session
      "nao \[0\] ~ $" {
          break
      }
  }

}

