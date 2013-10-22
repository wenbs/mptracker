#!/bin/bash

POSTGRES_KEY_URL='http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc'
POSTGRES_REPO='deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main'

export DEBIAN_FRONTEND=noninteractive

apt-get install -y curl python-software-properties
curl "$POSTGRES_KEY_URL" | sudo apt-key add -
add-apt-repository -y "$POSTGRES_REPO"
add-apt-repository -y ppa:fkrull/deadsnakes
apt-get update
apt-get upgrade -y
apt-get install -y postgresql-9.3 postgresql-contrib-9.3 \
                   build-essential python3.3 python3.3-dev

sudo -u postgres psql -c "CREATE USER mptracker WITH ENCRYPTED PASSWORD 'mptracker';"
sudo -u postgres psql -c "CREATE DATABASE mptracker"
sudo -u postgres psql mptracker -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'
