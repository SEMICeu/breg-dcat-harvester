#!/usr/bin/env bash

# This script builds the dashboard React app and
# moves the output files to the directory from which
# they will be served by the Flask application

set -e
set -x

APP_GIT_PATH=${APP_GIT_PATH:-".."}
APP_SPA_PATH=${APP_SPA_PATH:-"./api/breg_harvester/spa"}

if test -d "${APP_GIT_PATH}/.git"; then
    git clean -f -X -d ${APP_SPA_PATH}
else
    rm -fr ${APP_SPA_PATH}/*
fi

cd ./app
npm install
npm run build
mv ./build/* ../api/breg_harvester/spa