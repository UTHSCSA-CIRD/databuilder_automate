#!/bin/bash
# test file locking by running multiple jobs simultaniously

#set "/home/demo/databuilder_automate/run_concurrent.py"
set "/home/demo/databuilder_automate/run_sequential.py"
for i in . . . . ; do (python "$1" &); done

