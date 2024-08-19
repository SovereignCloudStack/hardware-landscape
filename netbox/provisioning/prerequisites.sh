#!/bin/bash

set -e

command_exists() {
  command -v "$1" &> /dev/null
}

if ! command_exists jq; then
  echo "Installing jq..."
  sudo curl -L "http://10.10.23.254:18080/jq" -o /usr/bin/jq
  sudo chmod +x /usr/bin/jq
else
  echo "jq is already installed"
fi

if ! command_exists yq; then
  echo "Installing yq..."
  sudo curl -L "http://10.10.23.254:18080/yq" -o /usr/bin/yq
  sudo chmod +x /usr/bin/yq
else
  echo "yq is already installed"
fi

echo "All prerequisites are met"
