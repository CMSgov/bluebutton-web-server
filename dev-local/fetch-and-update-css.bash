#!/usr/bin/env bash

fetch_and_update_css () {
    if [ ! -d '../bluebutton-css' ]
    then
        pushd ..
            git clone https://github.com/CMSgov/bluebutton-css.git
        popd
    else
        pushd ../bluebutton-css;
            git fetch --all
            git pull --all
        popd
        
        echo '🆗 CSS already installed. Fetched/pulled.'
    fi
}
