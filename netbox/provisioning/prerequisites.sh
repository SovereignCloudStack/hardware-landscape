#!/bin/bash

set -e

command_exists() {
  command -v "$1" &> /dev/null
}

if ! command_exists jq; then
  echo "Installing jq..."
  sudo curl -L "http://10.10.23.254:28080/jq" -o /usr/bin/jq
  sudo chmod +x /usr/bin/jq
else
  echo "jq is already installed"
fi

echo "All prerequisites are met"
