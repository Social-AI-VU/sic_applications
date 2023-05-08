#! /usr/bin/pwsh


###############################################
# Get hostname from arguments  #
###############################################

$host_name = $args[0]


###############################################
# Copy files to the robot                     #
###############################################

& .\copy_robot.ps1 ${host_name}

###############################################
# Install libraries                           #
###############################################

ssh nao@$host_name "
  cd ~/sic/lib/redis;                                   \
  pip install --user redis-3.5.3-py2.py3-none-any.whl;  \
  cd ../libtubojpeg/PyTurboJPEG-master;                 \
  pip install  --user . ;                               \
  cd ../../..;                                          \
  pip install --user -e .;                              \
"
