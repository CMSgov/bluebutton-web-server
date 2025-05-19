#!/bin/sh
docker compose pull
docker compose build
docker compose run inferno bundle exec inferno migrate
