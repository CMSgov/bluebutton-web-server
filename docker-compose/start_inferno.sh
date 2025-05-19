#!/bin/bash

# start inferno by:
# using smart-app-launch-test-kit as example.
# git clone <inferno-kits>, e.g. https://github.com/inferno-framework/smart-app-launch-test-kit.git
# cd smart-app-launch-test-kit
# ./setup.sh
# ./run.sh

if [ ! -d 'smart-app-launch-test-kit' ]
then
    git clone https://github.com/inferno-framework/smart-app-launch-test-kit.git
else
    echo 'smart-app-launch-test-kit already checked out.'
fi

echo "Start Inferno: smart-app-launch-test-kit ..."
cd smart-app-launch-test-kit ; ./setup.sh ; ./run.sh
echo "After start Inferno: smart-app-launch-test-kit ..."
