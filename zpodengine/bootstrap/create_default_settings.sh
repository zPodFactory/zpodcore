#!/bin/sh

#
# Set some prefect default settings
#

# Create zPod Engine Docker Based Work Pool
prefect work-pool create -t docker zpodengine-pool

# Set a concurrency limit 'download' tag to 2
prefect concurrency-limit create download 2
