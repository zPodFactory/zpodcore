#!/bin/sh

#
# Set some prefect default settings
# 

# Set a concurrency limit for the default-agent-pool to 4
prefect work-pool set-concurrency-limit default-agent-pool 4

# Set a concurrency limit "download" tag to 2
prefect concurrency-limit create download 2
