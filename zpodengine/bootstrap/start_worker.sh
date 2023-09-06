#!/bin/sh

echo "Waiting for zpodengine server to start"
curl --head -X GET --retry 10 --retry-connrefused --retry-delay 2 --silent --output /dev/null http://zpodengineserver:4200

echo "Set Default Settings"
/zpodcore/bootstrap/create_default_settings.sh

echo "Start Worker"
prefect worker start -p zpodengine-pool
