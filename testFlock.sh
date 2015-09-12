#!/bin/bash
# test file locking by running multiple jobs simultaniously

#set "/home/demo/data_builder_cron/run_concurrent.py"
set "/home/demo/data_builder_cron/run_sequential.py"
for i in . . . . ; do (python "$1" &); done

