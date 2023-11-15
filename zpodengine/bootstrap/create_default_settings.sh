#!/bin/sh

#
# Set some prefect default settings
#

# Create zPod Engine Docker Based Work Pool
prefect work-pool create -t docker zpodengine-pool

# Set zpodengine-pool concurrency limit to 8
prefect work-pool set-concurrency-limit zpodengine-pool 8

# Create Atomic Operation tag for disabling concurrency
prefect concurrency-limit create atomic_operation 1
